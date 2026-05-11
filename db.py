import streamlit as st
from supabase import create_client, Client
import uuid
from datetime import datetime
import json

# ── Conexão ───────────────────────────────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def load_negs() -> list:
    """Carrega todas as negociações com retry automático."""
    import time
    for tentativa in range(3):
        try:
            db = get_client()
            res = db.table("negociacoes").select("*").order("criado_em", desc=True).execute()
            negs = []
            for row in res.data:
                row["notas"] = json.loads(row["notas"]) if isinstance(row["notas"], str) else row["notas"]
                row["timeline"] = json.loads(row["timeline"]) if isinstance(row["timeline"], str) else row["timeline"]
                negs.append(row)
            return negs
        except Exception:
            if tentativa < 2:
                time.sleep(0.5)
            else:
                return []


def save_neg(neg: dict):
    """Insere uma nova negociação."""
    db = get_client()
    row = {**neg}
    row["notas"] = json.dumps(neg["notas"], ensure_ascii=False)
    row["timeline"] = json.dumps(neg["timeline"], ensure_ascii=False)
    db.table("negociacoes").insert(row).execute()


def update_neg(neg_id: str, fields: dict):
    """Atualiza campos de uma negociação existente."""
    db = get_client()
    row = {**fields}
    if "timeline" in row and isinstance(row["timeline"], list):
        row["timeline"] = json.dumps(row["timeline"], ensure_ascii=False)
    db.table("negociacoes").update(row).eq("id", neg_id).execute()


def delete_neg(neg_id: str):
    """Remove uma negociação."""
    db = get_client()
    db.table("negociacoes").delete().eq("id", neg_id).execute()


# ── Lógica de negócio ─────────────────────────────────────────────────────────

APPROVERS = ["Alexandre Vieira", "Beatriz Esteves"]

STATUS_LABELS = {
    "pendente":  "Aguarda aprovação",
    "aprovada":  "Aprovada",
    "recusada":  "Recusada",
    "concluida": "Concluída",
}

def calcular_ganho(valor_total: float, taxa: float) -> float:
    return round(valor_total * taxa / 100, 2)

def alcada_status(taxa: float) -> str:
    if taxa >= 2.0 and taxa <= 3.0:
        return "ok"
    if taxa > 3.0:
        return "above"
    return "below"

def novo_id() -> str:
    return str(uuid.uuid4())[:10]


# ── Fornecedores ──────────────────────────────────────────────────────────────

def load_fornecedores() -> list:
    """Carrega fornecedores com retry automático."""
    import time
    for tentativa in range(3):
        try:
            db = get_client()
            res = db.table("fornecedores").select("*").order("nome").execute()
            return res.data
        except Exception:
            if tentativa < 2:
                time.sleep(0.5)
            else:
                return []

def save_fornecedor(nome: str, cnpj: str, contato: str = "", obs: str = ""):
    db = get_client()
    db.table("fornecedores").insert({
        "id": str(uuid.uuid4())[:10],
        "nome": nome.strip(),
        "cnpj": cnpj.strip(),
        "contato": contato.strip(),
        "obs": obs.strip(),
        "criado_em": datetime.now().isoformat(),
    }).execute()

def update_fornecedor(forn_id: str, fields: dict):
    db = get_client()
    db.table("fornecedores").update(fields).eq("id", forn_id).execute()

def delete_fornecedor(forn_id: str):
    db = get_client()
    db.table("fornecedores").delete().eq("id", forn_id).execute()
