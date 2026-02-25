import { encodeGrpcWebPayload, getGrpcStatusAndMessage } from "./grpcWeb";
import { fetchWithTimeout } from "../utils/fetch";

const NSFW_API = "https://grok.com/auth_mgmt.AuthManagement/UpdateUserFeatureControls";
const AGE_VERIFY_API = "https://grok.com/rest/auth/set-birth-date";
const NSFW_FEATURES_PATH = "features";
const NSFW_FEATURES_ENABLED_PATH = "features.enabled";

const DEFAULT_UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36";
const FALLBACK_UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36";

const NSFW_PROTO_PAYLOAD_LEGACY = new Uint8Array([0x08, 0x01, 0x10, 0x01]);

export interface NsfwResult {
  success: boolean;
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

function normalizeLower(text: unknown): string {
  return String(text ?? "").trim().toLowerCase();
}

function messageForHeuristics(r: NsfwResult): string {
  return String(r.grpc_message ?? r.error ?? "").trim();
}

function isAuthRelated(text: string): boolean {
  const t = normalizeLower(text);
  return ["unauthorized", "forbidden", "auth", "permission", "token"].some((k) => t.includes(k));
}

function isPayloadDecodeError(text: string): boolean {
  const t = normalizeLower(text);
  return (
    t.includes("failed to decode protobuf") ||
    t.includes("invalid wire type") ||
    t.includes("updateuserfeaturecontrolsrequest.features")
  );
}

function isFieldMaskMissing(text: string): boolean {
  return normalizeLower(text).includes("field mask must be provided");
}

function isInvalidFieldMaskPath(text: string): boolean {
  const t = normalizeLower(text);
  return (
    t.includes("invalid field mask") ||
    t.includes("fieldmask") ||
    t.includes("cannot find field") ||
    t.includes("unknown path")
  );
}

function isRejectedFeaturesField(text: string): boolean {
  const t = normalizeLower(text);
  return t.includes("invalid field: features") || t.includes("invalid field") || t.includes("field mask must be provided");
}

function shouldRetryWithAlternateMaskField(r: NsfwResult): boolean {
  if (r.success) return false;
  if (r.grpc_status !== 3) return false;
  return isFieldMaskMissing(messageForHeuristics(r));
}

function shouldRetryWithAlternateMaskPath(r: NsfwResult): boolean {
  if (r.success) return false;
  if (r.grpc_status !== 3) return false;
  return isInvalidFieldMaskPath(messageForHeuristics(r));
}

function shouldRetryWithLegacyPayload(r: NsfwResult): boolean {
  if (r.success) return false;
  if (r.grpc_status !== 13) return false;
  return isPayloadDecodeError(messageForHeuristics(r));
}

function shouldRetryWithAgeVerify(r: NsfwResult): boolean {
  if (r.success) return false;
  if (r.grpc_status !== 3) return false;
  return isRejectedFeaturesField(messageForHeuristics(r));
}

function shouldRetryWithFallbackUa(r: NsfwResult): boolean {
  if (r.success) return false;
  if (r.http_status === 401 || r.http_status === 403) return true;
  if (r.grpc_status === 7 || r.grpc_status === 16) return true;
  return isAuthRelated(messageForHeuristics(r));
}

function buildProtoPayload(maskFieldNumber: number, maskPath: string): Uint8Array {
  const out: number[] = [0x0a, 0x04, 0x08, 0x01, 0x10, 0x01];
  const pathBytes = new TextEncoder().encode(String(maskPath ?? ""));
  if (!pathBytes.length || pathBytes.length > 255) return new Uint8Array(out);
  const fieldMask: number[] = [0x0a, pathBytes.length, ...Array.from(pathBytes)];
  if (fieldMask.length > 255) return new Uint8Array(out);
  const tag = ((Math.floor(maskFieldNumber) & 0xff) << 3) | 0x02;
  out.push(tag & 0xff, fieldMask.length & 0xff, ...fieldMask);
  return new Uint8Array(out);
}

async function sendEnableRequest(args: {
  token: string;
  cfCookie: string;
  userAgent: string;
  timeoutMs: number;
  protoPayload: Uint8Array;
}): Promise<NsfwResult> {
  const headers: Record<string, string> = {
    accept: "*/*",
    "content-type": "application/grpc-web+proto",
    origin: "https://grok.com",
    referer: "https://grok.com/",
    "x-grpc-web": "1",
    "x-user-agent": "connect-es/2.1.1",
    "user-agent": args.userAgent,
    cookie: buildCookie(args.token, args.cfCookie),
  };

  try {
    const resp = await fetchWithTimeout(
      NSFW_API,
      { method: "POST", headers, body: encodeGrpcWebPayload(args.protoPayload) },
      args.timeoutMs,
    );
    const bytes = new Uint8Array(await resp.arrayBuffer().catch(() => new ArrayBuffer(0)));
    const { grpc_status, grpc_message } = getGrpcStatusAndMessage(resp.headers, bytes);
    const success = resp.status === 200 && (grpc_status === null || grpc_status === 0);
    const error =
      success
        ? null
        : resp.status !== 200
          ? `HTTP ${resp.status}`
          : grpc_status !== null && grpc_status !== 0
            ? `gRPC ${grpc_status}${grpc_message ? `: ${grpc_message}` : ""}`
            : "unknown_error";
    return { success, http_status: resp.status, grpc_status, grpc_message, error };
  } catch (e) {
    return {
      success: false,
      http_status: 0,
      grpc_status: null,
      grpc_message: null,
      error: e instanceof Error ? e.message : String(e),
    };
  }
}

async function verifyAgeViaRest(args: {
  token: string;
  cfCookie: string;
  userAgent: string;
  timeoutMs: number;
}): Promise<NsfwResult> {
  const headers: Record<string, string> = {
    accept: "*/*",
    "content-type": "application/json",
    origin: "https://grok.com",
    referer: "https://grok.com/",
    "user-agent": args.userAgent,
    cookie: buildCookie(args.token, args.cfCookie),
  };

  try {
    const resp = await fetchWithTimeout(
      AGE_VERIFY_API,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ birthDate: "2001-01-01T16:00:00.000Z" }),
      },
      args.timeoutMs,
    );
    const ok = resp.status === 200;
    return {
      success: ok,
      http_status: resp.status,
      grpc_status: null,
      grpc_message: null,
      error: ok ? null : `HTTP ${resp.status}`,
    };
  } catch (e) {
    return {
      success: false,
      http_status: 0,
      grpc_status: null,
      grpc_message: null,
      error: e instanceof Error ? e.message : String(e),
    };
  }
}

