const HASH_PREFIX = "pbkdf2_sha256";
const DEFAULT_ITERATIONS = 310000;
const SALT_BYTES = 16;

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

async function derive(secret: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  const encoded = new TextEncoder().encode(secret);
  const raw = encoded.buffer.slice(encoded.byteOffset, encoded.byteOffset + encoded.byteLength) as ArrayBuffer;
  const saltBuffer = salt.buffer.slice(salt.byteOffset, salt.byteOffset + salt.byteLength) as ArrayBuffer;
  const key = await crypto.subtle.importKey("raw", raw, "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt: saltBuffer, iterations },
    key,
    256,
  );
  return new Uint8Array(bits);
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

export async function verifyPassword(
  secret: string,
  storedHash: string | null | undefined,
  legacyPlaintext?: string | null,
): Promise<boolean> {
  const candidate = String(secret ?? "");
  const hash = String(storedHash ?? "").trim();
  if (hash) {
    const [prefix, iterationText, saltText, digestText] = hash.split("$");
    if (prefix === HASH_PREFIX && iterationText && saltText && digestText) {
      const iterations = Number(iterationText);
      if (Number.isFinite(iterations) && iterations > 0) {
        const salt = base64UrlDecode(saltText);
        const expected = base64UrlEncode(await derive(candidate, salt, Math.floor(iterations)));
        return expected === digestText;
      }
    }
  }
  return candidate === String(legacyPlaintext ?? "");
}
