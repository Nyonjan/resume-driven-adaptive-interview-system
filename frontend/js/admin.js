/* ═══════════════════════════════════════════════════════════
   CONFIGURATION
═══════════════════════════════════════════════════════════ */
const API_BASE = 'http://127.0.0.1:5000/api/admin';

/* ═══════════════════════════════════════════════════════════
   AUTH GATE: Instant check to prevent flash
═══════════════════════════════════════════════════════════ */
(function () {
  const active = localStorage.getItem('admin_session_active');
  const cachedUsername = localStorage.getItem('admin_username');
  const style = document.createElement('style');
  style.id = 'authGateStyle';
  // Hide both initially to avoid messy layout flashes
  style.innerHTML = '#loginScreen, #dashboardScreen { display: none !important; }';
  document.head.appendChild(style);

  window.addEventListener('DOMContentLoaded', () => {
    const login = document.getElementById('loginScreen');
    const dash = document.getElementById('dashboardScreen');
    if (active) {
      if (dash) {
        dash.classList.remove('hidden');
        dash.style.display = 'flex';
      }
      if (login) login.style.display = 'none';

      if (cachedUsername) {
        const nameEl = document.getElementById('topbarName');
        const avatarEl = document.getElementById('topbarAvatar');
        if (nameEl) nameEl.textContent = cachedUsername;
        if (avatarEl) avatarEl.textContent = cachedUsername.charAt(0).toUpperCase();
      }
    } else {
      if (login) login.style.display = 'flex';
      if (dash) dash.style.display = 'none';
    }
    // Release the gate
    style.remove();
  });
})();

/* ═══════════════════════════════════════════════════════════
   DOM REFERENCES & INITIALIZATION
═══════════════════════════════════════════════════════════ */
let loginScreen, dashboardScreen, loginForm, loginBtn, loginError, loginErrorMsg;
let adminUsernameInp, adminPasswordInp, togglePw, pwEyeIcon, logoutBtn;
let logoutOverlay, cancelLogout, confirmLogout, navItems;

// Global references for sliding panels and forms
let actionPanel, csvContent, qContent, qForm;
let jobActionPanel, jobFormEl;
let skillActionPanel, skillPanelContent, synonymPanelContent, skillForm, synonymForm;
let userSearchInp, backToListBtn;

const sections = {};

function initDOM() {
  loginScreen = document.getElementById('loginScreen');
  dashboardScreen = document.getElementById('dashboardScreen');
  loginForm = document.getElementById('loginForm');
  loginBtn = document.getElementById('loginBtn');
  loginError = document.getElementById('loginError');
  loginErrorMsg = document.getElementById('loginErrorMsg');
  adminUsernameInp = document.getElementById('adminUsername');
  adminPasswordInp = document.getElementById('adminPassword');
  togglePw = document.getElementById('togglePw');
  pwEyeIcon = document.getElementById('pwEyeIcon');
  logoutBtn = document.getElementById('logoutBtn');
  logoutOverlay = document.getElementById('logoutOverlay');
  cancelLogout = document.getElementById('cancelLogout');
  confirmLogout = document.getElementById('confirmLogout');

  navItems = document.querySelectorAll('.nav-item[data-section]');
  
  sections.overview = document.getElementById('section_overview');
  sections.users = document.getElementById('section_users');
  sections.questions = document.getElementById('section_questions');
  sections.jobs = document.getElementById('section_jobs');
  sections.skills = document.getElementById('section_skills');
  sections.settings = document.getElementById('section_settings');

  // Question Panel References
  actionPanel = document.getElementById('actionPanel');
  csvContent = document.getElementById('csvPanelContent');
  qContent = document.getElementById('questionPanelContent');
  qForm = document.getElementById('questionForm');

  // Job Panel References
  jobActionPanel = document.getElementById('jobActionPanel');
  jobFormEl = document.getElementById('jobForm');

  // Skill Panel References
  skillActionPanel = document.getElementById('skillActionPanel');
  skillPanelContent = document.getElementById('skillPanelContent');
  synonymPanelContent = document.getElementById('synonymPanelContent');
  skillForm = document.getElementById('skillForm');
  synonymForm = document.getElementById('synonymForm');

  // Other references
  userSearchInp = document.getElementById('userSearch');
  backToListBtn = document.getElementById('btnBackToList');

  // ── ATTACH LISTENERS ───────────────────────────────────────

  // Navigation
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const target = item.getAttribute('data-section');
      switchSection(target);
    });
  });

  // Login
  if (loginForm) loginForm.addEventListener('submit', handleLogin);

  // Password Toggle
  if (togglePw) {
    togglePw.addEventListener('click', () => {
      const isHidden = adminPasswordInp.type === 'password';
      adminPasswordInp.type = isHidden ? 'text' : 'password';
      if (pwEyeIcon) pwEyeIcon.className = isHidden ? 'fas fa-eye' : 'fas fa-eye-slash';
    });
  }

  // Logout
  if (logoutBtn) logoutBtn.addEventListener('click', () => logoutOverlay?.classList.add('show'));
  if (cancelLogout) cancelLogout.addEventListener('click', () => logoutOverlay?.classList.remove('show'));
  if (logoutOverlay) logoutOverlay.addEventListener('click', (e) => {
    if (e.target === logoutOverlay) logoutOverlay.classList.remove('show');
  });
  if (confirmLogout) confirmLogout.addEventListener('click', handleLogout);

  // User Search
  if (userSearchInp) {
    userSearchInp.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      const filtered = allUsers.filter(u =>
        u.full_name.toLowerCase().includes(query) ||
        u.email.toLowerCase().includes(query)
      );
      renderUserTable(filtered);
    });
  }
  if (backToListBtn) backToListBtn.addEventListener('click', () => toggleView('list'));

  // Question Filters
  ['filterSkill', 'filterDifficulty', 'filterExp'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', loadQuestions);
  });

  // Question Form
  if (qForm) qForm.addEventListener('submit', handleQuestionSubmit);

  // Job Form
  if (jobFormEl) jobFormEl.addEventListener('submit', handleJobSubmit);

  // Skill Forms
  if (skillForm) skillForm.addEventListener('submit', handleSkillSubmit);
  if (synonymForm) synonymForm.addEventListener('submit', handleSynonymSubmit);

  // Settings Form
  const settingsForm = document.getElementById('generalSettingsForm');
  if (settingsForm) {
    settingsForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      await saveGeneralSettings();
    });
  }

  // Admin Account Form
  const accountForm = document.getElementById('adminAccountForm');
  if (accountForm) {
    accountForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      await saveAdminAccount();
    });
  }

  // Initial gate check already happened in IIFE, but we confirm session status here
  checkSession();
}

