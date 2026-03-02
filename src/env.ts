export interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
  KV_CACHE: KVNamespace;

  // Optional vars via wrangler.toml [vars]
  // Cache reset time zone offset minutes (default Asia/Shanghai = 480)
  CACHE_RESET_TZ_OFFSET_MINUTES?: string;

  // Build info (injected by CI)
  BUILD_SHA?: string;

  // CORS allow-list, comma separated. Example:
  // http://127.0.0.1:8000,http://localhost:8000
  CORS_ALLOW_ORIGINS?: string;

  // Max object size to store into KV (Workers KV has per-value limits; default 25MB)
  KV_CACHE_MAX_BYTES?: string;

  // Batch size for daily cleanup
  KV_CLEANUP_BATCH?: string;
}
