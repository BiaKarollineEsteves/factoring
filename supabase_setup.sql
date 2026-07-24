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

-- Tabela de fornecedores (rode este bloco se o app já estava configurado)
create table if not exists fornecedores (
  id         text primary key,
  nome       text not null,
  cnpj       text not null,
  contato    text,
  obs        text,
  criado_em  text not null
);

alter table fornecedores enable row level security;

create policy "allow_all_fornecedores" on fornecedores
  for all using (true) with check (true);

-- Tabela de compensações (rode no Supabase SQL Editor)
create table if not exists compensacoes (
  id                text primary key,
  num_adiantamento  text not null,
  neg_id            text not null,
  fornecedor        text not null,
  nf                text not null,
  valor_nf          numeric(15,2) not null,
  valor_desconto    numeric(15,2) not null,
  data_vencimento   text not null,
  data_antecipado   text not null,
  status            text not null default 'pendente',
  criado_em         text not null,
  criado_por        text,
  compensado_em     text,
  compensado_por    text,
  obs               text
);

alter table compensacoes enable row level security;
create policy "allow_all_compensacoes" on compensacoes
  for all using (true) with check (true);

-- Adiciona campos bancários na tabela fornecedores (rode se já existir a tabela)
alter table fornecedores add column if not exists banco       text;
alter table fornecedores add column if not exists agencia     text;
alter table fornecedores add column if not exists conta       text;
alter table fornecedores add column if not exists tipo_conta  text;
alter table fornecedores add column if not exists pix         text;
alter table fornecedores add column if not exists cnpj_fav    text;
