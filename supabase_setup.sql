-- Execute este SQL no Supabase: Dashboard → SQL Editor → New Query

create table if not exists negociacoes (
  id           text primary key,
  fornecedor   text not null,
  cnpj         text,
  notas        text not null,        -- JSON array
  taxa         numeric(5,2) not null,
  obs          text,
  valor_total  numeric(15,2) not null,
  ganho        numeric(15,2) not null,
  valor_pago   numeric(15,2) not null,
  status       text not null default 'concluida',
  criado_em    text not null,
  criado_por   text,
  aprovador_id text,
  decisao_em   text,
  timeline     text not null         -- JSON array
);

-- Permite leitura/escrita pública (ajuste conforme sua política de segurança)
alter table negociacoes enable row level security;

create policy "allow_all" on negociacoes
  for all using (true) with check (true);