window.addEventListener('DOMContentLoaded', initDOM);

/* ═══════════════════════════════════════════════════════════
   HELPERS
═══════════════════════════════════════════════════════════ */
function showLoginScreen() {
  if (loginScreen) loginScreen.style.display = 'flex';
  if (dashboardScreen) {
    dashboardScreen.style.display = 'none';
    dashboardScreen.classList.add('hidden');
  }
}

function showDashboard(adminData) {
  if (loginScreen) loginScreen.style.display = 'none';
  if (dashboardScreen) {
    dashboardScreen.classList.remove('hidden');
    dashboardScreen.style.display = 'flex';
  }

  // Populate admin name in sidebar (prefer username)
  const name = adminData.username || 'Admin';
  localStorage.setItem('admin_username', name); // Cache for immediate next load
  const nameEl = document.getElementById('topbarName');
  const avatarEl = document.getElementById('topbarAvatar');
  if (nameEl) nameEl.textContent = name;
  if (avatarEl) avatarEl.textContent = name.charAt(0).toUpperCase();

  // Default view
  switchSection('overview');
  updateDashboardStats();
  
  // Ensure branding is applied from cached settings if possible, or fetch it
  applyBranding();
}

function switchSection(id) {
  // Update UI active state
  navItems.forEach(btn => {
    const isActive = btn.getAttribute('data-section') === id;
    btn.classList.toggle('active', isActive);
    if (btn.parentElement && btn.parentElement.tagName === 'LI') {
      btn.parentElement.classList.toggle('active', isActive);
    }
  });

  // Show/Hide sections
  Object.keys(sections).forEach(key => {
    if (sections[key]) {
      sections[key].classList.toggle('hidden', key !== id);
    }
  });

  // Specific logic for sections
  if (id === 'users') {
    toggleView('list');
    loadUsers();
  } else if (id === 'overview') {
    updateDashboardStats();
  } else if (id === 'questions') {
    loadSkillsList();
    loadQuestions();
  } else if (id === 'jobs') {
    loadSkillsList();
    loadJobs();
  } else if (id === 'analytics') {
    loadAnalytics();
  } else if (id === 'skills') {
    loadSkillsTable();
  } else if (id === 'settings') {
    loadGeneralSettings();
    loadAllImageSettings();
  }
}

/* ═══════════════════════════════════════════════════════════
   SETTINGS TABS & SITE IMAGES
═══════════════════════════════════════════════════════════ */

function switchSettingsTab(tab) {
  const tabGeneral = document.getElementById('tab-general');
  const tabImages = document.getElementById('tab-images');
  const contentGeneral = document.getElementById('settingsTabGeneral');
  const contentImages = document.getElementById('settingsTabImages');

  if (tab === 'general') {
    tabGeneral.classList.add('active');
    tabImages.classList.remove('active');
    contentGeneral.classList.remove('hidden');
    contentImages.classList.add('hidden');
  } else {
    tabImages.classList.add('active');
    tabGeneral.classList.remove('active');
    contentImages.classList.remove('hidden');
    contentGeneral.classList.add('hidden');
    loadAllImageSettings();
  }
}

async function loadAllImageSettings() {
  try {
    const res = await fetch(`${API_BASE}/settings/public`);
    const data = await res.json();
    if (data.success && data.settings) {
      const keys = [
        'hero_image_url', 'audience_1_image_url', 'audience_2_image_url', 'audience_3_image_url',
        'advantage_1_image_url', 'advantage_2_image_url', 'advantage_3_image_url'
      ];
      
      keys.forEach(key => {
        const url = data.settings[key];
        showImagePreview(key, url);
      });
    }
  } catch (e) {
    console.error("Error loading image settings:", e);
  }
}

function showImagePreview(configKey, url) {
  const img = document.getElementById(`img_preview_${configKey}`);
  const empty = document.getElementById(`img_empty_${configKey}`);
  
  if (!img || !empty) return;

  if (url) {
    img.src = url;
    img.style.display = 'block';
    empty.style.display = 'none';
  } else {
    img.style.display = 'none';
    empty.style.display = 'flex';
  }
}

async function uploadSiteImage(event, configKey) {
  const file = event.target.files[0];
  if (!file) return;

  // Optimistic preview
  const reader = new FileReader();
  reader.onload = (e) => showImagePreview(configKey, e.target.result);
  reader.readAsDataURL(file);

  const formData = new FormData();
  formData.append('file', file);
  formData.append('config_key', configKey);

  try {
    const res = await fetch(`${API_BASE}/upload-image`, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
    const data = await res.json();
    
    if (data.success) {
      showImagePreview(configKey, data.image_url);
      alert(`Successfully updated image for ${configKey.replace(/_/g, ' ')}`);
    } else {
      alert(`Error updating image: ${data.message}`);
      // Revert preview on error by reloading settings
      loadAllImageSettings();
    }
  } catch (e) {
    alert("Server error uploading image.");
    loadAllImageSettings();
  } finally {
    // Reset file input
    event.target.value = '';
  }
}

async function resetSiteImage(configKey) {
  if (!confirm('Are you sure you want to reset this image to default?')) return;

  try {
    const res = await fetch(`${API_BASE}/upload-image`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ config_key: configKey }),
      credentials: 'include'
    });
    const data = await res.json();
    
    if (data.success) {
      showImagePreview(configKey, null);
    } else {
      alert(`Error resetting image: ${data.message}`);
    }
  } catch (e) {
    alert("Server error resetting image.");
  }
}

async function updateDashboardStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      const s = data.stats;
      animateCount(document.getElementById('statUsers'), s.totalUsers);
      animateCount(document.getElementById('statCompleted'), s.completedSessions);

      // Trigger detailed analytics for the new overview components
      loadDetailedAnalytics();
    }
  } catch (e) {
    console.error("Failed to load dashboard stats", e);
  }
}

