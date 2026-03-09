-- Projects
create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null default 'Untitled Project',
  prompt text,
  status text not null default 'draft', -- draft, generating, complete, failed
  preview_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Generated files
create table if not exists project_files (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id) on delete cascade not null,
  path text not null,
  content text not null,
  language text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(project_id, path)
);

-- Agent execution logs
create table if not exists agent_logs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id) on delete cascade not null,
  agent_name text not null,
  status text not null, -- started, progress, completed, failed
  message text,
  files_generated int default 0,
  created_at timestamptz not null default now()
);

-- RLS policies
alter table projects enable row level security;
alter table project_files enable row level security;
alter table agent_logs enable row level security;

create policy "Users can CRUD own projects" on projects
  for all using (auth.uid() = user_id);

create policy "Users can CRUD own project files" on project_files
  for all using (project_id in (select id from projects where user_id = auth.uid()));

create policy "Users can read own agent logs" on agent_logs
  for all using (project_id in (select id from projects where user_id = auth.uid()));

-- Indexes
create index if not exists idx_projects_user_id on projects(user_id);
create index if not exists idx_project_files_project_id on project_files(project_id);
create index if not exists idx_agent_logs_project_id on agent_logs(project_id);

-- Updated_at trigger
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger set_projects_updated_at
  before update on projects
  for each row execute function update_updated_at_column();

create trigger set_project_files_updated_at
  before update on project_files
  for each row execute function update_updated_at_column();
