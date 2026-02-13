let sb;
let token = localStorage.getItem('codelingo_token') || '';
let lessonIndex = Number(localStorage.getItem('lesson_idx') || 0);
let curriculumCache = null;

async function getSupabase() {
  if (sb) return sb;
  const config = await fetch('/api/public-config').then((r) => r.json());
  if (!config.supabase_url || !config.supabase_anon_key || !window.supabase) return null;
  sb = window.supabase.createClient(config.supabase_url, config.supabase_anon_key);
  return sb;
}

function headers() {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function signup() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const supabase = await getSupabase();
  if (!supabase) return setMsg('authMsg', 'Supabase non configuré: mode démo login direct.');
  const { error } = await supabase.auth.signUp({ email, password });
  setMsg('authMsg', error ? error.message : 'Compte créé, connecte-toi maintenant.');
}

async function login() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const supabase = await getSupabase();
  if (!supabase) {
    token = 'demo-token';
    localStorage.setItem('codelingo_token', token);
    location.href = '/app/onboarding';
    return;
  }

  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) return setMsg('authMsg', error.message);
  token = data.session.access_token;
  localStorage.setItem('codelingo_token', token);
  location.href = '/app/onboarding';
}

function logout() {
  localStorage.removeItem('codelingo_token');
  localStorage.removeItem('lesson_idx');
  location.href = '/app/login';
}

function setMsg(id, msg) {
  const node = document.getElementById(id);
  if (node) node.textContent = msg;
}

async function apiGet(path) {
  const res = await fetch(path, { headers: headers() });
  if (res.status === 401) {
    location.href = '/app/login';
    throw new Error('Unauthorized');
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers() },
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    location.href = '/app/login';
    throw new Error('Unauthorized');
  }
  return res.json();
}

async function loadCurriculum() {
  if (!curriculumCache) curriculumCache = await apiGet('/api/curriculum');
  return curriculumCache;
}

async function completeOnboarding() {
  const payload = {
    display_name: document.getElementById('displayName').value || 'CodeLearner',
    goal: document.getElementById('goal').value,
  };
  await apiPost('/api/onboarding', payload);
  location.href = '/app/dashboard';
}

async function initDashboardPage() {
  const data = await apiGet('/api/dashboard');
  const statHead = document.querySelector('.stat-head');
  statHead.innerHTML = `<span>🔥 ${data.streak.current_streak}</span><span>🐍 Python</span><span>⚡ ${data.total_xp}</span>`;

  const timeline = document.getElementById('timeline');
  const cur = await loadCurriculum();
  timeline.innerHTML = cur.lessons
    .map((l, idx) => `<div class='node'><div class='node-index'>${idx + 10}</div><div class='node-card' onclick='openLesson(${idx})'></div></div>`)
    .join('');
}

function openLesson(idx) {
  localStorage.setItem('lesson_idx', String(idx));
  location.href = '/app/lesson';
}

async function initLessonPage() {
  const cur = await loadCurriculum();
  const lesson = cur.lessons[lessonIndex % cur.lessons.length];
  document.getElementById('questionBox').textContent = lesson.quiz.question;
  document.getElementById('codeInput').value = lesson.exercise.starter_code;
  document.getElementById('lessonProgress').style.width = `${Math.round(((lessonIndex + 1) / cur.lessons.length) * 100)}%`;
  document.getElementById('lessonPercent').textContent = `${Math.round(((lessonIndex + 1) / cur.lessons.length) * 100)}%`;

  const choices = document.getElementById('choices');
  choices.innerHTML = lesson.quiz.options
    .map((opt) => `<button class='choice' onclick='selectChoice(${JSON.stringify(opt)})'>${opt}</button>`)
    .join('');
  window.selectedChoice = '';
}

function selectChoice(choice) {
  window.selectedChoice = choice;
  setMsg('lessonMsg', `Réponse sélectionnée: ${choice}`);
}

async function submitLesson() {
  const cur = await loadCurriculum();
  const lesson = cur.lessons[lessonIndex % cur.lessons.length];
  const result = await apiPost('/api/submit', {
    lesson_id: lesson.id,
    quiz_answer: window.selectedChoice || '',
    code: document.getElementById('codeInput').value,
  });
  setMsg('lessonMsg', result.message || '');
  document.getElementById('lessonOutput').textContent = result.output || '';
  if (result.success) {
    lessonIndex += 1;
    localStorage.setItem('lesson_idx', String(lessonIndex));
  }
}

async function initProfilePage() {
  const data = await apiGet('/api/profile');
  document.getElementById('profileEmail').textContent = data.user.email;
  document.getElementById('profileLevel').textContent = data.user.current_level;
  document.getElementById('profileXP').textContent = data.user.total_xp;
  document.getElementById('profileStreak').textContent = `${data.streak.current_streak} jours (best ${data.streak.best_streak})`;
  document.getElementById('profileBadges').textContent = data.badges.length
    ? data.badges.map((b) => b.name || b.id).join(', ')
    : 'Aucun badge';
  document.getElementById('profileHistory').innerHTML = data.history.length
    ? data.history.map((h) => `+${h.xp_delta} XP (${h.reason})`).join('<br/>')
    : 'Pas encore d’activité';
}
