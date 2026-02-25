export async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const ctrl = new AbortController();
  const timeout = Math.max(1, Math.floor(Number(timeoutMs || 0)));
  const timer = setTimeout(() => ctrl.abort("timeout"), timeout);
  try {
    return await fetch(input, { ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

