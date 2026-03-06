const HASH_PREFIX = "pbkdf2_sha256";
const DEFAULT_ITERATIONS = 100000;
const MAX_NATIVE_ITERATIONS = 100000;
const SALT_BYTES = 16;
const DERIVED_BYTES = 32;

function base64UrlEncode(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  const b64 = btoa(binary);
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlDecode(input: string): Uint8Array {
  const normalized = input.replace(/-/g, "+").replace(/_/g, "/");
  const pad = normalized.length % 4 === 0 ? "" : "=".repeat(4 - (normalized.length % 4));
  const binary = atob(normalized + pad);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
  return out;
}

function toArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
}

async function importPbkdf2Key(secret: string): Promise<CryptoKey> {
  const encoded = new TextEncoder().encode(secret);
  return crypto.subtle.importKey("raw", toArrayBuffer(encoded), "PBKDF2", false, ["deriveBits"]);
}

async function importHmacKey(secret: string): Promise<CryptoKey> {
  const encoded = new TextEncoder().encode(secret);
  return crypto.subtle.importKey(
    "raw",
    toArrayBuffer(encoded),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
}

async function deriveNative(secret: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  const key = await importPbkdf2Key(secret);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt: toArrayBuffer(salt), iterations },
    key,
    DERIVED_BYTES * 8,
  );
  return new Uint8Array(bits);
}

async function hmacSha256(key: CryptoKey, data: Uint8Array): Promise<Uint8Array> {
  const signed = await crypto.subtle.sign("HMAC", key, toArrayBuffer(data));
  return new Uint8Array(signed);
}

async function deriveManual(secret: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  const key = await importHmacKey(secret);
  const block = new Uint8Array(salt.length + 4);
  block.set(salt, 0);
  block[block.length - 1] = 1;

  let u = await hmacSha256(key, block);
  const output = new Uint8Array(u);
  for (let i = 1; i < iterations; i += 1) {
    u = await hmacSha256(key, u);
    for (let j = 0; j < output.length; j += 1) {
      const current = output[j] ?? 0;
      const next = u[j] ?? 0;
      output[j] = current ^ next;
    }
  }
  return output;
}

async function derive(secret: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  if (iterations <= MAX_NATIVE_ITERATIONS) {
    return deriveNative(secret, salt, iterations);
  }
  return deriveManual(secret, salt, iterations);
}

function parsePasswordHash(hash: string): { iterations: number; saltText: string; digestText: string } | null {
  const [prefix, iterationText, saltText, digestText] = hash.split("$");
  if (prefix !== HASH_PREFIX || !iterationText || !saltText || !digestText) return null;
  const iterations = Number(iterationText);
  if (!Number.isFinite(iterations) || iterations <= 0) return null;
  return {
    iterations: Math.floor(iterations),
    saltText,
    digestText,
  };
}

export async function hashPassword(secret: string, iterations = DEFAULT_ITERATIONS): Promise<string> {
  const salt = new Uint8Array(SALT_BYTES);
  crypto.getRandomValues(salt);
  const digest = await derive(secret, salt, iterations);
  return `${HASH_PREFIX}$${iterations}$${base64UrlEncode(salt)}$${base64UrlEncode(digest)}`;
}

export function hasPasswordHash(storedHash: string | null | undefined): boolean {
  return String(storedHash ?? "").startsWith(`${HASH_PREFIX}$`);
}

export function passwordHashNeedsUpgrade(storedHash: string | null | undefined): boolean {
  const parsed = parsePasswordHash(String(storedHash ?? "").trim());
  return Boolean(parsed && parsed.iterations !== DEFAULT_ITERATIONS);
}

export async function verifyPassword(
  secret: string,
  storedHash: string | null | undefined,
  legacyPlaintext?: string | null,
): Promise<boolean> {
  const candidate = String(secret ?? "");
  const hash = String(storedHash ?? "").trim();
  if (hash) {
    const parsed = parsePasswordHash(hash);
    if (parsed) {
      const salt = base64UrlDecode(parsed.saltText);
      const expected = base64UrlEncode(await derive(candidate, salt, parsed.iterations));
      return expected === parsed.digestText;
    }
  }
  return candidate === String(legacyPlaintext ?? "");
}
