/**
 * Student Result Management System - Frontend App Logic
 */

// Application State
const state = {
  token: localStorage.getItem('token') || null,
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  semesters: [],
  currentSemester: 'SEM-2025-SPRING',
  gradeScale: []
};

// Toast Notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3500);
}

// API Fetch Helper with Bearer Token
async function apiRequest(endpoint, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  if (!options.isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  
  try {
    const response = await fetch(endpoint, {
      ...options,
      headers
    });
    
    if (response.status === 401) {
      // Token expired or invalid
      logout();
      throw new Error("Session expired. Please log in again.");
    }
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.error || "An error occurred");
    }
    return data;
  } catch (err) {
    throw err;
  }
}

// ==========================================
// AUTHENTICATION (EMULATOR / FIREBASE)
// ==========================================

async function login(email, password) {
  try {
    // In emulator or Firebase Auth REST API, authenticate via Identity Toolkit endpoint
    const apiKey = "fake-api-key"; // Emulator does not validate real keys
    const authUrl = `http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${apiKey}`;
    
    const resp = await fetch(authUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        returnSecureToken: true
      })
    });
    
    const authData = await resp.json();
    if (!resp.ok) {
      throw new Error(authData.error?.message || "Invalid email or password");
    }
    
    state.token = authData.idToken;
    localStorage.setItem('token', state.token);
    
    // Fetch user profile from backend
    const meData = await apiRequest('/api/auth/me');
    state.user = meData.user;
    localStorage.setItem('user', JSON.stringify(state.user));
    
    showToast(`Welcome back, ${state.user.name}!`);
    renderApp();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  renderApp();
}

// ==========================================
// RENDER VIEWS
// ==========================================

function renderApp() {
  const root = document.getElementById('app-root');
  if (!root) return;
  
  if (!state.token || !state.user) {
    root.innerHTML = renderLoginView();
    attachLoginEvents();
    return;
  }
  
  root.innerHTML = `
    <nav class="navbar">
      <div class="brand">
        <div class="brand-icon">🎓</div>
        <span>ResultPortal</span>
      </div>
      <div class="user-profile-badge">
        <div>
          <span style="font-weight: 600;">${state.user.name}</span>
          <span class="role-badge ${state.user.role}">${state.user.role}</span>
        </div>
        <button id="logout-btn" class="btn btn-secondary btn-sm">Log Out</button>
      </div>
    </nav>
    <div id="role-dashboard"></div>
  `;
  
  document.getElementById('logout-btn').addEventListener('click', logout);
  
  if (state.user.role === 'admin') {
    renderAdminDashboard();
  } else if (state.user.role === 'teacher') {
    renderTeacherDashboard();
  } else if (state.user.role === 'student') {
    renderStudentDashboard();
  }
}

function renderLoginView() {
  return `
    <div style="min-height: 80vh; display: flex; align-items: center; justify-content: center;">
      <div class="card" style="width: 100%; max-width: 420px; padding: 2.25rem;">
        <div style="text-align: center; margin-bottom: 2rem;">
          <div class="brand-icon" style="margin: 0 auto 1.25rem; width: 3.25rem; height: 3.25rem; font-size: 1.6rem; border-radius: var(--radius-md);">🎓</div>
          <h1 style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em;">Student Result Portal</h1>
          <p style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.35rem;">Academic Grading & Records System</p>
        </div>
        <form id="login-form">
          <div class="form-group">
            <label for="login-email">Institutional Email</label>
            <input type="email" id="login-email" required placeholder="e.g. admin@university.edu" />
          </div>
          <div class="form-group">
            <label for="login-password">Password</label>
            <input type="password" id="login-password" required placeholder="Enter password" />
          </div>
          <button type="submit" id="btn-login-submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem; padding: 0.7rem;">Sign In</button>
        </form>
        
        <div style="margin-top: 1.75rem; padding-top: 1.25rem; border-top: 1px solid var(--border-subtle); font-size: 0.775rem; color: var(--text-muted); line-height: 1.6;">
          <div style="font-weight: 600; color: var(--text-secondary); margin-bottom: 0.35rem;">Demo Credentials:</div>
          • <b>Admin:</b> <code>admin@university.edu</code> (<code>AdminPassword123!</code>)<br/>
          • <b>Teacher:</b> <code>dr.smith@university.edu</code> (<code>TeacherPassword123!</code>)<br/>
          • <b>Student:</b> <code>alice@student.university.edu</code> (<code>StudentPassword123!</code>)
        </div>
      </div>
    </div>
  `;
}

