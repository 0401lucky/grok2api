let cachedSessionValid = false;

function clearStoredAppKey() {
  cachedSessionValid = false;
}

async function getStoredAppKey() {
  return '';
}

async function storeAppKey() {
  cachedSessionValid = true;
}

function buildAuthHeaders(apiKey) {
  return apiKey ? { Authorization: apiKey } : {};
}

async function validateSession() {
  try {
    const res = await fetch('/api/v1/admin/storage');
    return res.ok;
  } catch (e) {
    return false;
  }
}

async function ensureApiKey() {
  if (cachedSessionValid) return '';
  const ok = await validateSession();
  if (!ok) {
    clearStoredAppKey();
    window.location.href = '/login';
    return null;
  }
  cachedSessionValid = true;
  return '';
}

async function logout() {
  try {
    await fetch('/api/v1/admin/logout', { method: 'POST' });
  } catch (e) {
  } finally {
    clearStoredAppKey();
    window.location.href = '/login';
  }
}

async function fetchStorageType() {
  const apiKey = await ensureApiKey();
  if (apiKey === null) return null;
  try {
    const res = await fetch('/api/v1/admin/storage', {
      headers: buildAuthHeaders(apiKey),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data && data.type ? String(data.type) : null;
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
    redis: 'redis',
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
