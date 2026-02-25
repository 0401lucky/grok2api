import asyncio

import orjson

from app.api.v1 import image as image_module


class _DummyInfo:
    def __init__(self, token: str, tags=None, available: bool = True):
        self.token = token
        self.tags = list(tags or [])
        self._available = bool(available)

    def is_available(self) -> bool:
        return self._available


class _DummyPool:
    def __init__(self, infos):
        self._infos = list(infos)
        self._idx = {}
        for info in self._infos:
            token = str(getattr(info, "token", "") or "").strip()
            if token.startswith("sso="):
                token = token[4:]
            if token:
                self._idx[token] = info

    def list(self):
        return list(self._infos)

    def get(self, token):
        raw = str(token or "").strip()
        if raw.startswith("sso="):
            raw = raw[4:]
        return self._idx.get(raw)


class _DummyManager:
    def __init__(self, pools):
        self.pools = pools
        self.sync_calls = []

    async def sync_usage(self, token, *_args, **_kwargs):
        self.sync_calls.append(token)
        return True


def _no_quota(*_args, **_kwargs):
    async def _inner():
        return None

    return _inner()


def _no_record(*_args, **_kwargs):
    async def _inner():
        return None

    return _inner()


def test_nsfw_generation_prefers_tagged_tokens(monkeypatch):
    token_a = _DummyInfo("token-a", tags=[])
    token_b = _DummyInfo("token-b", tags=["nsfw"])
    mgr = _DummyManager({"ssoBasic": _DummyPool([token_a, token_b])})
    tried = []

    async def _fake_get_token_for_model(_model_id: str):
        return mgr, "token-a"

    async def _fake_collect(token: str, **_kwargs):
        tried.append(token)
        if token == "token-a":
            raise AssertionError("should not use untagged token when tagged token exists")
        return ["img-tagged"]

    monkeypatch.setattr(image_module, "enforce_daily_quota", _no_quota)
    monkeypatch.setattr(image_module, "_record_request", _no_record)
    monkeypatch.setattr(image_module, "_get_token_for_model", _fake_get_token_for_model)
    monkeypatch.setattr(image_module, "_collect_experimental_generation_images", _fake_collect)

    req = image_module.ImageGenerationRequest(
        prompt="demo",
        model="grok-imagine-1.0",
        n=1,
        stream=False,
    )
    resp = asyncio.run(image_module.create_image_nsfw(req, api_key="k"))
    payload = orjson.loads(resp.body)

    assert tried == ["token-b"]
    assert payload["data"][0]["b64_json"] == "img-tagged"
    assert mgr.sync_calls == ["token-b"]


def test_nsfw_generation_falls_back_to_all_tokens_when_no_tag(monkeypatch):
    token_a = _DummyInfo("token-a", tags=[])
    token_b = _DummyInfo("token-b", tags=[])
    mgr = _DummyManager({"ssoBasic": _DummyPool([token_a, token_b])})
    tried = []

    async def _fake_get_token_for_model(_model_id: str):
        return mgr, "token-a"

    async def _fake_collect(token: str, **_kwargs):
        tried.append(token)
        return ["img-fallback"]

    monkeypatch.setattr(image_module, "enforce_daily_quota", _no_quota)
    monkeypatch.setattr(image_module, "_record_request", _no_record)
    monkeypatch.setattr(image_module, "_get_token_for_model", _fake_get_token_for_model)
    monkeypatch.setattr(image_module, "_collect_experimental_generation_images", _fake_collect)

    req = image_module.ImageGenerationRequest(
        prompt="demo",
        model="grok-imagine-1.0",
        n=1,
        stream=False,
    )
    resp = asyncio.run(image_module.create_image_nsfw(req, api_key="k"))
    payload = orjson.loads(resp.body)

    assert tried[0] == "token-a"
    assert payload["data"][0]["b64_json"] == "img-fallback"
    assert mgr.sync_calls == ["token-a"]
