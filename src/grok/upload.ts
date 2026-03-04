import type { GrokSettings } from "../settings";
import { getDynamicHeaders } from "./headers";
import { arrayBufferToBase64 } from "../utils/base64";

const UPLOAD_API = "https://grok.com/rest/app-chat/upload-file";

const MIME_DEFAULT = "image/jpeg";

function isUrl(input: string): boolean {
  try {
    const u = new URL(input);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

function parseAllowHosts(raw: string | undefined): Set<string> {
  return new Set(
    String(raw ?? "")
      .split(",")
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
}

function isPrivateIpv4(hostname: string): boolean {
  const m = hostname.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (!m) return false;
  const octets = m.slice(1).map((s) => Number(s));
  if (octets.some((n) => !Number.isInteger(n) || n < 0 || n > 255)) return true;
  const a = octets[0] ?? -1;
  const b = octets[1] ?? -1;
  if (a === 10) return true;
  if (a === 127) return true;
  if (a === 169 && b === 254) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 192 && b === 168) return true;
  return false;
}

function isPrivateHostname(hostname: string): boolean {
  const h = hostname.toLowerCase();
  if (!h) return true;
  if (h === "localhost" || h.endsWith(".localhost")) return true;
  if (h === "::1") return true;
  return isPrivateIpv4(h);
}

async function readArrayBufferWithLimit(resp: Response, maxBytes: number): Promise<ArrayBuffer> {
  const contentLength = Number(resp.headers.get("content-length") || 0);
  if (Number.isFinite(contentLength) && contentLength > maxBytes) {
    throw new Error(`远程图片过大: ${contentLength} > ${maxBytes}`);
  }
  if (!resp.body) {
    const buf = await resp.arrayBuffer();
    if (buf.byteLength > maxBytes) throw new Error(`远程图片过大: ${buf.byteLength} > ${maxBytes}`);
    return buf;
  }

  const reader = resp.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (!value) continue;
    total += value.byteLength;
    if (total > maxBytes) throw new Error(`远程图片过大: ${total} > ${maxBytes}`);
    chunks.push(value);
  }
  const out = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return out.buffer;
}

function guessExtFromMime(mime: string): string {
  const m = mime.split(";")[0]?.trim() ?? "";
  const parts = m.split("/");
  return parts.length === 2 && parts[1] ? parts[1] : "jpg";
}

function parseDataUrl(dataUrl: string): { base64: string; mime: string } {
  const trimmed = dataUrl.trim();
  const comma = trimmed.indexOf(",");
  if (comma === -1) return { base64: trimmed, mime: MIME_DEFAULT };
  const header = trimmed.slice(0, comma);
  const base64 = trimmed.slice(comma + 1);
  const match = header.match(/^data:([^;]+);base64$/i);
  return { base64, mime: match?.[1] ?? MIME_DEFAULT };
}

export async function uploadImage(
  imageInput: string,
  cookie: string,
  settings: GrokSettings,
  options?: {
    requestOrigin?: string;
    allowHostsCsv?: string;
    maxBytes?: number;
    timeoutMs?: number;
  },
): Promise<{ fileId: string; fileUri: string }> {
  let base64 = "";
  let mime = MIME_DEFAULT;
  let filename = "image.jpg";
  const maxBytes = Math.max(1, Number(options?.maxBytes ?? 10 * 1024 * 1024));
  const timeoutMs = Math.max(1000, Number(options?.timeoutMs ?? 10000));

  if (isUrl(imageInput)) {
    const parsed = new URL(imageInput);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      throw new Error("仅支持 http/https 图片地址");
    }

    const allowedHosts = parseAllowHosts(options?.allowHostsCsv);
    if (options?.requestOrigin) {
      try {
        allowedHosts.add(new URL(options.requestOrigin).hostname.toLowerCase());
      } catch {
        // ignore invalid request origin
      }
    }
    allowedHosts.add("assets.grok.com");
    const hostname = parsed.hostname.toLowerCase();
    if (isPrivateHostname(hostname)) {
      throw new Error("禁止访问内网或本地地址");
    }
    if (allowedHosts.size > 0 && !allowedHosts.has(hostname)) {
      throw new Error(`不允许的图片域名: ${hostname}`);
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort("timeout"), timeoutMs);
    const r = await fetch(imageInput, { redirect: "follow", signal: controller.signal }).finally(() => clearTimeout(timer));
    if (!r.ok) throw new Error(`下载图片失败: ${r.status}`);
    mime = r.headers.get("content-type")?.split(";")[0] ?? MIME_DEFAULT;
    if (!mime.startsWith("image/")) mime = MIME_DEFAULT;
    const content = await readArrayBufferWithLimit(r, maxBytes);
    base64 = arrayBufferToBase64(content);
    filename = `image.${guessExtFromMime(mime)}`;
  } else if (imageInput.trim().startsWith("data:image")) {
    const parsed = parseDataUrl(imageInput);
    base64 = parsed.base64;
    mime = parsed.mime;
    const estimated = Math.floor((base64.length * 3) / 4);
    if (estimated > maxBytes) throw new Error(`图片数据过大: ${estimated} > ${maxBytes}`);
    filename = `image.${guessExtFromMime(mime)}`;
  } else {
    base64 = imageInput.trim();
    const estimated = Math.floor((base64.length * 3) / 4);
    if (estimated > maxBytes) throw new Error(`图片数据过大: ${estimated} > ${maxBytes}`);
    filename = "image.jpg";
    mime = MIME_DEFAULT;
  }

  const body = JSON.stringify({
    fileName: filename,
    fileMimeType: mime,
    content: base64,
  });

  const headers = getDynamicHeaders(settings, "/rest/app-chat/upload-file");
  headers.Cookie = cookie;

  const resp = await fetch(UPLOAD_API, { method: "POST", headers, body });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`上传失败: ${resp.status} ${text.slice(0, 200)}`);
  }
  const data = (await resp.json()) as { fileMetadataId?: string; fileUri?: string };
  return { fileId: data.fileMetadataId ?? "", fileUri: data.fileUri ?? "" };
}

