import type { MiddlewareHandler } from "hono";
import { getCookie } from "hono/cookie";
import type { Env } from "./env";
import { getSettings } from "./settings";
import { dbFirst } from "./db";
import { validateApiKey } from "./repo/apiKeys";
import { verifyAdminSession } from "./repo/adminSessions";

const ADMIN_SESSION_COOKIE = "g2a_admin_session";

export interface ApiAuthInfo {
  key: string | null;
  name: string;
  is_admin: boolean;
}

function bearerToken(authHeader: string | null): string | null {
  if (!authHeader) return null;
  const match = authHeader.match(/^Bearer\s+(.+)$/i);
  return match?.[1]?.trim() || null;
}

function authError(message: string, code: string): Record<string, unknown> {
  return {
    error: {
      message,
      type: "authentication_error",
      code,
    },
  };
}

function envBool(value: string | undefined): boolean {
  const normalized = String(value ?? "").trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
}

export const requireApiAuth: MiddlewareHandler<{ Bindings: Env; Variables: { apiAuth: ApiAuthInfo } }> = async (
  c,
  next,
) => {
  const token = bearerToken(c.req.header("Authorization") ?? null);
  const settings = await getSettings(c.env);

  if (!token) {
    const globalKey = (settings.grok.api_key ?? "").trim();
    const allowAnonBootstrap = envBool(c.env.ALLOW_ANON_API);
    if (!globalKey && allowAnonBootstrap) {
      const row = await dbFirst<{ c: number }>(
        c.env.DB,
        "SELECT COUNT(1) as c FROM api_keys WHERE is_active = 1",
      );
      if ((row?.c ?? 0) === 0) {
        c.set("apiAuth", { key: null, name: "Anonymous", is_admin: false });
        return next();
      }
    }
    if (!globalKey) {
      return c.json(authError("API Key 未配置，请先设置或显式开启 ALLOW_ANON_API。", "api_key_not_configured"), 401);
    }
    return c.json(authError("缺少认证令牌", "missing_token"), 401);
  }

  const globalKey = (settings.grok.api_key ?? "").trim();
  if (globalKey && token === globalKey) {
    c.set("apiAuth", { key: token, name: "默认管理员", is_admin: true });
    return next();
  }

  const keyInfo = await validateApiKey(c.env.DB, token);
  if (keyInfo) {
    c.set("apiAuth", { key: keyInfo.key, name: keyInfo.name, is_admin: false });
    return next();
  }

  return c.json(authError(`令牌无效，长度 ${token.length}`, "invalid_token"), 401);
};

export const requireAdminAuth: MiddlewareHandler<{ Bindings: Env }> = async (c, next) => {
  const token = bearerToken(c.req.header("Authorization") ?? null) ?? getCookie(c, ADMIN_SESSION_COOKIE) ?? null;
  if (!token) return c.json({ error: "缺少会话", code: "MISSING_SESSION" }, 401);
  const ok = await verifyAdminSession(c.env.DB, token);
  if (!ok) return c.json({ error: "会话已过期", code: "SESSION_EXPIRED" }, 401);
  return next();
};