function attachLoginEvents() {
  const form = document.getElementById('login-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('login-email').value;
      const pass = document.getElementById('login-password').value;
      await login(email, pass);
    });
  }
}

// ==========================================
// ADMIN DASHBOARD
// ==========================================

async function renderAdminDashboard() {
  const container = document.getElementById('role-dashboard');
  container.innerHTML = `
    <div class="tab-nav">
      <button class="tab-btn active" onclick="switchAdminTab('users')">Manage Users</button>
      <button class="tab-btn" onclick="switchAdminTab('courses')">Courses & Assignments</button>
      <button class="tab-btn" onclick="switchAdminTab('semesters')">Semesters</button>
      <button class="tab-btn" onclick="switchAdminTab('audit')">Audit Logs</button>
    </div>
    <div id="admin-tab-content"></div>
  `;
  await switchAdminTab('users');
}

window.switchAdminTab = async function(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  event?.target?.classList.add('active');
  
  const content = document.getElementById('admin-tab-content');
  if (tab === 'users') {
    content.innerHTML = `<div class="card"><div class="card-title"><h3>User Management</h3> <button class="btn btn-primary btn-sm" onclick="openAddUserModal()">+ Add User</button></div><div id="admin-users-list">Loading...</div></div>`;
    loadAdminUsers();
  } else if (tab === 'courses') {
    content.innerHTML = `<div class="card"><div class="card-title"><h3>Course Offerings & Teacher Assignments</h3> <button class="btn btn-primary btn-sm" onclick="openAddCourseModal()">+ Add Course</button></div><div id="admin-courses-list">Loading...</div></div>`;
    loadAdminCourses();
  } else if (tab === 'semesters') {
    content.innerHTML = `<div class="card"><div class="card-title"><h3>Semesters</h3> <button class="btn btn-primary btn-sm" onclick="openAddSemesterModal()">+ Add Semester</button></div><div id="admin-semesters-list">Loading...</div></div>`;
    loadAdminSemesters();
  } else if (tab === 'audit') {
    content.innerHTML = `<div class="card"><div class="card-title"><h3>Marks Modification Audit Trail</h3></div><div id="admin-audit-list">Loading...</div></div>`;
    loadAdminAuditLogs();
  }
};