async function loadDetailedAnalytics() {
  const container = document.getElementById('skillPopularityContainer');
  const trendEl = document.getElementById('statTrend');

  try {
    const res = await fetch(`${API_BASE}/analytics`, { credentials: 'include' });
    const data = await res.json();

    if (data.success) {
      // 1. Update Activity Trend (Last 7 Days)
      const totalActivity = data.activityTrend.reduce((sum, item) => sum + item.count, 0);
      animateCount(trendEl, totalActivity);

      // 2. Render Skill Popularity
      renderSkillPopularity(data.skillPopularity);
    }
  } catch (e) {
    console.error("Failed to load detailed analytics", e);
    if (container) container.innerHTML = '<div style="color:var(--red);text-align:center;padding:20px;">Failed to load analytics.</div>';
  }
}

function renderSkillPopularity(skills) {
  const container = document.getElementById('skillPopularityContainer');
  if (!container) return;

  if (!skills || skills.length === 0) {
    container.innerHTML = '<p style="text-align:center;color:var(--muted);padding:20px;">No skill data available yet.</p>';
    return;
  }

  // We'll show top 6 for a clean look
  const displaySkills = skills.slice(0, 6);
  const maxCount = Math.max(...displaySkills.map(s => s.user_count));

  container.innerHTML = displaySkills.map(s => {
    const pct = maxCount > 0 ? (s.user_count / maxCount) * 100 : 0;
    return `
      <div class="skill-bar-row">
        <div class="skill-bar-info">
          <span class="skill-bar-name">${s.skill_name}</span>
          <span class="skill-bar-count">${s.user_count} Users</span>
        </div>
        <div class="skill-bar-bg">
          <div class="skill-bar-fill" style="width: ${pct}%"></div>
        </div>
      </div>
    `;
  }).join('');
}

function animateCount(el, target) {
  if (!el) return;
  let start = 0;
  const duration = 1000;
  const stepTime = 30;
  const steps = duration / stepTime;
  const increment = target / steps;

  const timer = setInterval(() => {
    start += increment;
    if (start >= target) {
      el.textContent = Math.floor(target).toLocaleString();
      clearInterval(timer);
    } else {
      el.textContent = Math.floor(start).toLocaleString();
    }
  }, stepTime);
}

/* ═══════════════════════════════════════════════════════════
   USER MANAGEMENT LOGIC
═══════════════════════════════════════════════════════════ */
let allUsers = [];

