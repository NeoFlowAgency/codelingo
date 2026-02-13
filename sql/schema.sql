-- CodeLingo Supabase schema (PostgreSQL)
create extension if not exists "pgcrypto";

create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  display_name text not null default 'CodeLearner',
  avatar_seed text not null default 'bot',
  goal text,
  onboarding_completed boolean not null default false,
  current_level integer not null default 1 check (current_level > 0),
  total_xp integer not null default 0 check (total_xp >= 0),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.modules (
  id text primary key,
  title text not null,
  description text not null,
  order_index integer not null unique check (order_index > 0),
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.lessons (
  id text primary key,
  module_id text not null references public.modules(id) on delete cascade,
  title text not null,
  explanation text not null,
  code_example text not null,
  quiz_question text not null,
  quiz_options jsonb not null,
  quiz_answer text not null,
  order_index integer not null,
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  unique (module_id, order_index)
);

create table if not exists public.exercises (
  id uuid primary key default gen_random_uuid(),
  lesson_id text not null unique references public.lessons(id) on delete cascade,
  prompt text not null,
  starter_code text not null,
  expected_output text not null,
  xp_reward integer not null check (xp_reward >= 0),
  validator_type text not null default 'output_exact',
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.user_progress (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  lesson_id text not null references public.lessons(id) on delete cascade,
  is_completed boolean not null default false,
  xp_earned integer not null default 0 check (xp_earned >= 0),
  completed_at date,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (user_id, lesson_id)
);

create table if not exists public.user_streak (
  user_id uuid primary key references public.users(id) on delete cascade,
  current_streak integer not null default 0 check (current_streak >= 0),
  best_streak integer not null default 0 check (best_streak >= 0),
  last_activity_date date,
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.badges (
  id text primary key,
  name text not null,
  description text not null,
  rule_xp integer not null check (rule_xp >= 0),
  icon text,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.user_badges (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  badge_id text not null references public.badges(id) on delete cascade,
  earned_at date not null default current_date,
  unique (user_id, badge_id)
);

create table if not exists public.xp_history (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  reason text not null,
  xp_delta integer not null,
  lesson_id text references public.lessons(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_user_progress_user on public.user_progress(user_id);
create index if not exists idx_user_progress_completed on public.user_progress(user_id, is_completed);
create index if not exists idx_xp_history_user_created on public.xp_history(user_id, created_at desc);
create index if not exists idx_lessons_module_order on public.lessons(module_id, order_index);

alter table public.users enable row level security;
alter table public.user_progress enable row level security;
alter table public.user_streak enable row level security;
alter table public.user_badges enable row level security;
alter table public.xp_history enable row level security;

create policy "users_select_own" on public.users for select using (auth.uid() = id);
create policy "users_update_own" on public.users for update using (auth.uid() = id);
create policy "users_insert_own" on public.users for insert with check (auth.uid() = id);

create policy "progress_read_own" on public.user_progress for select using (auth.uid() = user_id);
create policy "progress_write_own" on public.user_progress for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "streak_read_own" on public.user_streak for select using (auth.uid() = user_id);
create policy "streak_write_own" on public.user_streak for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "badges_read_own" on public.user_badges for select using (auth.uid() = user_id);
create policy "badges_write_own" on public.user_badges for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "history_read_own" on public.xp_history for select using (auth.uid() = user_id);
create policy "history_write_own" on public.xp_history for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- shared read tables
alter table public.modules enable row level security;
alter table public.lessons enable row level security;
alter table public.exercises enable row level security;
alter table public.badges enable row level security;
create policy "modules_public_read" on public.modules for select using (true);
create policy "lessons_public_read" on public.lessons for select using (true);
create policy "exercises_public_read" on public.exercises for select using (true);
create policy "badges_public_read" on public.badges for select using (true);

-- Seed content
insert into public.modules (id, title, description, order_index) values
('variables','Variables','Stocke des données simplement.',1),
('conditions','Conditions','Prends des décisions avec if/else.',2),
('loops','Boucles','Répète des actions.',3),
('lists','Listes','Manipule des collections.',4),
('functions','Fonctions','Réutilise ton code.',5)
on conflict (id) do update set title=excluded.title, description=excluded.description, order_index=excluded.order_index;

insert into public.badges (id,name,description,rule_xp,icon) values
('first-steps','Premier pas','Valider la première leçon.',25,'🥉'),
('focused','Concentré','Atteindre 100 XP.',100,'🥈'),
('python-rookie','Python Rookie','Atteindre 200 XP.',200,'🥇')
on conflict (id) do update set name=excluded.name, description=excluded.description, rule_xp=excluded.rule_xp, icon=excluded.icon;
