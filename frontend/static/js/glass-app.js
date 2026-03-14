/* glass-app.js — Global utilities for Glass UI */
const API = '/api';

// ── Auth ──────────────────────────────────────────────────────
const getToken = () => localStorage.getItem('token');
const getUser  = () => JSON.parse(localStorage.getItem('user') || '{}');
const saveAuth = d => {
  localStorage.setItem('token', d.token);
  localStorage.setItem('user', JSON.stringify({ name:d.name, email:d.email, role:d.role, id:d.user_id }));
};
const clearAuth = () => { localStorage.removeItem('token'); localStorage.removeItem('user'); };

async function api(method, endpoint, body=null, isForm=false) {
  const opts = { method, headers: { Authorization: `Bearer ${getToken()}` } };
  if (body && !isForm) { opts.headers['Content-Type']='application/json'; opts.body=JSON.stringify(body); }
  else if (isForm) opts.body = body;
  try {
    const res = await fetch(`${API}${endpoint}`, opts);
    return await res.json();
  } catch { return { success:false, message:'Network error' }; }
}

// ── Toast ──────────────────────────────────────────────────────
function toast(msg, type='info') {
  let stack = document.getElementById('toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.id = 'toast-stack';
    stack.className = 'toast-stack';
    document.body.appendChild(stack);
  }
  const icons = { success:'✅', error:'❌', info:'💡', warning:'⚠️' };
  const el = document.createElement('div');
  el.className = `g-toast ${type}`;
  el.innerHTML = `<span class="g-toast-icon">${icons[type]||'💡'}</span><span>${msg}</span>`;
  stack.appendChild(el);
  setTimeout(() => { el.style.opacity='0'; el.style.transform='translateX(110%)'; el.style.transition='all .3s'; setTimeout(()=>el.remove(),300); }, 3500);
}

// ── Auth Guards ────────────────────────────────────────────────
function requireAuth(role) {
  const token = getToken(), user = getUser();
  if (!token) { window.location.href = '/login'; return null; }
  if (role && user.role !== role && user.role !== 'admin') {
    toast('Access denied','error');
    setTimeout(()=>window.location.href=`/${user.role||'login'}`,600);
    return null;
  }
  return user;
}

function logout() {
  clearAuth();
  toast('Signed out successfully','info');
  setTimeout(()=>window.location.href='/login',600);
}

// ── Sidebar fill ───────────────────────────────────────────────
function fillSidebar() {
  const u = getUser();
  const ava = document.getElementById('g-user-ava');
  const nm  = document.getElementById('g-user-name');
  const rl  = document.getElementById('g-user-role');
  if (ava) ava.textContent = (u.name||'?')[0].toUpperCase();
  if (nm)  nm.textContent  = u.name || '';
  if (rl)  rl.textContent  = (u.role||'').charAt(0).toUpperCase()+(u.role||'').slice(1);
}

// ── Nav section switcher ───────────────────────────────────────
function showSection(id, label) {
  document.querySelectorAll('.g-section').forEach(s=>s.style.display='none');
  const sec = document.getElementById('sec-'+id);
  if (sec) { sec.style.display='block'; sec.classList.add('fade-in'); }
  document.querySelectorAll('.g-nav-item').forEach(n=>n.classList.remove('active'));
  const navItem = document.getElementById('nav-'+id);
  if (navItem) navItem.classList.add('active');
  const titleEl = document.getElementById('g-page-title');
  if (titleEl && label) titleEl.textContent = label;
}

// ── Modal helpers ──────────────────────────────────────────────
const openModal  = id => document.getElementById(id)?.classList.add('open');
const closeModal = id => document.getElementById(id)?.classList.remove('open');

// Close on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('g-modal-overlay')) closeModal(e.target.id);
});

// ── Score helpers ──────────────────────────────────────────────
function scoreClass(pct) { return pct>=70?'high':pct>=40?'medium':'low'; }
function scoreBadge(pct) {
  const cls = pct>=70?'badge-success':pct>=40?'badge-warning':'badge-danger';
  return `<span class="badge ${cls}">${pct}%</span>`;
}

// ── Tabs ───────────────────────────────────────────────────────
function initGlassTabs() {
  document.querySelectorAll('.g-tabs').forEach(tabBar=>{
    const group = tabBar.dataset.group;
    tabBar.querySelectorAll('.g-tab-btn').forEach(btn=>{
      btn.addEventListener('click',()=>{
        tabBar.querySelectorAll('.g-tab-btn').forEach(b=>b.classList.remove('active'));
        document.querySelectorAll(`.g-tab-content[data-group="${group}"]`).forEach(c=>c.classList.remove('active'));
        btn.classList.add('active');
        document.querySelector(`.g-tab-content[data-tab="${btn.dataset.tab}"][data-group="${group}"]`)?.classList.add('active');
      });
    });
  });
}

// ── Date format ────────────────────────────────────────────────
function fmtDate(s) { if(!s)return'—'; return new Date(s).toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}); }
function fmtDateTime(s) { if(!s)return'—'; return new Date(s).toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}); }

// ── Drag & Drop Upload ─────────────────────────────────────────
function initDropZone(zoneId, inputId, onFiles) {
  const zone  = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  if (!zone || !input) return;
  zone.addEventListener('click',()=>input.click());
  zone.addEventListener('dragover',e=>{ e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave',()=>zone.classList.remove('dragover'));
  zone.addEventListener('drop',e=>{ e.preventDefault(); zone.classList.remove('dragover'); onFiles(e.dataTransfer.files); });
  input.addEventListener('change',()=>onFiles(input.files));
}

// ── Lib check banner ──────────────────────────────────────────
async function checkDepsAndWarn() {
  const d = await api('GET','/ml/install-check');
  if (d.success) {
    const missing = Object.entries(d.libraries).filter(([,v])=>v.includes('❌')).map(([k])=>k);
    if (missing.length) toast(`Missing Python packages: ${missing.join(', ')} — run install commands below`,'warning');
  }
}

document.addEventListener('DOMContentLoaded',()=>{ fillSidebar(); initGlassTabs(); });