async function enableChain(args: {
  token: string;
  cfCookie: string;
  userAgent: string;
  timeoutMs: number;
}): Promise<NsfwResult> {
  let result = await sendEnableRequest({
    ...args,
    protoPayload: buildProtoPayload(2, NSFW_FEATURES_PATH),
  });
  if (result.success) return result;

  if (shouldRetryWithAlternateMaskField(result)) {
    const second = await sendEnableRequest({
      ...args,
      protoPayload: buildProtoPayload(3, NSFW_FEATURES_PATH),
    });
    if (second.success) return second;
    second.error = `primary payload failed: ${result.error ?? "unknown"}; alternate mask field failed: ${second.error ?? "unknown"}`;
    result = second;
  }

  if (shouldRetryWithAlternateMaskPath(result)) {
    const third = await sendEnableRequest({
      ...args,
      protoPayload: buildProtoPayload(2, NSFW_FEATURES_ENABLED_PATH),
    });
    if (third.success) return third;
    third.error = `previous payload failed: ${result.error ?? "unknown"}; alternate mask path failed: ${third.error ?? "unknown"}`;
    result = third;
  }

  if (shouldRetryWithLegacyPayload(result)) {
    const legacy = await sendEnableRequest({
      ...args,
      protoPayload: NSFW_PROTO_PAYLOAD_LEGACY,
    });
    if (legacy.success) return legacy;
    legacy.error = `previous payload failed: ${result.error ?? "unknown"}; legacy payload failed: ${legacy.error ?? "unknown"}`;
    result = legacy;
  }

  if (shouldRetryWithAgeVerify(result)) {
    const age = await verifyAgeViaRest(args);
    if (age.success) return age;
    age.error = `gRPC update failed: ${result.error ?? "unknown"}; age-verify fallback failed: ${age.error ?? "unknown"}`;
    result = age;
  }

  return result;
}

export async function enableNsfw(args: {
  token: string;
  cfCookie: string;
  userAgent?: string;
  timeoutMs?: number;
}): Promise<NsfwResult> {
  const token = String(args.token ?? "").trim();
  if (!token) {
    return { success: false, http_status: 0, grpc_status: null, grpc_message: null, error: "missing sso" };
  }

  const timeoutMs = Math.max(1000, Math.min(60_000, Math.floor(Number(args.timeoutMs ?? 15_000))));
  const preferredUa = String(args.userAgent ?? DEFAULT_UA).trim() || DEFAULT_UA;

  const first = await enableChain({ token, cfCookie: args.cfCookie, userAgent: preferredUa, timeoutMs });
  if (first.success) return first;

  if (shouldRetryWithFallbackUa(first) && preferredUa !== FALLBACK_UA) {
    const second = await enableChain({ token, cfCookie: args.cfCookie, userAgent: FALLBACK_UA, timeoutMs });
    if (second.success) return second;
    second.error = `primary attempt failed: ${first.error ?? "unknown"}; fallback attempt failed: ${second.error ?? "unknown"}`;
    return second;
  }

  return first;
}

