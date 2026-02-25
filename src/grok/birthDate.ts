import { fetchWithTimeout } from "../utils/fetch";

const BIRTH_API = "https://grok.com/rest/auth/set-birth-date";

const DEFAULT_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
  "AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/120.0.0.0 Safari/537.36";

export interface BirthDateResult {
  ok: boolean;
  http_status: number;
  error: string | null;
  response_text: string;
}

function buildCookie(token: string, cf: string): string {
  const t = String(token ?? "").trim();
  const cfCookie = String(cf ?? "").trim();
  return cfCookie ? `sso-rw=${t};sso=${t};${cfCookie}` : `sso-rw=${t};sso=${t}`;
}

function randomIntInclusive(min: number, max: number): number {
  const a = Math.floor(min);
  const b = Math.floor(max);
  if (a >= b) return a;
  return a + Math.floor(Math.random() * (b - a + 1));
}

function generateRandomBirthdate(): string {
  const now = new Date();
  const age = randomIntInclusive(20, 40);
  const year = now.getUTCFullYear() - age;
  const month = randomIntInclusive(1, 12);
  const day = randomIntInclusive(1, 28);
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}T16:00:00.000Z`;
}

export async function setBirthDate(args: {
  token: string;
  cfCookie: string;
  userAgent?: string;
  timeoutMs?: number;
}): Promise<BirthDateResult> {
  const token = String(args.token ?? "").trim();
  if (!token) {
    return { ok: false, http_status: 0, error: "missing sso", response_text: "" };
  }

  const ua = String(args.userAgent ?? DEFAULT_UA).trim() || DEFAULT_UA;
  const headers: Record<string, string> = {
    accept: "*/*",
    "content-type": "application/json",
    origin: "https://grok.com",
    referer: "https://grok.com/",
    "user-agent": ua,
    cookie: buildCookie(token, args.cfCookie),
  };

  const timeoutMs = Math.max(1000, Math.min(30_000, Math.floor(Number(args.timeoutMs ?? 15_000))));
  try {
    const resp = await fetchWithTimeout(
      BIRTH_API,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ birthDate: generateRandomBirthdate() }),
      },
      timeoutMs,
    );
    const text = await resp.text().catch(() => "");
    const ok = resp.status === 200;
    return { ok, http_status: resp.status, error: ok ? null : `HTTP ${resp.status}`, response_text: text.slice(0, 500) };
  } catch (e) {
    return {
      ok: false,
      http_status: 0,
      error: e instanceof Error ? e.message : String(e),
      response_text: "",
    };
  }
}

