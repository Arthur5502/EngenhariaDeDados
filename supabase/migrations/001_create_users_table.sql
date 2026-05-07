-- Tabela de perfis de usuários (vinculada ao auth.users do Supabase)
create table if not exists public.users (
    id          uuid primary key references auth.users(id) on delete cascade,
    nome        text        not null,
    cpf         text        not null unique,
    cnpj        text        not null unique,
    telefone    text        not null,
    razao_social  text      not null,
    cnae_principal text     not null,
    uf          char(2)     not null,
    municipio   text        not null,
    ativo       boolean     not null default true,
    created_at  timestamptz not null default now()
);

-- Somente o próprio usuário pode ler/alterar seu perfil
alter table public.users enable row level security;

create policy "usuario_le_proprio_perfil"
    on public.users for select
    using (auth.uid() = id);

create policy "usuario_insere_proprio_perfil"
    on public.users for insert
    with check (auth.uid() = id);

create policy "usuario_atualiza_proprio_perfil"
    on public.users for update
    using (auth.uid() = id);

-- Service role ignora RLS, então o backend com SERVICE_KEY tem acesso total
