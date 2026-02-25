from __future__ import annotations

from typing import Tuple


def _extract_cookie_value(cookie_str: str, name: str) -> str | None:
    needle = f"{name}="
    if needle not in cookie_str:
        return None
    for part in cookie_str.split(";"):
        item = part.strip()
        if item.startswith(needle):
            value = item[len(needle) :].strip()
            return value or None
    return None


def parse_sso_pair(raw_token: str) -> Tuple[str, str]:
    raw = str(raw_token or "").strip()
    if not raw:
        return "", ""

    if ";" in raw:
        sso = _extract_cookie_value(raw, "sso") or ""
        sso_rw = _extract_cookie_value(raw, "sso-rw") or sso
        return sso.strip(), sso_rw.strip()

    sso = raw[4:].strip() if raw.startswith("sso=") else raw
    sso_rw = sso
    return sso, sso_rw


def build_auth_cookie(raw_token: str, cf_clearance: str = "") -> str:
    sso, sso_rw = parse_sso_pair(raw_token)
    if not sso:
        return ""
    if not sso_rw:
        sso_rw = sso

    parts = [f"sso-rw={sso_rw}", f"sso={sso}"]
    clearance = str(cf_clearance or "").strip()
    if clearance:
        parts.append(f"cf_clearance={clearance}")
    return ";".join(parts)


__all__ = ["parse_sso_pair", "build_auth_cookie"]
