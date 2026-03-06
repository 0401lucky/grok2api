const usernameInput = document.getElementById('username-input');
const passwordInput = document.getElementById('password-input');
const linuxdoLoginContainer = document.getElementById('linuxdo-login-container');
const linuxdoLoginButton = document.getElementById('linuxdo-login-button');
const DEFAULT_RETURN_TO = '/admin/token';

usernameInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') passwordInput.focus();
});

passwordInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') login();
});

if (linuxdoLoginButton) {
  linuxdoLoginButton.addEventListener('click', () => {
    window.location.href = `/api/v1/admin/login/linuxdo?return_to=${encodeURIComponent(DEFAULT_RETURN_TO)}`;
  });
}

function normalizeLoginError(error, errorDescription) {
  const text = String(error || '').trim();
  const description = String(errorDescription || '').trim();
  if (description) return description;
  if (!text) return '';
  const map = {
    state_missing: '登录状态已失效，请重新发起 Linux.do 登录。',
    state_mismatch: '登录状态校验失败，请重新发起 Linux.do 登录。',
    oauth_disabled: 'Linux.do 登录尚未启用。',
    oauth_not_configured: 'Linux.do 登录配置不完整。',
    allowlist_denied: '当前 Linux.do 账号未被允许登录后台。',
    token_exchange_failed: 'Linux.do 登录换取令牌失败。',
    userinfo_failed: '获取 Linux.do 用户信息失败。',
    missing_code: '缺少授权 code，请重新登录。',
    invalid_return_to: '回跳地址无效，已拒绝跳转。',
  };
  return map[text] || text;
}

async function loadLoginOptions() {
  try {
    const res = await fetch('/api/v1/admin/login/options');
    const data = await res.json().catch(() => ({}));
    const linuxdo = data?.linuxdo || {};
    const enabled = Boolean((linuxdo.enabled ?? data?.enabled) && (linuxdo.configured ?? data?.configured));
    if (linuxdoLoginContainer) {
      linuxdoLoginContainer.classList.toggle('hidden', !enabled);
    }
  } catch (e) {
    if (linuxdoLoginContainer) {
      linuxdoLoginContainer.classList.add('hidden');
    }
  }
}

async function login() {
  const username = (usernameInput.value || '').trim();
  const password = (passwordInput.value || '').trim();
  if (!username || !password) return;

  try {
    const res = await fetch('/api/v1/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      await storeAppKey();
      window.location.href = DEFAULT_RETURN_TO;
      return;
    }

    const message = data && (data.detail || data.error || data.message)
      ? String(data.detail || data.error || data.message)
      : '用户名或密码错误';
    showToast(message, 'error');
  } catch (e) {
    showToast('连接失败', 'error');
  }
}

(async () => {
  usernameInput.value = 'admin';
  passwordInput.focus();

  const params = new URLSearchParams(window.location.search);
  const loginError = normalizeLoginError(params.get('error'), params.get('error_description'));
  if (loginError) {
    showToast(loginError, 'error');
    const cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete('error');
    cleanUrl.searchParams.delete('error_description');
    window.history.replaceState({}, '', cleanUrl.toString());
  }

  const ok = await fetch('/api/v1/admin/storage').then((res) => res.ok).catch(() => false);
  if (ok) {
    window.location.href = DEFAULT_RETURN_TO;
  } else {
    clearStoredAppKey();
    await loadLoginOptions();
  }
})();
