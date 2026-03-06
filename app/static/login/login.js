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
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      await storeAppKey();
      window.location.href = '/admin/token';
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
  const ok = await fetch('/api/v1/admin/storage').then((res) => res.ok).catch(() => false);
  if (ok) {
    window.location.href = '/admin/token';
  } else {
    clearStoredAppKey();
  }
})();
