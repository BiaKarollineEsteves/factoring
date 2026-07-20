# 🏦 Factoring — Negociação com Fornecedores

App Streamlit hospedado na nuvem. Dados salvos no Supabase (gratuito).

---

## 🗺 Visão geral

```
GitHub (seu código) ──► Streamlit Cloud (roda o app) ──► Supabase (banco de dados)
```

Tudo gratuito. Você acessa via link público no navegador, sem instalar nada.

---

## ✅ Passo a passo completo

### PARTE 1 — Supabase (banco de dados)

**1.1** Acesse **https://supabase.com** → clique em **Start your project** → faça login com GitHub

**1.2** Clique em **New project**:
- Nome: `factoring`
- Senha do banco: anote em algum lugar seguro
- Região: South America (São Paulo)
- Clique em **Create new project** e aguarde ~2 minutos

**1.3** Crie a tabela do app:
- No menu lateral, clique em **SQL Editor**
- Clique em **New query**
- Copie e cole o conteúdo do arquivo `supabase_setup.sql` (incluso no projeto)
- Clique em **Run** (▶)
- Deve aparecer: *Success. No rows returned*

**1.4** Pegue as credenciais:
- No menu lateral, clique em **Project Settings → API**
- Copie:
  - **Project URL** (ex: `https://abcdefgh.supabase.co`)
  - **anon public key** (começa com `eyJ...`)

---

### PARTE 2 — GitHub (código)

**2.1** Acesse **https://github.com** → faça login → clique em **New repository**
- Nome: `factoring`
- Visibilidade: **Private** (recomendado)
- Clique em **Create repository**

**2.2** Faça upload dos arquivos:
- Clique em **uploading an existing file**
- Arraste os arquivos: `app.py`, `db.py`, `excel.py`, `requirements.txt`, `.gitignore`
- **Não suba** o arquivo `.streamlit/secrets.toml` (contém senhas!)
- Clique em **Commit changes**

---

### PARTE 3 — Streamlit Cloud (hospedagem)

**3.1** Acesse **https://share.streamlit.io** → clique em **Sign in with GitHub**

**3.2** Clique em **New app**:
- Repository: selecione `factoring`
- Branch: `main`
- Main file path: `app.py`
- Clique em **Advanced settings...**

**3.3** Em **Secrets**, cole o seguinte (substituindo pelos valores do Supabase):
```toml
[supabase]
url = "https://SEU_URL.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**3.4** Clique em **Deploy!** e aguarde ~1 minuto

**3.5** Pronto! Você vai receber um link do tipo:
`https://seu-nome-factoring.streamlit.app`

---

## 🔄 Como atualizar o app no futuro

1. Edite os arquivos no VSCode
2. No GitHub, abra o arquivo → clique no lápis (editar) → cole o novo conteúdo → **Commit**
3. O Streamlit Cloud atualiza automaticamente em ~30 segundos

---

## 📁 Estrutura do projeto

```
factoring/
├── app.py                  # App principal (telas e navegação)
├── db.py                   # Conexão com Supabase e funções de dados
├── excel.py                # Geração de planilhas Excel
├── requirements.txt        # Dependências Python
├── supabase_setup.sql      # SQL para criar a tabela (rodar 1x no Supabase)
├── .gitignore              # Arquivos a ignorar no GitHub
└── .streamlit/
    └── secrets.toml        # ⚠ NÃO subir no GitHub — suas credenciais
```

---

## 🔐 Lógica de alçadas

| Taxa | Ação |
|---|---|
| Abaixo de 2% | Vai para aprovação de Alexandre Vieira ou Beatriz Esteves |
| 2% a 3% | Negociador conclui direto |
| Acima de 3% | Alerta — favorável mas incomum |

---

## ❓ Problemas comuns

**App abre mas dá erro de banco**
→ Verifique se o `secrets.toml` está configurado corretamente no Streamlit Cloud

**"Table not found"**
→ Rode o `supabase_setup.sql` no Supabase SQL Editor

**Quero trocar os aprovadores**
→ Edite a variável `APPROVERS` no arquivo `db.py`
