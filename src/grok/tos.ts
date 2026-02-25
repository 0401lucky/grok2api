import { encodeGrpcWebPayload, getGrpcStatusAndMessage } from "./grpcWeb";
import { fetchWithTimeout } from "../utils/fetch";

const TOS_API = "https://accounts.x.ai/auth_mgmt.AuthManagement/SetTosAcceptedVersion";

const DEFAULT_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
  "AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/120.0.0.0 Safari/537.36";

export interface GrpcWebResult {
  ok: boolean;
  http_status: number;
  grpc_status: number | null;
  grpc_message: string | null;
  error: string | null;
}

function buildCookie(token: string, cf: string): string {
  const t = String(token ?? "").trim();
  const cfCookie = String(cf ?? "").trim();
  return cfCookie ? `sso-rw=${t};sso=${t};${cfCookie}` : `sso-rw=${t};sso=${t}`;
}

export async function acceptTos(args: {
  token: string;
  cfCookie: string;
  userAgent?: string;
  timeoutMs?: number;
}): Promise<GrpcWebResult> {
  const token = String(args.token ?? "").trim();
  if (!token) {
    return { ok: false, http_status: 0, grpc_status: null, grpc_message: null, error: "missing sso" };
  }

  const ua = String(args.userAgent ?? DEFAULT_UA).trim() || DEFAULT_UA;
  const headers: Record<string, string> = {
    accept: "*/*",
    "content-type": "application/grpc-web+proto",
    origin: "https://accounts.x.ai",
    referer: "https://accounts.x.ai/accept-tos",
    "x-grpc-web": "1",
    "user-agent": ua,
    cookie: buildCookie(token, args.cfCookie),
  };

  const protoPayload = new Uint8Array([0x10, 0x01]);
  const body = encodeGrpcWebPayload(protoPayload);
  const timeoutMs = Math.max(1000, Math.min(30_000, Math.floor(Number(args.timeoutMs ?? 15_000))));

  try {
    const resp = await fetchWithTimeout(TOS_API, { method: "POST", headers, body }, timeoutMs);
    const bytes = new Uint8Array(await resp.arrayBuffer().catch(() => new ArrayBuffer(0)));
    const { grpc_status, grpc_message } = getGrpcStatusAndMessage(resp.headers, bytes);
    const ok = resp.status === 200 && (grpc_status === null || grpc_status === 0);
    const error =
      ok
        ? null
        : resp.status !== 200
          ? `HTTP ${resp.status}`
          : grpc_status !== null && grpc_status !== 0
            ? `gRPC ${grpc_status}${grpc_message ? `: ${grpc_message}` : ""}`
            : "unknown_error";
    return { ok, http_status: resp.status, grpc_status, grpc_message, error };
  } catch (e) {
    return {
      ok: false,
      http_status: 0,
      grpc_status: null,
      grpc_message: null,
      error: e instanceof Error ? e.message : String(e),
    };
  }
}

