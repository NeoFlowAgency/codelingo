let supabaseClient;

async function getSupabase() {
  if (supabaseClient) return supabaseClient;
  const res = await fetch('/api/public-config');
  const cfg = await res.json();
  if (cfg.supabase_url && cfg.supabase_anon_key && window.supabase) {
    supabaseClient = window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key);
  }
  return supabaseClient;
}

function getToken() {
  return localStorage.getItem('access_token') || '';
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function signup() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const supabase = await getSupabase();
  if (!supabase) return setMsg('authMsg', 'Configure Supabase pour l’auth réelle.', true);
  const { error } = await supabase.auth.signUp({ email, password });
  if (error) return setMsg('authMsg', error.message, true);
  setMsg('authMsg', 'Compte créé. Vérifie ton email si confirmation activée.');
}

async function login() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const supabase = await getSupabase();
  if (!supabase) {
    localStorage.setItem('access_token', 'demo-token');
    window.location.href = '/dashboard';
    return;
  }
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) return setMsg('authMsg', error.message, true);
  localStorage.setItem('access_token', data.session.access_token);
  window.location.href = '/dashboard';
}

function logout() {
  localStorage.removeItem('access_token');
  window.location.href = '/login';
}

function setMsg(id, msg, isError = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = isError ? 'text-red-300 text-sm' : 'text-emerald-300 text-sm';
}

async function apiGet(url) {
  const res = await fetch(url, { headers: { ...authHeaders() } });
  if (res.status === 401) {
    if (!location.pathname.includes('/login')) window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  return res.json();
}

async function initDashboard() {
  const data = await apiGet('/api/bootstrap');
  const cards = [
    ['XP', data.profile.total_xp],
    ['Streak', `${data.profile.streak} 🔥`],
    ['Progression', `${data.stats.completion_pct}%`],
    ['Badges', data.profile.badges.length],
  ];
  document.getElementById('statsCards').innerHTML = cards
    .map(([label, value]) => `<div class="bg-slate-900 border border-slate-800 rounded-xl p-4"><p class="text-slate-400 text-xs">${label}</p><p class="text-xl font-bold">${value}</p></div>`)
    .join('');

  const next = data.lessons.find((l) => !l.progress.completed) || data.lessons[data.lessons.length - 1];
  document.getElementById('nextLesson').innerHTML = `<h3 class="font-semibold">${next.title}</h3><p class="text-sm text-slate-300">${next.description}</p><a class="inline-block mt-2 bg-emerald-500 text-slate-950 px-3 py-2 rounded" href="/lessons/${next.slug}">Continuer</a>`;
}

async function initLessons() {
  const lessons = await apiGet('/api/lessons');
  document.getElementById('lessonsList').innerHTML = lessons
    .map(
      (l, i) => `<a href="/lessons/${l.slug}" class="block bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div class="flex items-center justify-between gap-2"><h3 class="font-semibold">${i + 1}. ${l.title}</h3><span class="text-xs ${l.progress.completed ? 'text-emerald-300' : 'text-slate-400'}">${l.progress.completed ? '✅ terminé' : '⏳ à faire'}</span></div>
        <p class="text-sm text-slate-300">${l.description}</p>
      </a>`
    )
    .join('');
}

async function initLessonDetail() {
  const root = document.getElementById('lessonDetail');
  const slug = root.dataset.slug;
  const lesson = await apiGet(`/api/lessons/${slug}`);
  document.getElementById('lessonTitle').textContent = lesson.title;
  document.getElementById('lessonContent').textContent = lesson.content;
  document.getElementById('lessonExample').textContent = lesson.example;
  document.getElementById('exerciseTitle').textContent = lesson.exercise.title + ` (+${lesson.exercise.xp} XP)`;
  document.getElementById('exercisePrompt').textContent = lesson.exercise.prompt;
  document.getElementById('codeInput').value = lesson.exercise.starter_code;
}

async function submitExercise() {
  const root = document.getElementById('lessonDetail');
  const slug = root.dataset.slug;
  const code = document.getElementById('codeInput').value;
  const res = await fetch(`/api/exercises/${slug}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ code }),
  });
  const data = await res.json();
  const ok = data.success;
  setMsg('exerciseFeedback', data.feedback, !ok);
  document.getElementById('exerciseOutput').textContent = data.output || '';
}

async function initProfile() {
  const data = await apiGet('/api/bootstrap');
  document.getElementById('profileEmail').textContent = data.user.email || 'demo@local.dev';
  document.getElementById('profileXP').textContent = data.profile.total_xp;
  document.getElementById('profileStreak').textContent = data.profile.streak;
  document.getElementById('profileBadges').innerHTML = data.profile.badges.length
    ? data.profile.badges.map((b) => `<span class="px-3 py-1 rounded-full bg-emerald-900 text-emerald-200 text-sm">${b}</span>`).join('')
    : '<span class="text-slate-400 text-sm">Aucun badge pour le moment.</span>';
}
