const textDecoder = new TextDecoder();

function safeDecodeUri(value: string): string {
  const v = String(value ?? "").trim();
  if (!v) return "";
  try {
    return decodeURIComponent(v.replace(/\+/g, "%20"));
  } catch {
    return v;
  }
}

export function encodeGrpcWebPayload(protoPayload: Uint8Array): ArrayBuffer {
  const payload = protoPayload ?? new Uint8Array();
  const len = payload.length >>> 0;
  const out = new Uint8Array(5 + len);
  out[0] = 0x00;
  out[1] = (len >>> 24) & 0xff;
  out[2] = (len >>> 16) & 0xff;
  out[3] = (len >>> 8) & 0xff;
  out[4] = len & 0xff;
  out.set(payload, 5);
  return out.buffer;
}

export function parseGrpcWebTrailers(body: Uint8Array): Record<string, string> {
  const bytes = body ?? new Uint8Array();
  const trailers: Record<string, string> = {};
  let i = 0;
  while (i + 5 <= bytes.length) {
    const flag = bytes[i] ?? 0;
    const len =
      ((bytes[i + 1] ?? 0) << 24) |
      ((bytes[i + 2] ?? 0) << 16) |
      ((bytes[i + 3] ?? 0) << 8) |
      (bytes[i + 4] ?? 0);
    i += 5;
    if (len < 0 || i + len > bytes.length) break;
    const payload = bytes.slice(i, i + len);
    i += len;

    if (flag & 0x80) {
      const text = textDecoder.decode(payload);
      text
        .split("\r\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .forEach((line) => {
          const idx = line.indexOf(":");
          if (idx <= 0) return;
          const k = line.slice(0, idx).trim().toLowerCase();
          const v = safeDecodeUri(line.slice(idx + 1).trim());
          if (k) trailers[k] = v;
        });
      break;
    }
  }
  return trailers;
}

export function getGrpcStatusAndMessage(
  headers: Headers,
  body?: Uint8Array,
): { grpc_status: number | null; grpc_message: string | null } {
  const statusHeader = String(headers.get("grpc-status") ?? "").trim();
  const messageHeader = safeDecodeUri(String(headers.get("grpc-message") ?? "").trim());

  const parseGrpcStatus = (value: string): number | null => {
    if (!value) return null;
    const n = Number(value);
    return Number.isFinite(n) ? Math.floor(n) : null;
  };

  let grpc_status = parseGrpcStatus(statusHeader);
  let grpc_message = messageHeader || null;

  if (grpc_status === null || !grpc_message) {
    const trailers = parseGrpcWebTrailers(body ?? new Uint8Array());
    if (grpc_status === null && trailers["grpc-status"]) {
      grpc_status = parseGrpcStatus(trailers["grpc-status"] ?? "");
    }
    if (!grpc_message && trailers["grpc-message"]) {
      grpc_message = String(trailers["grpc-message"] ?? "").trim() || null;
    }
  }

  return { grpc_status, grpc_message };
}
