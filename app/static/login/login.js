const usernameInput = document.getElementById('username-input');
const passwordInput = document.getElementById('password-input');

usernameInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') passwordInput.focus();
});

passwordInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') login();
});

async function login() {
  const username = (usernameInput.value || '').trim();
  const password = (passwordInput.value || '').trim();
  if (!username || !password) return;

  try {
    const res = await fetch('/api/v1/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json().catch(() => ({}));

    if (res.ok && data && data.api_key) {
      await storeAppKey(data.api_key);
      window.location.href = '/admin/token';
    } else {
      const message = (data && (data.detail || data.error)) ? String(data.detail || data.error) : '用户名或密码错误';
      showToast(message, 'error');
    }
  } catch (e) {
    showToast('连接失败', 'error');
  }
}

// Auto-redirect checks
(async () => {
  const existingToken = await getStoredAppKey();
  usernameInput.value = 'admin';
  passwordInput.focus();

  if (!existingToken) return;

  const res = await fetch('/api/v1/admin/storage', {
    headers: buildAuthHeaders(`Bearer ${existingToken}`)
  }).catch(() => null);
  if (res && res.ok) {
    window.location.href = '/admin/token';
    return;
  }
  clearStoredAppKey();
})();
