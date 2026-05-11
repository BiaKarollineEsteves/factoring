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
    """Carrega todas as negociações do Supabase."""
    try:
        db = get_client()
        res = db.table("negociacoes").select("*").order("criado_em", desc=True).execute()
        negs = []
        for row in res.data:
            # notas e timeline são JSON strings no banco
            row["notas"] = json.loads(row["notas"]) if isinstance(row["notas"], str) else row["notas"]
            row["timeline"] = json.loads(row["timeline"]) if isinstance(row["timeline"], str) else row["timeline"]
            negs.append(row)
        return negs
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
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
