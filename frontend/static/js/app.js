// ── API Helper ────────────────────────────────────────────────────────────────
const API_BASE = '/api';

function getToken() { return localStorage.getItem('token'); }
function getUser()  { return JSON.parse(localStorage.getItem('user') || '{}'); }
function saveAuth(data) {
  localStorage.setItem('token', data.token);
  localStorage.setItem('user', JSON.stringify({ name: data.name, email: data.email, role: data.role, id: data.user_id }));
}
function clearAuth() { localStorage.removeItem('token'); localStorage.removeItem('user'); }

async function api(method, endpoint, body = null, isForm = false) {
  const opts = {
    method,
    headers: { 'Authorization': `Bearer ${getToken()}` }
  };
  if (body && !isForm) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (isForm) {
    opts.body = body; // FormData
  }
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, opts);
    const data = await res.json();
    return data;
  } catch (e) {
    return { success: false, message: 'Network error' };
  }
}

// ── Toast ──────────────────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── Auth Guard ──────────────────────────────────────────────────────────────────
function requireAuth(expectedRole) {
  const token = getToken();
  const user = getUser();
  if (!token || !user.role) {
    window.location.href = '/login';
    return false;
  }
  if (expectedRole && user.role !== expectedRole && user.role !== 'admin') {
    showToast('Access denied', 'error');
    window.location.href = `/${user.role}`;
    return false;
  }
  return user;
}

function logout() {
  clearAuth();
  showToast('Logged out', 'info');
  setTimeout(() => window.location.href = '/login', 500);
}

// ── Sidebar Nav Highlight ────────────────────────────────────────────────────────
function setActiveNav(id) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
}

// ── Render user info in sidebar ───────────────────────────────────────────────
function renderUserInfo() {
  const user = getUser();
  const avatarEl = document.getElementById('sidebar-avatar');
  const nameEl   = document.getElementById('sidebar-name');
  const roleEl   = document.getElementById('sidebar-role');
  if (avatarEl) avatarEl.textContent = (user.name || 'U').charAt(0).toUpperCase();
  if (nameEl)   nameEl.textContent = user.name || '';
  if (roleEl)   roleEl.textContent = user.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : '';
}

// ── Modal Helpers ────────────────────────────────────────────────────────────
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// ── Score Color ──────────────────────────────────────────────────────────────
function scoreClass(pct) {
  if (pct >= 70) return 'high';
  if (pct >= 40) return 'medium';
  return 'low';
}

function scoreBadge(pct) {
  const cls = pct >= 70 ? 'badge-success' : pct >= 40 ? 'badge-warning' : 'badge-danger';
  return `<span class="badge ${cls}">${pct}%</span>`;
}

// ── Tab Switching ────────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const group = btn.closest('.tabs').dataset.group;
      document.querySelectorAll(`[data-group="${group}"] .tab-btn`).forEach(b => b.classList.remove('active'));
      document.querySelectorAll(`.tab-content[data-group="${group}"]`).forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.querySelector(`.tab-content[data-tab="${btn.dataset.tab}"][data-group="${group}"]`).classList.add('active');
    });
  });
}

// ── Format Date ────────────────────────────────────────────────────────────
function fmtDate(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

document.addEventListener('DOMContentLoaded', () => { initTabs(); renderUserInfo(); });