async function loadUsers() {
  const tbody = document.getElementById('userTableBody');
  const loader = document.getElementById('tableLoading');

  if (tbody) tbody.innerHTML = '';
  if (loader) loader.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/users`, { credentials: 'include' });
    const data = await res.json();

    if (data.success) {
      allUsers = data.users;
      const countEl = document.getElementById('totalUsersCount');
      if (countEl) countEl.textContent = allUsers.length;
      renderUserTable(allUsers);
    }
  } catch (e) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--red);">Failed to load users.</td></tr>';
  } finally {
    if (loader) loader.classList.add('hidden');
  }
}

function renderUserTable(usersList) {
  const tbody = document.getElementById('userTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (usersList.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:40px;">No users found.</td></tr>';
    return;
  }

  usersList.forEach(user => {
    const row = document.createElement('tr');
    const dateStr = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A';

    const avatarContent = user.avatar
      ? `<img src="../images/avatar/${user.avatar}" alt="Avatar" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`
      : user.full_name.charAt(0);

    row.innerHTML = `
      <td>
        <div class="user-cell">
          <div class="user-avatar">${avatarContent}</div>
          <strong>${user.full_name}</strong>
        </div>
      </td>
      <td style="color:var(--muted);">${user.email}</td>
      <td>${dateStr}</td>
      <td>
        <div style="display:flex; gap:8px;">
          <button class="btn-view" onclick="viewUserProfile(${user.id})">View Profile</button>
          <button class="btn-view" style="color:var(--red); border-color:rgba(239,68,68,0.3);" onclick="deleteUser(${user.id}, '${user.full_name}')">Delete</button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// Search Logic moved to initDOM

// Profile Detail View
async function viewUserProfile(userId) {
  toggleView('profile');

  // Clear previous
  const nameEl = document.getElementById('profName');
  const emailEl = document.getElementById('profEmail');
  const skillsEl = document.getElementById('profSkills');
  const historyEl = document.getElementById('profHistory');
  const resumeEl = document.getElementById('profResume');
  
  if (nameEl) nameEl.textContent = 'Loading...';
  if (emailEl) emailEl.textContent = '';
  if (skillsEl) skillsEl.innerHTML = '';
  if (historyEl) historyEl.innerHTML = '';
  if (resumeEl) resumeEl.textContent = 'Loading...';

  try {
    const res = await fetch(`${API_BASE}/users/${userId}`, { credentials: 'include' });
    const data = await res.json();

    if (data.success) {
      const u = data.user;
      if (nameEl) nameEl.textContent = u.fullName;
      if (emailEl) emailEl.textContent = u.email;

      const profAvatarEl = document.getElementById('profAvatar');
      if (profAvatarEl) {
        if (u.avatar) {
          profAvatarEl.innerHTML = `<img src="../images/avatar/${u.avatar}" alt="Avatar" style="width:100%; height:100%; border-radius:inherit; object-fit:cover;">`;
          profAvatarEl.style.background = 'none';
        } else {
          profAvatarEl.textContent = u.fullName.charAt(0);
          profAvatarEl.style.background = 'linear-gradient(135deg, var(--accent), #3b82f6)';
        }
      }

      // Resume
      if (resumeEl) resumeEl.textContent = u.resume || 'No resume content found.';

      // Skills
      if (skillsEl) {
        if (u.skills && u.skills.length > 0) {
          u.skills.forEach(s => {
            const pill = document.createElement('div');
            pill.className = 'skill-pill';
            pill.innerHTML = `<span class="name">${s.name}</span><span class="meta">${s.years}yr • ${s.level}</span>`;
            skillsEl.appendChild(pill);
          });
        } else {
          skillsEl.innerHTML = '<span style="color:var(--muted);font-size:0.9rem;">No skills extracted yet.</span>';
        }
      }

      // History
      if (historyEl) {
        if (u.history && u.history.length > 0) {
          u.history.forEach(h => {
            const item = document.createElement('div');
            item.className = 'history-item';
            const dateAt = new Date(h.started_at).toLocaleDateString();
            const score = h.avg_score ? (h.avg_score * 100).toFixed(0) + '%' : 'N/A';

            item.innerHTML = `
              <div class="info">
                <h4>Interview Session #${h.id}</h4>
                <span>${dateAt} • ${h.status.toUpperCase()}</span>
              </div>
              <div class="score-badge">
                <span class="val">${score}</span>
                <span class="lbl">Score</span>
              </div>
            `;
            historyEl.appendChild(item);
          });
        } else {
          historyEl.innerHTML = '<span style="color:var(--muted);font-size:0.9rem;">No interview history found.</span>';
        }
      }
    }
  } catch (e) {
    console.error(e);
  }
}

async function deleteUser(userId, userName) {
  if (!confirm(`Are you sure you want to permanently delete user "${userName}"? This action cannot be undone and will remove all their interview history.`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/users/${userId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    const data = await res.json();
    if (data.success) {
      loadUsers();
      updateDashboardStats();
    } else {
      alert('Error deleting user: ' + data.message);
    }
  } catch (e) {
    alert('Server error while deleting user.');
  }
}

function toggleView(view) {
  const listView = document.getElementById('userListView');
  const profileView = document.getElementById('userProfileView');

  if (view === 'list') {
    if (listView) listView.classList.remove('hidden');
    if (profileView) profileView.classList.add('hidden');
  } else {
    if (listView) listView.classList.add('hidden');
    if (profileView) profileView.classList.remove('hidden');
  }
}

// backToListBtn listener moved to initDOM

function showError(msg) {
  if (loginErrorMsg) loginErrorMsg.textContent = msg;
  if (loginError) loginError.classList.add('show');
}
function hideError() {
  if (loginError) loginError.classList.remove('show');
}

function setLoading(bool) {
  if (loginBtn) {
    loginBtn.disabled = bool;
    loginBtn.classList.toggle('loading', bool);
  }
}

/* ═══════════════════════════════════════════════════════════
   QUESTION BANK LOGIC
═══════════════════════════════════════════════════════════ */
let allQuestions = [];
let skillsList = [];

async function loadSkillsList() {
  try {
    const res = await fetch(`${API_BASE}/skills`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      skillsList = data.skills;
      allSkills = data.skills; // Keep in sync
      const filterSel = document.getElementById('filterSkill');
      const qSel = document.getElementById('qSkillSelect');

      if (filterSel) {
        let html = '<option value="">All Skills</option>';
        skillsList.forEach(s => html += `<option value="${s.id}">${s.skill_name}</option>`);
        filterSel.innerHTML = html;
      }

      if (qSel) {
        let qHtml = '<option value="">Select Skill...</option>';
        skillsList.forEach(s => qHtml += `<option value="${s.id}">${s.skill_name}</option>`);
        qSel.innerHTML = qHtml;
      }
    }
  } catch (e) { }
}

async function loadQuestions() {
  const tbody = document.getElementById('questionTableBody');
  const loader = document.getElementById('qTableLoading');
  if (tbody) tbody.innerHTML = '';
  if (loader) loader.classList.remove('hidden');

  const filterSkill = document.getElementById('filterSkill');
  const filterDiff = document.getElementById('filterDifficulty');
  const filterExp = document.getElementById('filterExp');

  const sId = filterSkill ? filterSkill.value : '';
  const diff = filterDiff ? filterDiff.value : '';
  const exp = filterExp ? filterExp.value : '';

  const params = new URLSearchParams();
  if (sId) params.append('skill_id', sId);
  if (diff) params.append('difficulty', diff);
  if (exp) params.append('experience_level', exp);

  try {
    const res = await fetch(`${API_BASE}/questions?${params.toString()}`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      allQuestions = data.questions;
      renderQuestionsTable(allQuestions);
    }
  } catch (e) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--red);">Error loading questions</td></tr>';
  } finally {
    if (loader) loader.classList.add('hidden');
  }
}

function renderQuestionsTable(list) {
  const tbody = document.getElementById('questionTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--muted);">No questions found.</td></tr>';
    return;
  }

  list.forEach(q => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><div style="max-width:450px; line-height:1.5;"><strong>${q.question}</strong></div></td>
      <td><span class="status-tag" style="background:var(--surface2); color:var(--text); font-weight:600;">${q.skill_name}</span></td>
      <td><span class="status-tag" style="text-transform:capitalize; background:rgba(0,0,0,0.03);">${q.experience_level}</span></td>
      <td>
        <span class="status-tag" style="
          background: ${q.difficulty === 'hard' ? 'rgba(239,68,68,0.1)' : (q.difficulty === 'medium' ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)')};
          color: ${q.difficulty === 'hard' ? 'var(--red)' : (q.difficulty === 'medium' ? '#92400e' : 'var(--accent)')};
          font-weight: 700; text-transform: capitalize;">
          ${q.difficulty}
        </span>
      </td>
      <td>
        <div style="display:flex; gap:12px;">
          <button class="btn-text" onclick="toggleQuestionPanel(${q.id})">Edit</button>
          <button class="btn-text red" onclick="deleteQuestion(${q.id})">Delete</button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// ── Action Panel Logic (Slide) ────────────────────────────────
// References moved to initDOM

function closeActionPanel() {
  if (actionPanel) actionPanel.classList.remove('show');
  setTimeout(() => {
    if (csvContent) csvContent.classList.add('hidden');
    if (qContent) qContent.classList.add('hidden');
  }, 500);
}

function toggleCsvPanel() {
  if (actionPanel && actionPanel.classList.contains('show') && csvContent && !csvContent.classList.contains('hidden')) {
    closeActionPanel();
  } else {
    // Switch to CSV mode
    if (qContent) qContent.classList.add('hidden');
    if (csvContent) csvContent.classList.remove('hidden');

    // Prepare CSV view
    const csvSel = document.getElementById('csvSkillSelect');
    if (csvSel) {
      let opts = '<option value="">-- Choose skill --</option>';
      skillsList.forEach(s => opts += `<option value="${s.id}">${s.skill_name}</option>`);
      csvSel.innerHTML = opts;
    }
    _csvFile = null;
    const csvFileName = document.getElementById('csvFileName');
    if (csvFileName) csvFileName.innerHTML = 'Click to browse or drag & drop <strong>.csv</strong>';
    
    const csvFileInp = document.getElementById('csvFileInput');
    if (csvFileInp) csvFileInp.value = '';
    
    const status = document.getElementById('csvUploadStatus');
    if (status) status.style.display = 'none';

    if (actionPanel) {
      actionPanel.classList.add('show');
      actionPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

function toggleQuestionPanel(qid = null) {
  if (!qid && actionPanel && actionPanel.classList.contains('show') && qContent && !qContent.classList.contains('hidden')) {
    closeActionPanel();
    return;
  }

  // Switch to Question mode
  if (csvContent) csvContent.classList.add('hidden');
  if (qContent) qContent.classList.remove('hidden');

  if (qForm) qForm.reset();
  const qIdInput = document.getElementById('qIdInput');
  const qPanelTitle = document.getElementById('qPanelTitle');
  if (qIdInput) qIdInput.value = qid || '';
  if (qPanelTitle) qPanelTitle.textContent = qid ? 'Edit Question' : 'Add New Question';

  if (qid) {
    const q = allQuestions.find(it => it.id === qid);
    if (q) {
      const skillSel = document.getElementById('qSkillSelect');
      const expSel = document.getElementById('qExpSelect');
      const diffSel = document.getElementById('qDiffSelect');
      const textInp = document.getElementById('qTextInput');
      const opt1 = document.getElementById('qOpt1');
      const opt2 = document.getElementById('qOpt2');
      const opt3 = document.getElementById('qOpt3');
      const opt4 = document.getElementById('qOpt4');
      
      if (skillSel) skillSel.value = q.skill_id;
      if (expSel) expSel.value = q.experience_level;
      if (diffSel) diffSel.value = q.difficulty;
      if (textInp) textInp.value = q.question;
      if (opt1) opt1.value = q.option1;
      if (opt2) opt2.value = q.option2;
      if (opt3) opt3.value = q.option3;
      if (opt4) opt4.value = q.option4;
      
      const correctChoice = document.querySelector(`input[name="correctChoice"][value="${q.correct}"]`);
      if (correctChoice) correctChoice.checked = true;
    }
  }

  if (actionPanel) {
    actionPanel.classList.add('show');
    actionPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Preserve old naming for edit buttons if any
window.openQuestionModal = toggleQuestionPanel;
window.openCsvModal = toggleCsvPanel;

async function handleQuestionSubmit(e) {
  e.preventDefault();
  const qid = document.getElementById('qIdInput').value;
  const data = {
    skill_id: document.getElementById('qSkillSelect').value,
    experience_level: document.getElementById('qExpSelect').value,
    difficulty: document.getElementById('qDiffSelect').value,
    question: document.getElementById('qTextInput').value,
    option1: document.getElementById('qOpt1').value,
    option2: document.getElementById('qOpt2').value,
    option3: document.getElementById('qOpt3').value,
    option4: document.getElementById('qOpt4').value,
    correct: document.querySelector('input[name="correctChoice"]:checked').value
  };

  const btn = document.getElementById('btnSaveQuestion');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Saving...';
  }

  try {
    const url = qid ? `${API_BASE}/questions/${qid}` : `${API_BASE}/questions`;
    const method = qid ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data)
    });
    const resData = await res.json();
    if (resData.success) {
      closeActionPanel();
      loadQuestions();
      updateDashboardStats();
    } else {
      alert('Error: ' + resData.message);
    }
  } catch (e) {
    alert('Server error saving question.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Save Question';
    }
  }
}

async function deleteQuestion(qid) {
  if (!confirm('Are you sure you want to delete this question?')) return;
  try {
    const res = await fetch(`${API_BASE}/questions/${qid}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    const data = await res.json();
    if (data.success) loadQuestions();
  } catch (e) { alert('Error deleting question'); }
}

// ── CSV Upload Logic ─────────────────────────────────────────
let _csvFile = null;

function onCsvFileChosen(event) {
  const file = event.target.files[0];
  if (!file) return;
  _csvFile = file;
  const nameEl = document.getElementById('csvFileName');
  if (nameEl) nameEl.innerHTML = `<i class="fas fa-check-circle" style="color:var(--accent);"></i> <strong>${file.name}</strong> — ready to import`;
  const dz = document.getElementById('csvDropZone');
  if (dz) {
    dz.style.borderColor = 'var(--accent)';
    dz.style.background = 'rgba(16,185,129,0.05)';
  }
}

async function doUploadCsv() {
  const skillIdEl = document.getElementById('csvSkillSelect');
  const skillId = skillIdEl ? skillIdEl.value : '';
  const statusEl = document.getElementById('csvUploadStatus');

  if (!skillId) {
    if (statusEl) {
      statusEl.style.display = 'block';
      statusEl.style.background = 'rgba(239,68,68,0.1)';
      statusEl.style.color = 'var(--red)';
      statusEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please select a skill first.';
    }
    return;
  }
  if (!_csvFile) {
    if (statusEl) {
      statusEl.style.display = 'block';
      statusEl.style.background = 'rgba(239,68,68,0.1)';
      statusEl.style.color = 'var(--red)';
      statusEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please choose a CSV file.';
    }
    return;
  }

  const btn = document.getElementById('btnUploadCsv');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Uploading...';
  }

  const formData = new FormData();
  formData.append('file', _csvFile);
  formData.append('skill_id', skillId);

  try {
    const res = await fetch(`${API_BASE}/questions/csv`, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
    const data = await res.json();
    if (statusEl) statusEl.style.display = 'block';
    if (data.success) {
      if (statusEl) {
        statusEl.style.background = 'rgba(16,185,129,0.1)';
        statusEl.style.color = 'var(--accent)';
        statusEl.innerHTML = `<i class="fas fa-check-circle"></i> ${data.message}`;
      }
      loadQuestions();
      updateDashboardStats();
      setTimeout(closeActionPanel, 2000);
    } else {
      if (statusEl) {
        statusEl.style.background = 'rgba(239,68,68,0.1)';
        statusEl.style.color = 'var(--red)';
        statusEl.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${data.message}`;
      }
    }
  } catch (e) {
    if (statusEl) {
      statusEl.style.display = 'block';
      statusEl.style.color = 'var(--red)';
      statusEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Server error.';
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-upload"></i> Import Questions';
    }
  }
}

/* ═══════════════════════════════════════════════════════════
   SKILLS & SYNONYMS LOGIC
═══════════════════════════════════════════════════════════ */
let allSkills = [];

async function loadSkillsTable() {
  const tbody = document.getElementById('skillsTableBody');
  const loader = document.getElementById('skillsLoading');
  if (tbody) tbody.innerHTML = '';
  if (loader) loader.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/skills`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      allSkills = data.skills;
      renderSkillsTable(allSkills);
    }
  } catch (e) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="4">Error loading skills</td></tr>';
  } finally {
    if (loader) loader.classList.add('hidden');
  }
}

function renderSkillsTable(list) {
  const tbody = document.getElementById('skillsTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:40px; color:var(--muted);">No skills found.</td></tr>';
    return;
  }

  list.forEach(s => {
    const row = document.createElement('tr');
    const synArray = s.synonyms ? s.synonyms.split(', ') : [];
    const synHtml = synArray.map(syn => `
      <div class="status-tag" style="background:#f3f4f6; color:var(--muted); font-size:0.75rem;">${syn}</div>
    `).join('');

    row.innerHTML = `
      <td><strong>${s.skill_name}</strong></td>
      <td><span class="status-tag" style="background:var(--surface2); color:var(--text); font-weight:600;">${s.category}</span></td>
      <td>
        <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
          ${synHtml}
          <button class="btn-icon" style="width:24px; height:24px; font-size:0.7rem;" onclick="toggleSynonymPanel(${s.id}, '${s.skill_name}')" title="Add Alias"><i class="fas fa-plus"></i></button>
        </div>
      </td>
      <td>
        <button class="btn-icon red" onclick="deleteSkill(${s.id})" title="Delete Skill"><i class="fas fa-trash"></i></button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function filterSkills() {
  const queryField = document.getElementById('skillSearch');
  if (!queryField) return;
  const query = queryField.value.toLowerCase();
  const filtered = allSkills.filter(s => s.skill_name.toLowerCase().includes(query));
  renderSkillsTable(filtered);
}

// References moved to initDOM

function closeSkillActionPanel() {
  if (skillActionPanel) skillActionPanel.classList.remove('show');
  setTimeout(() => {
    if (skillPanelContent) skillPanelContent.classList.add('hidden');
    if (synonymPanelContent) synonymPanelContent.classList.add('hidden');
  }, 500);
}

function toggleSkillPanel() {
  if (skillActionPanel && skillActionPanel.classList.contains('show') && skillPanelContent && !skillPanelContent.classList.contains('hidden')) {
    closeSkillActionPanel();
  } else {
    if (synonymPanelContent) synonymPanelContent.classList.add('hidden');
    if (skillPanelContent) skillPanelContent.classList.remove('hidden');
    if (skillForm) skillForm.reset();
    if (skillActionPanel) {
      skillActionPanel.classList.add('show');
      skillActionPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

function toggleSynonymPanel(id, name) {
  if (skillPanelContent) skillPanelContent.classList.add('hidden');
  if (synonymPanelContent) synonymPanelContent.classList.remove('hidden');
  if (synonymForm) synonymForm.reset();
  
  const idInp = document.getElementById('synBaseSkillId');
  const nameLabel = document.getElementById('synBaseSkillName');
  if (idInp) idInp.value = id;
  if (nameLabel) nameLabel.textContent = name;
  
  if (skillActionPanel) {
    skillActionPanel.classList.add('show');
    skillActionPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

window.showAddSkillModal = toggleSkillPanel;
window.showAddSynonymModal = toggleSynonymPanel;

async function handleSkillSubmit(e) {
  e.preventDefault();
  const synInput = document.getElementById('skillSynonymsInput').value;
  const synonyms = synInput ? synInput.split(',').map(s => s.trim()).filter(s => s !== '') : [];

  const payload = {
    skill_name: document.getElementById('skillNameInput').value,
    category: document.getElementById('skillCategoryInput').value,
    synonyms: synonyms
  };
  try {
    const res = await fetch(`${API_BASE}/skills`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      closeSkillActionPanel();
      loadSkillsTable();
      // Clear synonyms for next time
      const synField = document.getElementById('skillSynonymsInput');
      if (synField) synField.value = '';
    } else {
      alert(data.message);
    }
  } catch (e) { alert('Server error'); }
}

async function handleSynonymSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('synBaseSkillId').value;
  const payload = { synonym: document.getElementById('synonymInput').value };
  try {
    const res = await fetch(`${API_BASE}/skills/${id}/synonyms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      closeSkillActionPanel();
      loadSkillsTable();
    } else {
      alert(data.message);
    }
  } catch (e) { alert('Server error'); }
}

async function deleteSkill(id) {
  if (!confirm('Deleting a skill will also delete ALL related questions and synonyms. Continue?')) return;
  alert('Skill deletion is currently disabled via UI for safety. Use SQL for structural changes.');
}

/* ═══════════════════════════════════════════════════════════
   JOBS MANAGEMENT
═══════════════════════════════════════════════════════════ */
let allJobs = [];

function filterJobs() {
  const queryField = document.getElementById('jobSearch');
  if (!queryField) return;
  const query = queryField.value.toLowerCase();
  const filtered = allJobs.filter(j => j.title.toLowerCase().includes(query));
  renderJobTable(filtered);
}

async function loadJobs() {
  const tbody = document.getElementById('jobTableBody');
  const loader = document.getElementById('jobLoading');
  if (tbody) tbody.innerHTML = '';
  if (loader) loader.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/jobs`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      allJobs = data.jobs;
      renderJobTable(allJobs);
    }
  } catch (e) { console.error(e); }
  if (loader) loader.classList.add('hidden');
}

function renderJobTable(list) {
  const tbody = document.getElementById('jobTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:40px; color:var(--muted);">No job roles found.</td></tr>';
    return;
  }
  list.forEach(j => {
    const row = document.createElement('tr');
    const exp = `${j.min_experience}${j.max_experience ? ' - ' + j.max_experience : '+'} yrs`;
    const skills = j.skills.map(s => `<span class="status-tag" style="background:rgba(74, 222, 128, 0.08); color:var(--accent); font-size:0.72rem; border:1px solid rgba(74,222,128,0.2);">${s.skill_name} (${s.required_level})</span>`).join(' ');

    row.innerHTML = `
      <td><strong>${j.title}</strong></td>
      <td><span class="status-tag" style="background:rgba(0,0,0,0.03);">${exp}</span></td>
      <td><div style="display:flex; flex-wrap:wrap; gap:6px;">${skills || '<span style="color:var(--muted); font-size:0.8rem;">No requirements</span>'}</div></td>
      <td>
        <div style="display:flex; gap:12px;">
          <button class="btn-text" onclick="toggleJobPanel(${j.id})">Edit</button>
          <button class="btn-text red" onclick="deleteJob(${j.id})">Delete</button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// Reference moved to initDOM

function closeJobActionPanel() {
  if (jobActionPanel) jobActionPanel.classList.remove('show');
}

async function toggleJobPanel(jid = null) {
  if (!jid && jobActionPanel && jobActionPanel.classList.contains('show')) {
    closeJobActionPanel();
  } else {
    const jobForm = document.getElementById('jobForm');
    const skillsContainer = document.getElementById('jobSkillsContainer');
    const panelTitle = document.getElementById('jobPanelTitle');
    
    if (jobForm) jobForm.reset();
    if (skillsContainer) skillsContainer.innerHTML = '';
    if (panelTitle) panelTitle.textContent = jid ? 'Edit Job Role' : 'Add New Job Role';

    if (jid) {
      const job = allJobs.find(it => it.id === jid);
      if (job) {
        const titleInp = document.getElementById('jobTitleInp');
        const minExp = document.getElementById('jobMinExpInp');
        const maxExp = document.getElementById('jobMaxExpInp');
        
        if (titleInp) titleInp.value = job.title;
        if (minExp) minExp.value = job.min_experience;
        if (maxExp) maxExp.value = job.max_experience || '';
        
        for (const s of job.skills) {
          await addSkillToJob(s.skill_id, s.required_level);
        }
      }
    } else {
      await addSkillToJob(); // add first empty row for new job
    }

    if (jobActionPanel) {
      jobActionPanel.classList.add('show');
      jobActionPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

async function addSkillToJob(skill_id = '', level = 'mid') {
  // Ensure skills are loaded for the dropdowns
  if (skillsList.length === 0) await loadSkillsList();

  const container = document.getElementById('jobSkillsContainer');
  if (!container) return;
  const row = document.createElement('div');
  row.style = "display:grid; grid-template-columns: 2fr 1fr 40px; gap:10px; margin-bottom:8px; align-items:center;";

  // Use skillsList consistently
  let skillOptions = skillsList.map(s => `<option value="${s.id}" ${s.id == skill_id ? 'selected' : ''}>${s.skill_name}</option>`).join('');

  row.innerHTML = `
    <select class="job-skill-select" required>
      <option value="">Select Skill...</option>
      ${skillOptions}
    </select>
    <select class="job-level-select" required>
      <option value="fresher" ${level === 'fresher' ? 'selected' : ''}>Fresher</option>
      <option value="junior" ${level === 'junior' ? 'selected' : ''}>Junior</option>
      <option value="mid" ${level === 'mid' ? 'selected' : ''}>Mid-Level</option>
      <option value="senior" ${level === 'senior' ? 'selected' : ''}>Senior</option>
    </select>
    <button type="button" class="btn-icon" onclick="this.parentElement.remove()" style="color:var(--red); border-color:transparent; background:transparent;"><i class="fas fa-times"></i></button>
  `;
  container.appendChild(row);
}

async function handleJobSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById('btnSaveJob');
  if (btn) btn.disabled = true;

  const skills = [];
  document.querySelectorAll('#jobSkillsContainer > div').forEach(div => {
    const sidEl = div.querySelector('.job-skill-select');
    const lvlEl = div.querySelector('.job-level-select');
    if (sidEl && lvlEl) {
      const sid = sidEl.value;
      const lvl = lvlEl.value;
      if (sid) skills.push({ skill_id: parseInt(sid), level: lvl });
    }
  });

  const payload = {
    title: document.getElementById('jobTitleInp').value,
    min_experience: parseInt(document.getElementById('jobMinExpInp').value),
    max_experience: document.getElementById('jobMaxExpInp').value ? parseInt(document.getElementById('jobMaxExpInp').value) : null,
    skills: skills
  };

  try {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'include'
    });
    const data = await res.json();
    if (data.success) {
      closeJobActionPanel();
      loadJobs();
    }
  } catch (e) { alert('Error saving job role'); }
  if (btn) btn.disabled = false;
}

async function deleteJob(id) {
  if (!confirm('Are you sure? This will remove this job role from recommendations.')) return;
  try {
    await fetch(`${API_BASE}/jobs/${id}`, { method: 'DELETE', credentials: 'include' });
    loadJobs();
  } catch (e) { }
}

/* ═══════════════════════════════════════════════════════════
   ANALYTICS & CHARTS
═══════════════════════════════════════════════════════════ */
async function loadAnalytics() {
  const skillContainer = document.getElementById('skillPopularityChart');
  const categoryContainer = document.getElementById('categoryPerformanceChart');

  if (skillContainer) skillContainer.innerHTML = '<p style="text-align:center; padding:20px; color:var(--muted);">Loading analytics data...</p>';
  if (categoryContainer) categoryContainer.innerHTML = '';

  try {
    const res = await fetch(`${API_BASE}/analytics`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      if (skillContainer) renderBarChart(skillContainer, data.skillPopularity, 'skill_name', 'user_count', 'Users');
      if (categoryContainer) renderBarChart(categoryContainer, data.categoryPerformance, 'category', 'avg_score', 'Avg Score', true);
    }
  } catch (e) { console.error(e); }
}

function renderBarChart(container, data, labelKey, valueKey, suffix, isPercentage = false) {
  if (!container) return;
  container.innerHTML = '';
  if (!data || data.length === 0) {
    container.innerHTML = '<p style="color:var(--muted); font-size:0.85rem;">No data available yet.</p>';
    return;
  }

  const maxVal = Math.max(...data.map(d => d[valueKey]));

  data.forEach(item => {
    const val = item[valueKey];
    const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
    const displayVal = isPercentage ? (val * 100).toFixed(0) + '%' : val + ' ' + suffix;

    const row = document.createElement('div');
    row.className = 'chart-row';
    row.style = "margin-bottom: 16px;";
    row.innerHTML = `
      <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:6px;">
        <span style="font-weight:600;">${item[labelKey]}</span>
        <span style="color:var(--muted);">${displayVal}</span>
      </div>
      <div style="width:100%; height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden;">
        <div style="width:0; height:100%; background:var(--accent); border-radius:4px; transition: width 1s ease-out;" data-pct="${pct}"></div>
      </div>
    `;
    container.appendChild(row);

    // Trigger animation
    setTimeout(() => {
      const fill = row.querySelector('div > div');
      if (fill) fill.style.width = pct + '%';
    }, 100);
  });
}

async function checkSession() {
  try {
    const response = await fetch(`${API_BASE}/me`, {
      credentials: 'include'
    });
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.admin) {
        localStorage.setItem('admin_session_active', 'true');
        showDashboard(data.admin);
        return;
      }
    }
  } catch (_) { /* network error */ }

  localStorage.removeItem('admin_session_active');
  localStorage.removeItem('admin_username');
  showLoginScreen();
}

/* ═══════════════════════════════════════════════════════════
   LOGIN & LOGOUT HANDLERS
═══════════════════════════════════════════════════════════ */
async function handleLogin(e) {
  e.preventDefault();
  hideError();

  const username = adminUsernameInp.value.trim();
  const password = adminPasswordInp.value;

  if (!username || !password) {
    showError('Please enter both username and password.');
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (data.success) {
      if (adminPasswordInp) adminPasswordInp.value = '';
      localStorage.setItem('admin_session_active', 'true');
      showDashboard(data.admin);
    } else {
      showError(data.message || 'Invalid credentials. Please try again.');
    }
  } catch (err) {
    showError('Network error. Make sure the server is running.');
  } finally {
    setLoading(false);
  }
}

async function handleLogout() {
  confirmLogout.disabled = true;
  confirmLogout.textContent = 'Signing out…';

  try {
    await fetch(`${API_BASE}/logout`, {
      method: 'POST',
      credentials: 'include'
    });
  } catch (_) { /* proceed regardless */ }

  if (logoutOverlay) logoutOverlay.classList.remove('show');
  confirmLogout.disabled = false;
  confirmLogout.textContent = 'Yes, Sign Out';
  localStorage.removeItem('admin_session_active');
  if (adminUsernameInp) adminUsernameInp.value = '';
  if (adminPasswordInp) adminPasswordInp.value = '';
  showLoginScreen();
}

/* ═══════════════════════════════════════════════════════════
   SITE SETTINGS (GENERAL)
═══════════════════════════════════════════════════════════ */

async function loadGeneralSettings() {
  try {
    const res = await fetch(`${API_BASE}/settings`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      const s = data.settings;
      if (document.getElementById('set_siteName')) document.getElementById('set_siteName').value = s.site_name || '';
      if (document.getElementById('set_siteTagline')) document.getElementById('set_siteTagline').value = s.site_tagline || '';
    }
  } catch (e) { console.error('Error loading settings:', e); }
}

async function saveGeneralSettings() {
  const btn = document.getElementById('btnSaveSettings');
  const status = document.getElementById('settingsStatus');
  
  if (btn) btn.disabled = true;
  if (status) status.style.display = 'none';

  const payload = {
    site_name: document.getElementById('set_siteName').value,
    site_tagline: document.getElementById('set_siteTagline').value
  };

  try {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (status) {
      status.style.display = 'block';
      status.style.background = data.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)';
      status.style.color = data.success ? 'var(--accent)' : 'var(--red)';
      status.innerHTML = data.success ? '<i class="fas fa-check-circle"></i> Settings updated successfully.' : `<i class="fas fa-exclamation-circle"></i> ${data.message || 'Update failed.'}`;
    }
    if (data.success) {
      // Re-apply branding if site name changed
      applyBranding();
    }
  } catch (e) {
    if (status) {
      status.style.display = 'block';
      status.style.color = 'var(--red)';
      status.innerHTML = 'Server error.';
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

/* ═══════════════════════════════════════════════════════════
   ADMIN ACCOUNT MANAGEMENT
   ═══════════════════════════════════════════════════════════ */

async function saveAdminAccount() {
  const btn = document.getElementById('btnSaveAccount');
  const status = document.getElementById('accountStatus');
  const name = document.getElementById('acc_fullName').value;
  const pw = document.getElementById('acc_newPassword').value;
  const confirmPw = document.getElementById('acc_confirmPassword').value;

  if (pw && pw !== confirmPw) {
    status.style.display = 'block';
    status.style.background = 'rgba(239,68,68,0.1)';
    status.style.color = 'var(--red)';
    status.innerHTML = '<i class="fas fa-exclamation-circle"></i> Passwords do not match.';
    return;
  }

  if (btn) btn.disabled = true;
  
  try {
    const res = await fetch(`${API_BASE}/me`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ fullName: name, password: pw })
    });
    const data = await res.json();
    
    status.style.display = 'block';
    status.style.background = data.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)';
    status.style.color = data.success ? 'var(--accent)' : 'var(--red)';
    status.innerHTML = data.success ? '<i class="fas fa-check-circle"></i> Profile updated successfully.' : `<i class="fas fa-exclamation-circle"></i> ${data.message}`;
    
    if (data.success) {
      // Update sidebar display
      const topName = document.getElementById('topbarName');
      const topAvatar = document.getElementById('topbarAvatar');
      if (topName) topName.textContent = name;
      if (topAvatar) topAvatar.textContent = name.charAt(0).toUpperCase();
      localStorage.setItem('admin_username', name);
      
      // Clear password fields
      document.getElementById('acc_newPassword').value = '';
      document.getElementById('acc_confirmPassword').value = '';
    }
  } catch (e) {
    status.style.display = 'block';
    status.style.color = 'var(--red)';
    status.innerHTML = 'Server error.';
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function applyBranding() {
  try {
    // We use the public endpoint to get the configuration
    const res = await fetch(`${API_BASE}/settings/public`);
    const data = await res.json();
    if (data.success && data.settings) {
      const s = data.settings;
      const siteName = s.site_name || 'Interview Me';
      
      // Update all brand name elements
      const els = ['loginBrandName', 'sidebarBrandName'];
      els.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          // Preserve the <em> part if possible, or just replace text
          // "Interview Me" -> "Interview <em>Me</em>"
          if (siteName === 'Interview Me') {
             el.innerHTML = 'Interview <em>Me</em>';
          } else {
             el.textContent = siteName;
          }
        }
      });
      
      // Also update page title
      document.title = `Admin Portal – ${siteName}`;
    }
  } catch (e) { console.error("Branding failed:", e); }
}

// Populate account fields when switching to settings
// Update switchSection to handle this
const originalSwitchSection = switchSection;
switchSection = function(id) {
  originalSwitchSection(id);
  if (id === 'settings') {
    // Fill account info
    const name = localStorage.getItem('admin_username');
    if (document.getElementById('acc_fullName')) document.getElementById('acc_fullName').value = name || '';
    
    // We might want to fetch username too, but for now we know it's in session
    // Let's assume we can get it from /me if needed
    fetchAdminInfoForAccount();
  }
};

async function fetchAdminInfoForAccount() {
  try {
    const res = await fetch(`${API_BASE}/me`, { credentials: 'include' });
    const data = await res.json();
    if (data.success) {
      const u = data.admin;
      if (document.getElementById('acc_fullName')) document.getElementById('acc_fullName').value = u.fullName;
      if (document.getElementById('acc_username')) document.getElementById('acc_username').value = u.username;
    }
  } catch (e) {}
}
