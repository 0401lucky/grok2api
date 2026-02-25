from app.services.grok.cookie import build_auth_cookie, parse_sso_pair


def test_parse_sso_pair_plain_token():
    sso, sso_rw = parse_sso_pair("token-abc")
    assert sso == "token-abc"
    assert sso_rw == "token-abc"


def test_parse_sso_pair_cookie_string():
    sso, sso_rw = parse_sso_pair("foo=bar; sso=token-a; sso-rw=token-b; x=y")
    assert sso == "token-a"
    assert sso_rw == "token-b"


def test_build_auth_cookie_contains_sso_rw_sso_and_cf():
    cookie = build_auth_cookie("sso=token-x", "cf-value")
    assert cookie == "sso-rw=token-x;sso=token-x;cf_clearance=cf-value"
