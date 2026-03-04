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

  // 显式允许无 API key 启动（仅用于受控 bootstrap）
  ALLOW_ANON_API?: string;

  // 是否允许通过 ?debug=1 输出错误细节（默认关闭）
  DEBUG_ERRORS?: string;

  // 仅用于受控环境 bootstrap：临时允许弱管理员密码
  ALLOW_WEAK_ADMIN_PASSWORD?: string;

  // 允许从远程 URL 拉取 image_url 的主机白名单（逗号分隔）
  IMAGE_FETCH_ALLOW_HOSTS?: string;

  // 远程 image_url 拉取的最大字节数
  IMAGE_FETCH_MAX_BYTES?: string;

  // 是否允许 /images/u_<base64url(full_url)> 代理模式
  ALLOW_IMAGE_URL_PROXY?: string;
}