async function loadAdminUsers() {
  try {
    const data = await apiRequest('/api/admin/users');
    const listEl = document.getElementById('admin-users-list');
    let rows = data.users.map(u => `
      <tr>
        <td><b>${u.name}</b></td>
        <td>${u.email}</td>
        <td><span class="role-badge ${u.role}">${u.role}</span></td>
        <td>${u.student_id || '-'}</td>
        <td><span class="status-badge ${u.is_active ? 'pass' : 'fail'}">${u.is_active ? 'Active' : 'Deactivated'}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleUserActive('${u.uid}', ${!u.is_active})">
            ${u.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </td>
      </tr>
    `).join('');
    
    listEl.innerHTML = `
      <div class="table-responsive">
        <table>
          <thead>
            <tr><th>Name</th><th>Email</th><th>Role</th><th>Student ID</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

window.toggleUserActive = async function(uid, is_active) {
  try {
    await apiRequest(`/api/admin/users/${uid}`, {
      method: 'PUT',
      body: JSON.stringify({ is_active })
    });
    showToast(`User ${is_active ? 'activated' : 'deactivated'} successfully`);
    loadAdminUsers();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

async function loadAdminCourses() {
  try {
    const [coursesData, usersData] = await Promise.all([
      apiRequest('/api/admin/courses'),
      apiRequest('/api/admin/users?role=teacher')
    ]);
    
    const teachersMap = {};
    usersData.users.forEach(t => teachersMap[t.uid] = t.name);
    
    const listEl = document.getElementById('admin-courses-list');
    let rows = coursesData.courses.map(c => {
      const assignedTeachers = (c.teacher_uids || []).map(uid => teachersMap[uid] || uid).join(', ') || '<em>None</em>';
      return `
        <tr>
          <td><b>${c.code}</b></td>
          <td>${c.title}</td>
          <td>${c.credits}</td>
          <td>${c.semester_id}</td>
          <td>${assignedTeachers}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="openAssignTeacherModal('${c.id}', '${escape(JSON.stringify(c.teacher_uids || []))}')">Assign Teacher</button>
          </td>
        </tr>
      `;
    }).join('');
    
    listEl.innerHTML = `
      <div class="table-responsive">
        <table>
          <thead><tr><th>Code</th><th>Title</th><th>Credits</th><th>Semester</th><th>Assigned Faculty</th><th>Action</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminSemesters() {
  try {
    const data = await apiRequest('/api/admin/semesters');
    const listEl = document.getElementById('admin-semesters-list');
    let rows = data.semesters.map(s => `
      <tr>
        <td><b>${s.id}</b></td>
        <td>${s.name}</td>
        <td>${s.academic_year}</td>
        <td><span class="status-badge pass">Active</span></td>
      </tr>
    `).join('');
    listEl.innerHTML = `
      <div class="table-responsive">
        <table>
          <thead><tr><th>ID</th><th>Semester Name</th><th>Academic Year</th><th>Status</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminAuditLogs() {
  try {
    const data = await apiRequest('/api/admin/audit-logs');
    const listEl = document.getElementById('admin-audit-list');
    let rows = data.audit_logs.map(log => {
      const oldScore = log.old_value ? log.old_value.score : 'None';
      const newScore = log.new_value ? log.new_value.score : 'None';
      const dateStr = new Date(log.timestamp).toLocaleString();
      return `
        <tr>
          <td><small>${dateStr}</small></td>
          <td>${log.actor_email} <span class="role-badge ${log.actor_role}">${log.actor_role}</span></td>
          <td><code>${log.action}</code></td>
          <td>${log.course_id}</td>
          <td>${log.student_uid}</td>
          <td>${oldScore} &rarr; <b>${newScore}</b></td>
        </tr>
      `;
    }).join('');
    
    listEl.innerHTML = `
      <div class="table-responsive">
        <table>
          <thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Course</th><th>Student UID</th><th>Score Change</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Modal implementations for Admin
window.openAddUserModal = function() {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.id = 'active-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h2 style="margin-bottom: 1.25rem;">Create New User</h2>
      <form id="add-user-form">
        <div class="form-group">
          <label>Full Name</label>
          <input type="text" id="user-name" required placeholder="e.g. John Doe" />
        </div>
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" id="user-email" required placeholder="e.g. john@university.edu" />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" id="user-pass" required value="Password@123" />
        </div>
        <div class="form-group">
          <label>Role</label>
          <select id="user-role">
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div class="form-group" id="student-id-grp">
          <label>Student ID / Roll Number</label>
          <input type="text" id="user-student-id" placeholder="e.g. STU2025010" />
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Create User</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  
  document.getElementById('add-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify({
          name: document.getElementById('user-name').value,
          email: document.getElementById('user-email').value,
          password: document.getElementById('user-pass').value,
          role: document.getElementById('user-role').value,
          student_id: document.getElementById('user-student-id').value
        })
      });
      showToast('User created successfully');
      closeModal();
      loadAdminUsers();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
};

window.openAddCourseModal = function() {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.id = 'active-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h2 style="margin-bottom: 1.25rem;">Create New Course</h2>
      <form id="add-course-form">
        <div class="form-group">
          <label>Course Code</label>
          <input type="text" id="course-code" required placeholder="e.g. CS201" />
        </div>
        <div class="form-group">
          <label>Course Title</label>
          <input type="text" id="course-title" required placeholder="e.g. Operating Systems" />
        </div>
        <div class="form-group">
          <label>Credits</label>
          <input type="number" step="0.5" id="course-credits" value="4.0" required />
        </div>
        <div class="form-group">
          <label>Semester</label>
          <select id="course-sem">
            <option value="SEM-2025-SPRING">Spring 2025</option>
            <option value="SEM-2024-FALL">Fall 2024</option>
          </select>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Course</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  
  document.getElementById('add-course-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const code = document.getElementById('course-code').value.toUpperCase();
      await apiRequest('/api/admin/courses', {
        method: 'POST',
        body: JSON.stringify({
          id: code,
          code: code,
          title: document.getElementById('course-title').value,
          credits: parseFloat(document.getElementById('course-credits').value),
          semester_id: document.getElementById('course-sem').value
        })
      });
      showToast('Course created successfully');
      closeModal();
      loadAdminCourses();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
};

window.openAddSemesterModal = function() {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.id = 'active-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h2 style="margin-bottom: 1.25rem;">Create New Semester</h2>
      <form id="add-sem-form">
        <div class="form-group">
          <label>Semester ID</label>
          <input type="text" id="sem-id" required placeholder="e.g. SEM-2025-FALL" />
        </div>
        <div class="form-group">
          <label>Semester Name</label>
          <input type="text" id="sem-name" required placeholder="e.g. Fall 2025" />
        </div>
        <div class="form-group">
          <label>Academic Year</label>
          <input type="text" id="sem-year" required placeholder="e.g. 2025-2026" />
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Semester</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  
  document.getElementById('add-sem-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/admin/semesters', {
        method: 'POST',
        body: JSON.stringify({
          id: document.getElementById('sem-id').value,
          name: document.getElementById('sem-name').value,
          academic_year: document.getElementById('sem-year').value
        })
      });
      showToast('Semester created successfully');
      closeModal();
      loadAdminSemesters();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
};

window.openAssignTeacherModal = async function(courseId, existingTeachersJson) {
  const existingTeachers = JSON.parse(unescape(existingTeachersJson));
  const teachersData = await apiRequest('/api/admin/users?role=teacher');
  
  const checkboxes = teachersData.users.map(t => `
    <label style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; cursor: pointer;">
      <input type="checkbox" value="${t.uid}" ${existingTeachers.includes(t.uid) ? 'checked' : ''} style="width: auto;" />
      <span>${t.name} (${t.email})</span>
    </label>
  `).join('');
  
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.id = 'active-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h2 style="margin-bottom: 1.25rem;">Assign Teachers: ${courseId}</h2>
      <div style="max-height: 250px; overflow-y: auto; margin-bottom: 1.5rem;">
        ${checkboxes}
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="button" class="btn btn-primary" id="btn-save-assign">Save Assignments</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  
  document.getElementById('btn-save-assign').addEventListener('click', async () => {
    const selected = Array.from(modal.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
    try {
      await apiRequest(`/api/admin/courses/${courseId}/assign-teacher`, {
        method: 'PUT',
        body: JSON.stringify({ teacher_uids: selected })
      });
      showToast('Teacher assignments updated');
      closeModal();
      loadAdminCourses();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
};

window.closeModal = function() {
  const modal = document.getElementById('active-modal');
  if (modal) modal.remove();
};

// ==========================================
// TEACHER DASHBOARD
// ==========================================

async function renderTeacherDashboard() {
  const container = document.getElementById('role-dashboard');
  container.innerHTML = `
    <div class="card">
      <div class="card-title">
        <h3>Assigned Courses & Marks Management</h3>
        <div style="display: flex; gap: 0.75rem;">
          <select id="teacher-sem-select" style="width: auto; padding: 0.4rem 0.8rem;">
            <option value="SEM-2025-SPRING">Spring 2025</option>
            <option value="SEM-2024-FALL">Fall 2024</option>
          </select>
        </div>
      </div>
      <div id="teacher-courses-grid" class="stat-grid">Loading...</div>
    </div>
    <div id="teacher-course-details"></div>
  `;
  
  loadTeacherCourses();
}

async function loadTeacherCourses() {
  try {
    const data = await apiRequest('/api/teacher/courses');
    const container = document.getElementById('teacher-courses-grid');
    if (!data.courses || data.courses.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted);">No courses currently assigned to you.</p>`;
      return;
    }
    
    container.innerHTML = data.courses.map(c => `
      <div class="stat-box" style="cursor: pointer;" onclick="selectTeacherCourse('${c.id}', '${c.code}', '${c.title}')">
        <div class="stat-label">${c.code} (${c.credits} Credits)</div>
        <div style="font-size: 1.1rem; font-weight: 700; margin: 0.35rem 0;">${c.title}</div>
        <button class="btn btn-secondary btn-sm" style="margin-top: 0.5rem; width: 100%;">Manage Marks & Stats</button>
      </div>
    `).join('');
    
    // Select first course by default
    if (data.courses.length > 0) {
      selectTeacherCourse(data.courses[0].id, data.courses[0].code, data.courses[0].title);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

window.selectTeacherCourse = async function(courseId, code, title) {
  const detailsEl = document.getElementById('teacher-course-details');
  const semId = document.getElementById('teacher-sem-select')?.value || 'SEM-2025-SPRING';
  
  detailsEl.innerHTML = `
    <div class="card">
      <div class="card-title">
        <div>
          <h3>${code}: ${title}</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.2rem;">Semester: ${semId}</p>
        </div>
        <div style="display: flex; gap: 0.75rem;">
          <button class="btn btn-secondary btn-sm" onclick="openBulkUploadModal('${courseId}', '${semId}')">📤 Bulk Upload CSV</button>
          <button class="btn btn-primary btn-sm" onclick="openSingleMarkModal('${courseId}', '${semId}')">+ Enter Mark</button>
        </div>
      </div>
      
      <!-- Class Stats Summary -->
      <div id="teacher-course-stats" class="stat-grid"></div>
      
      <div id="teacher-course-marks-table">Loading marks...</div>
    </div>
  `;
  
  loadCourseMarksAndStats(courseId, semId);
};

async function loadCourseMarksAndStats(courseId, semId) {
  try {
    const [marksData, statsData] = await Promise.all([
      apiRequest(`/api/teacher/courses/${courseId}/marks?semester_id=${semId}`),
      apiRequest(`/api/reports/class-summary?course_id=${courseId}&semester_id=${semId}`)
    ]);
    
    // Render Stats
    const stats = statsData.statistics;
    const statsEl = document.getElementById('teacher-course-stats');
    if (statsEl) {
      statsEl.innerHTML = `
        <div class="stat-box">
          <div class="stat-label">Students Graded</div>
          <div class="stat-value">${stats.count}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Class Average</div>
          <div class="stat-value">${stats.average}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Highest / Lowest</div>
          <div class="stat-value" style="font-size: 1.3rem;">${stats.highest} / ${stats.lowest}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Pass Percentage</div>
          <div class="stat-value" style="color: ${stats.pass_percentage >= 75 ? 'var(--success)' : 'var(--warning)'};">${stats.pass_percentage}%</div>
        </div>
      `;
    }
    
    // Render Marks Table
    const tableEl = document.getElementById('teacher-course-marks-table');
    if (tableEl) {
      if (marksData.marks.length === 0) {
        tableEl.innerHTML = `<p style="color: var(--text-muted);">No marks recorded yet for this course & semester.</p>`;
        return;
      }
      
      let rows = marksData.marks.map(m => `
        <tr>
          <td><b>${m.student_id}</b></td>
          <td>${m.student_name}</td>
          <td><b>${m.score}</b> / ${m.max_marks}</td>
          <td><b>${m.grade}</b></td>
          <td>${m.grade_points}</td>
          <td><span class="status-badge ${m.is_pass ? 'pass' : 'fail'}">${m.is_pass ? 'PASS' : 'FAIL'}</span></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="editStudentMark('${courseId}', '${semId}', '${m.student_uid}', '${m.student_name}', ${m.score})">Edit</button>
          </td>
        </tr>
      `).join('');
      
      tableEl.innerHTML = `
        <div class="table-responsive">
          <table>
            <thead><tr><th>Student ID</th><th>Student Name</th><th>Score</th><th>Grade</th><th>Grade Points</th><th>Result</th><th>Action</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

window.openSingleMarkModal = async function(courseId, semId) {
  try {
    const studentsData = await apiRequest('/api/teacher/students');
    if (!studentsData.students || studentsData.students.length === 0) {
      showToast('No active students found in system', 'error');
      return;
    }
    
    const studentOptions = studentsData.students.map(s => `
      <option value="${s.uid}">${s.student_id || s.uid} - ${s.name} (${s.email})</option>
    `).join('');
  
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.id = 'active-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h2 style="margin-bottom: 1.25rem;">Enter / Update Mark</h2>
      <form id="single-mark-form">
        <div class="form-group">
          <label>Select Student</label>
          <select id="mark-student-uid" required>${studentOptions}</select>
        </div>
        <div class="form-group">
          <label>Score (0 - 100)</label>
          <input type="number" step="0.1" min="0" max="100" id="mark-score" required placeholder="e.g. 85.5" />
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Marks</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  
  document.getElementById('single-mark-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/teacher/marks', {
        method: 'POST',
        body: JSON.stringify({
          course_id: courseId,
          semester_id: semId,
          student_uid: document.getElementById('mark-student-uid').value,
          score: parseFloat(document.getElementById('mark-score').value)
        })
      });
      showToast('Mark saved and audit logged');
      closeModal();
      loadCourseMarksAndStats(courseId, semId);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
  } catch (outerErr) {
    showToast(outerErr.message, 'error');
  }
};

window.editStudentMark = function(courseId, semId, studentUid, studentName, currentScore) {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.id = 'active-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h2 style="margin-bottom: 1.25rem;">Edit Mark: ${studentName}</h2>
      <form id="edit-mark-form">
        <div class="form-group">
          <label>New Score (0 - 100)</label>
          <input type="number" step="0.1" min="0" max="100" id="edit-score" value="${currentScore}" required />
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Update & Audit</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  
  document.getElementById('edit-mark-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/api/teacher/marks', {
        method: 'POST',
        body: JSON.stringify({
          course_id: courseId,
          semester_id: semId,
          student_uid: studentUid,
          score: parseFloat(document.getElementById('edit-score').value)
        })
      });
      showToast('Mark updated successfully');
      closeModal();
      loadCourseMarksAndStats(courseId, semId);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
};

window.openBulkUploadModal = function(courseId, semId) {
  const modal = document.createElement('div');
  modal.className = 'modal-backdrop';
  modal.id = 'active-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h2 style="margin-bottom: 1.25rem;">Bulk Upload Marks (CSV)</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">
        Upload a CSV file containing columns: <code>student_id</code> (or email) and <code>score</code>.
      </p>
      <form id="bulk-upload-form">
        <div class="form-group">
          <label>CSV File</label>
          <input type="file" id="csv-file-input" accept=".csv" required />
        </div>
        <div id="upload-report" style="margin-top: 1rem; display: none;"></div>
        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeModal()">Close</button>
          <button type="submit" class="btn btn-primary" id="btn-submit-csv">Upload & Validate</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  
  document.getElementById('bulk-upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('csv-file-input');
    if (!fileInput.files || fileInput.files.length === 0) return;
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('course_id', courseId);
    formData.append('semester_id', semId);
    
    const reportDiv = document.getElementById('upload-report');
    reportDiv.style.display = 'block';
    reportDiv.innerHTML = `<p>Validating and uploading records...</p>`;
    
    try {
      const res = await apiRequest('/api/teacher/marks/bulk-upload', {
        method: 'POST',
        body: formData,
        isFormData: true
      });
      
      let errorHtml = '';
      if (res.errors && res.errors.length > 0) {
        errorHtml = `
          <div style="background: var(--danger-bg); border: 1px solid var(--danger); padding: 0.75rem; border-radius: 6px; margin-top: 0.5rem; max-height: 120px; overflow-y: auto;">
            <b>Validation Errors (${res.errors.length}):</b><br/>
            ${res.errors.map(err => `• Row ${err.row}: ${err.error}`).join('<br/>')}
          </div>
        `;
      }
      
      reportDiv.innerHTML = `
        <div style="background: var(--success-bg); border: 1px solid var(--success); padding: 0.75rem; border-radius: 6px;">
          ✅ Successfully processed <b>${res.processed_count}</b> student records!
        </div>
        ${errorHtml}
      `;
      showToast(res.message);
      loadCourseMarksAndStats(courseId, semId);
    } catch (err) {
      reportDiv.innerHTML = `<div style="color: var(--danger);">Upload failed: ${err.message}</div>`;
      showToast(err.message, 'error');
    }
  });
};

// ==========================================
// STUDENT DASHBOARD
// ==========================================

async function renderStudentDashboard() {
  const container = document.getElementById('role-dashboard');
  container.innerHTML = `
    <div class="card">
      <div class="card-title">
        <div>
          <h3>Academic Results & Performance</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.2rem;">
            Roll No: <b>${state.user.student_id || state.user.uid}</b>
          </p>
        </div>
        <div style="display: flex; gap: 0.75rem; align-items: center;">
          <select id="student-sem-select" style="width: auto; padding: 0.4rem 0.8rem;" onchange="loadStudentResults()">
            <option value="SEM-2025-SPRING">Spring 2025</option>
            <option value="SEM-2024-FALL">Fall 2024</option>
          </select>
          <button class="btn btn-primary btn-sm" id="btn-download-pdf" onclick="downloadStudentPdf()">📄 Download Official PDF</button>
        </div>
      </div>
      
      <!-- Student Summary Stats -->
      <div id="student-summary-stats" class="stat-grid"></div>
      
      <!-- Course Breakdown Table -->
      <div id="student-results-table">Loading results...</div>
    </div>
  `;
  
  loadStudentResults();
}

async function loadStudentResults() {
  const semId = document.getElementById('student-sem-select')?.value || 'SEM-2025-SPRING';
  try {
    const data = await apiRequest(`/api/student/results?semester_id=${semId}`);
    
    // Render Stats
    const semSum = data.semester_summary;
    const cumSum = data.cumulative_summary;
    const statsEl = document.getElementById('student-summary-stats');
    if (statsEl) {
      statsEl.innerHTML = `
        <div class="stat-box">
          <div class="stat-label">Semester GPA (SGPA)</div>
          <div class="stat-value" style="color: var(--primary);">${semSum.gpa.toFixed(2)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Cumulative GPA (CGPA)</div>
          <div class="stat-value" style="color: var(--secondary);">${cumSum.cgpa.toFixed(2)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Credits Registered</div>
          <div class="stat-value">${semSum.total_credits}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Semester Status</div>
          <div class="stat-value">
            <span class="status-badge ${semSum.all_passed ? 'pass' : 'fail'}" style="font-size: 1rem; padding: 0.3rem 0.8rem;">
              ${semSum.all_passed ? 'PASSED' : 'BACKLOG'}
            </span>
          </div>
        </div>
      `;
    }
    
    // Render Results Table
    const tableEl = document.getElementById('student-results-table');
    if (tableEl) {
      if (data.marks.length === 0) {
        tableEl.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No published results found for this semester.</p>`;
        return;
      }
      
      let rows = data.marks.map(m => `
        <tr>
          <td><b>${m.course_code}</b></td>
          <td>${m.course_title}</td>
          <td>${m.credits}</td>
          <td><b>${m.score}</b> / ${m.max_marks}</td>
          <td><b>${m.grade}</b></td>
          <td>${m.grade_points}</td>
          <td><span class="status-badge ${m.is_pass ? 'pass' : 'fail'}">${m.is_pass ? 'PASS' : 'FAIL'}</span></td>
        </tr>
      `).join('');
      
      tableEl.innerHTML = `
        <div class="table-responsive">
          <table>
            <thead><tr><th>Course Code</th><th>Course Title</th><th>Credits</th><th>Score</th><th>Grade</th><th>Grade Points</th><th>Status</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

window.downloadStudentPdf = async function() {
  const semId = document.getElementById('student-sem-select')?.value || 'SEM-2025-SPRING';
  try {
    const resp = await fetch(`/api/student/results/export-pdf?semester_id=${semId}`, {
      headers: {
        'Authorization': `Bearer ${state.token}`
      }
    });
    if (!resp.ok) {
      throw new Error("Failed to generate PDF");
    }
    const blob = await resp.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `Academic_Result_${state.user.student_id || 'Student'}_${semId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    showToast("PDF Transcript downloaded successfully!");
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  renderApp();
});
