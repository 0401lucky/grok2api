const APP_KEY_STORAGE = 'grok2api_admin_session';
let cachedApiKey = null;

function clearStoredAppKey() {
  localStorage.removeItem(APP_KEY_STORAGE);
  cachedApiKey = null;
}

async function getStoredAppKey() {
  return (localStorage.getItem(APP_KEY_STORAGE) || '').trim();
}

async function storeAppKey(input) {
  const token = typeof input === 'string'
    ? input.trim()
    : (input && typeof input === 'object' ? String(input.api_key || '').trim() : '');
  if (!token) {
    clearStoredAppKey();
    return;
  }
  localStorage.setItem(APP_KEY_STORAGE, token);
  cachedApiKey = `Bearer ${token}`;
}

function buildAuthHeaders(apiKey) {
  return apiKey ? { 'Authorization': apiKey } : {};
}

async function validateSession(apiKey) {
  try {
    const res = await fetch('/api/v1/admin/storage', {
      headers: buildAuthHeaders(apiKey)
    });
    return res.ok;
  } catch (e) {
    return false;
  }
}

async function ensureApiKey() {
  if (cachedApiKey) {
    const ok = await validateSession(cachedApiKey);
    if (ok) return cachedApiKey;
    clearStoredAppKey();
  }

  const token = await getStoredAppKey();
  if (!token) {
    window.location.href = '/login';
    return null;
  }

  const apiKey = `Bearer ${token}`;
  const ok = await validateSession(apiKey);
  if (!ok) {
    clearStoredAppKey();
    window.location.href = '/login';
    return null;
  }

  cachedApiKey = apiKey;
  return cachedApiKey;
}

function logout() {
  clearStoredAppKey();
  window.location.href = '/login';
}

async function fetchStorageType() {
  const apiKey = await ensureApiKey();
  if (apiKey === null) return null;
  try {
    const res = await fetch('/api/v1/admin/storage', {
      headers: buildAuthHeaders(apiKey)
    });
    if (!res.ok) return null;
    const data = await res.json();
    return (data && data.type) ? String(data.type) : null;
  } catch (e) {
    return null;
  }
}

function formatStorageLabel(type) {
  if (!type) return '-';
  const normalized = type.toLowerCase();
  const map = {
    local: 'local',
    mysql: 'mysql',
    pgsql: 'pgsql',
    postgres: 'pgsql',
    postgresql: 'pgsql',
    d1: 'd1',
    redis: 'redis'
  };
  return map[normalized] || '-';
}

async function updateStorageModeButton() {
  const buttons = Array.from(document.querySelectorAll('#storage-mode-btn, [data-storage-mode-btn]'));
  if (!buttons.length) return;
  buttons.forEach((btn) => {
    btn.textContent = '...';
    btn.title = '存储模式';
    btn.classList.remove('storage-ready');
  });
  const storageType = await fetchStorageType();
  const label = formatStorageLabel(storageType);
  buttons.forEach((btn) => {
    btn.textContent = label === '-' ? label : label.toUpperCase();
    btn.title = '存储模式';
    if (label !== '-') btn.classList.add('storage-ready');
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', updateStorageModeButton);
} else {
  updateStorageModeButton();
}
