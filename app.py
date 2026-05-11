import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
import hashlib

from db import (
    load_negs, save_neg, update_neg, delete_neg,
    calcular_ganho, alcada_status, novo_id,
    STATUS_LABELS, APPROVERS
)
from excel import gerar_historico, gerar_relatorio

st.set_page_config(
    page_title="Factoring",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Login ──────────────────────────────────────────────────────────────────────

def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def check_login(usuario: str, senha: str) -> bool:
    usuarios = st.secrets.get("usuarios", {})
    hash_correto = usuarios.get(usuario)
    if not hash_correto:
        return False
    return _hash(senha) == hash_correto

def tela_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🏦 Factoring")
        st.markdown("*Negociação com fornecedores*")
        st.divider()
        with st.form("login_form"):
            usuario = st.selectbox("Usuário", ["Claudia Passos", "Alexandre Vieira", "Beatriz Esteves"])
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if entrar:
            if check_login(usuario, senha):
                st.session_state.autenticado = True
                st.session_state.usuario = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    tela_login()
    st.stop()  # Nada abaixo é renderizado sem login

st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 230px !important; max-width: 230px !important; }
.alçada-ok  { background:#E1F5EE; color:#0F6E56; padding:10px 14px; border-radius:8px; font-size:13px; margin-bottom:12px; }
.alçada-warn{ background:#FAEEDA; color:#854F0B; padding:10px 14px; border-radius:8px; font-size:13px; margin-bottom:12px; }
.alçada-err { background:#FCEBEB; color:#A32D2D; padding:10px 14px; border-radius:8px; font-size:13px; margin-bottom:12px; }
.timeline-item { border-left: 2px solid #e0e0e0; padding: 4px 0 10px 16px; margin-left: 8px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = "Claudia Passos"
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"
if "negs" not in st.session_state:
    st.session_state.negs = load_negs()

def reload():
    st.session_state.negs = load_negs()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏦 Factoring")
    st.markdown("*Negociação com fornecedores*")
    st.divider()

    pendentes = sum(1 for n in st.session_state.negs if n["status"] == "pendente")
    label_aprov = f"Aprovações 🔴 {pendentes}" if pendentes > 0 else "Aprovações"

    for p in ["Dashboard", "Nova negociação", "Negociações", label_aprov, "Relatórios"]:
        p_clean = p.split(" 🔴")[0].strip()
        ativo = st.session_state.pagina == p_clean
        if st.button(p, use_container_width=True, type="primary" if ativo else "secondary"):
            st.session_state.pagina = p_clean
            reload()
            st.rerun()

    st.divider()
    st.caption(f"👤 {st.session_state.usuario}")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.rerun()

pagina = st.session_state.pagina
negs = st.session_state.negs

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "Dashboard":
    st.title("Dashboard")
    concluidas = [n for n in negs if n["status"] in ("concluida", "aprovada")]
    ganho_total = sum(float(n["ganho"]) for n in concluidas)
    taxa_media = (sum(float(n["taxa"]) for n in concluidas) / len(concluidas)) if concluidas else 0

    def brl(v): return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Ganho total", brl(ganho_total))
    c2.metric("📋 Negociações", len(negs))
    c3.metric("📊 Taxa média", f"{taxa_media:.2f}%".replace(".",",") if taxa_media else "—")
    c4.metric("⏳ Aguardando aprovação", pendentes)

    st.divider()
    st.subheader("Últimas negociações")
    if not negs:
        st.info("Nenhuma negociação ainda. Use **Nova negociação** para começar.")
    else:
        rows = [{
            "Fornecedor": n["fornecedor"],
            "NF(s)": ", ".join(x["nf"] for x in (n["notas"] if isinstance(n["notas"], list) else [])),
            "Valor total": brl(n["valor_total"]),
            "Taxa": f"{float(n['taxa']):.2f}%".replace(".",","),
            "Ganho": brl(n["ganho"]),
            "Data": datetime.fromisoformat(n["criado_em"]).strftime("%d/%m/%Y"),
            "Status": STATUS_LABELS.get(n["status"], n["status"]),
        } for n in negs[:10]]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# NOVA NEGOCIAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Nova negociação":
    st.title("Nova negociação")

    with st.form("form_neg", clear_on_submit=True):
        st.subheader("Fornecedor")
        col1, col2 = st.columns(2)
        fornecedor = col1.text_input("Fornecedor *", placeholder="Razão social ou nome")
        cnpj = col2.text_input("CNPJ", placeholder="00.000.000/0000-00")

        st.subheader("Notas fiscais")
        num_notas = st.number_input("Quantidade de notas", min_value=1, max_value=20, value=1, step=1)
        notas_input = []
        for i in range(int(num_notas)):
            st.markdown(f"**Nota {i+1}**")
            c1, c2, c3, c4 = st.columns(4)
            nf       = c1.text_input("Número NF *",   key=f"nf_{i}",      placeholder="NF-0000")
            venc     = c2.date_input("Vencimento *",   key=f"venc_{i}",    value=date.today())
            valor    = c3.number_input("Valor (R$) *", key=f"valor_{i}",   min_value=0.0, step=100.0, format="%.2f")
            desdobr  = c4.text_input("Desdobramento",  key=f"desdobr_{i}", placeholder="ex: 1/3")
            notas_input.append({"id": str(uuid.uuid4())[:8], "nf": nf,
                                "vencimento": str(venc), "valor": valor, "desdobramento": desdobr})

        valor_total = sum(float(n["valor"]) for n in notas_input)
        if valor_total > 0:
            st.markdown(f"**Total: R$ {valor_total:,.2f}**".replace(",","X").replace(".",",").replace("X","."))

        st.subheader("Taxa negociada")
        taxa = st.slider("Taxa (%)", min_value=0.5, max_value=4.0, value=2.5, step=0.1, format="%.1f%%")
        ganho = calcular_ganho(valor_total, taxa)
        valor_pago = valor_total - ganho

        alc = alcada_status(taxa)
        if alc == "ok":
            st.markdown('<div class="alçada-ok">✅ <strong>Dentro da alçada (2%–3%)</strong> — conclui direto, sem aprovação.</div>', unsafe_allow_html=True)
        elif alc == "above":
            st.markdown('<div class="alçada-warn">⚠️ <strong>Acima do teto (3%)</strong> — favorável, verifique se está correto.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alçada-err">🔒 <strong>Abaixo da alçada (2%)</strong> — será enviado para aprovação automaticamente.</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        def brl(v): return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        c1.metric("Ganho estimado", brl(ganho))
        c2.metric("Valor a pagar", brl(valor_pago))
        c3.metric("Desconto", f"{taxa:.1f}%".replace(".",","))

        obs = st.text_area("Observações / justificativa", placeholder="Contexto da negociação...")
        submitted = st.form_submit_button("💾 Registrar negociação", type="primary", use_container_width=True)

    if submitted:
        erros = []
        if not fornecedor.strip(): erros.append("Fornecedor é obrigatório.")
        for i, n in enumerate(notas_input):
            if not n["nf"].strip(): erros.append(f"Nota {i+1}: número da NF obrigatório.")
            if float(n["valor"]) <= 0: erros.append(f"Nota {i+1}: valor deve ser maior que zero.")
        if erros:
            for e in erros: st.error(e)
        else:
            alc = alcada_status(taxa)
            status = "pendente" if alc == "below" else "concluida"
            now = datetime.now().isoformat()
            timeline = [{"at": now, "msg": f"Registrada por {st.session_state.usuario}. Taxa: {taxa:.2f}%"}]
            if alc == "below":
                timeline.append({"at": now, "msg": "Enviado para aprovação (taxa abaixo de 2%)."})
            neg = {
                "id": novo_id(),
                "fornecedor": fornecedor.strip(),
                "cnpj": cnpj.strip(),
                "notas": notas_input,
                "taxa": taxa,
                "obs": obs.strip(),
                "valor_total": valor_total,
                "ganho": ganho,
                "valor_pago": valor_pago,
                "status": status,
                "criado_em": now,
                "criado_por": st.session_state.usuario,
                "aprovador_id": None,
                "decisao_em": None,
                "timeline": timeline,
            }
            save_neg(neg)
            reload()
            if alc == "below":
                st.success("✅ Enviado para aprovação de Alexandre Vieira / Beatriz Esteves!")
            else:
                st.success("✅ Negociação registrada!")
            st.balloons()

# ══════════════════════════════════════════════════════════════════════════════
# NEGOCIAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Negociações":
    st.title("Negociações")
    def brl(v): return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

    col1, col2, col3 = st.columns([3, 1, 1])
    busca = col1.text_input("🔍 Buscar", label_visibility="collapsed", placeholder="Buscar fornecedor ou NF...")
    filtro = col2.selectbox("Status", ["Todos","concluida","aprovada","pendente","recusada"], label_visibility="collapsed")

    excel_bytes = gerar_historico(negs)
    col3.download_button("⬇ Excel", data=excel_bytes,
                         file_name=f"historico_factoring_{datetime.now().strftime('%Y%m%d')}.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         use_container_width=True)

    filtered = negs
    if busca:
        b = busca.lower()
        filtered = [n for n in filtered if b in n["fornecedor"].lower() or
                    any(b in x["nf"].lower() for x in (n["notas"] if isinstance(n["notas"], list) else []))]
    if filtro != "Todos":
        filtered = [n for n in filtered if n["status"] == filtro]

    if not filtered:
        st.info("Nenhuma negociação encontrada.")
    else:
        for n in filtered:
            notas_list = n["notas"] if isinstance(n["notas"], list) else []
            nfs = ", ".join(x["nf"] for x in notas_list)
            label = f"**{n['fornecedor']}** — {nfs} — {brl(n['valor_total'])} — {STATUS_LABELS.get(n['status'], n['status'])}"
            with st.expander(label):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Valor total", brl(n["valor_total"]))
                c2.metric("Taxa", f"{float(n['taxa']):.2f}%".replace(".",","))
                c3.metric("Ganho", brl(n["ganho"]))
                c4.metric("Criado por", n.get("criado_por","—"))

                if notas_list:
                    df_n = pd.DataFrame([{"NF": x["nf"], "Vencimento": x["vencimento"],
                                          "Valor": brl(x["valor"]), "Desdobramento": x.get("desdobramento","")}
                                         for x in notas_list])
                    st.dataframe(df_n, hide_index=True, use_container_width=True)

                if n.get("obs"):
                    st.info(f"📝 {n['obs']}")

                timeline = n.get("timeline", [])
                if timeline:
                    st.caption("**Histórico:**")
                    for t in timeline:
                        dt = datetime.fromisoformat(t["at"]).strftime("%d/%m/%Y %H:%M")
                        st.markdown(f'<div class="timeline-item">🔵 <strong>{dt}</strong> — {t["msg"]}</div>', unsafe_allow_html=True)

                if st.button("🗑 Excluir", key=f"del_{n['id']}"):
                    delete_neg(n["id"])
                    reload()
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# APROVAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Aprovações":
    st.title("Aprovações pendentes")
    def brl(v): return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    pendentes_list = [n for n in negs if n["status"] == "pendente"]

    if not pendentes_list:
        st.success("✅ Tudo em dia! Sem aprovações pendentes.")
    else:
        for n in pendentes_list:
            notas_list = n["notas"] if isinstance(n["notas"], list) else []
            with st.container(border=True):
                col1, col2 = st.columns([3,1])
                col1.markdown(f"### {n['fornecedor']}")
                col1.caption(f"NF(s): {', '.join(x['nf'] for x in notas_list)} · por {n.get('criado_por','—')} · {datetime.fromisoformat(n['criado_em']).strftime('%d/%m/%Y %H:%M')}")
                col2.error(f"⚠ {float(n['taxa']):.2f}% — abaixo da alçada".replace(".",","))

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Valor total", brl(n["valor_total"]))
                c2.metric(f"Ganho com {float(n['taxa']):.1f}%".replace(".",","), brl(n["ganho"]))
                ganho_2 = float(n["valor_total"]) * 0.02
                c3.metric("Ganho com 2,0%", brl(ganho_2))
                c4.metric("Diferença", f"- {brl(ganho_2 - float(n['ganho']))}")

                if n.get("obs"):
                    st.info(f"📝 **Justificativa:** {n['obs']}")

                ca, cr, _ = st.columns([1, 1, 4])
                if ca.button("✅ Aprovar", key=f"aprov_{n['id']}", type="primary"):
                    now = datetime.now().isoformat()
                    tl = (n.get("timeline") or []) + [{"at": now, "msg": f"✓ Aprovada por {st.session_state.usuario}"}]
                    update_neg(n["id"], {"status": "aprovada", "decisao_em": now,
                                         "aprovador_id": st.session_state.usuario, "timeline": tl})
                    reload()
                    st.success("Aprovada!")
                    st.rerun()
                if cr.button("❌ Recusar", key=f"recus_{n['id']}"):
                    now = datetime.now().isoformat()
                    tl = (n.get("timeline") or []) + [{"at": now, "msg": f"✗ Recusada por {st.session_state.usuario}"}]
                    update_neg(n["id"], {"status": "recusada", "decisao_em": now,
                                         "aprovador_id": st.session_state.usuario, "timeline": tl})
                    reload()
                    st.warning("Recusada.")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RELATÓRIOS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Relatórios":
    st.title("Relatórios")
    def brl(v): return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    concluidas = [n for n in negs if n["status"] in ("concluida", "aprovada")]
    ganho_total = sum(float(n["ganho"]) for n in concluidas)
    taxa_media = (sum(float(n["taxa"]) for n in concluidas) / len(concluidas)) if concluidas else 0
    vol_total = sum(float(n["valor_total"]) for n in concluidas)

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Ganho total", brl(ganho_total))
    c2.metric("📦 Volume negociado", brl(vol_total))
    c3.metric("📊 Taxa média", f"{taxa_media:.2f}%".replace(".",",") if taxa_media else "—")

    st.divider()
    st.subheader("Ganho por fornecedor")
    if not concluidas:
        st.info("Nenhuma negociação concluída ainda.")
    else:
        por_forn = {}
        for n in concluidas:
            f = n["fornecedor"]
            if f not in por_forn:
                por_forn[f] = {"Fornecedor": f, "Negociações": 0, "Volume (R$)": 0.0, "Ganho (R$)": 0.0}
            por_forn[f]["Negociações"] += 1
            por_forn[f]["Volume (R$)"] += float(n["valor_total"])
            por_forn[f]["Ganho (R$)"] += float(n["ganho"])
        df = pd.DataFrame(por_forn.values()).sort_values("Ganho (R$)", ascending=False)
        df["% do total"] = (df["Ganho (R$)"] / ganho_total * 100).map("{:.1f}%".format) if ganho_total else "—"
        df["Volume (R$)"] = df["Volume (R$)"].map(brl)
        df["Ganho (R$)"] = df["Ganho (R$)"].map(brl)
        st.dataframe(df, hide_index=True, use_container_width=True)

    st.divider()
    col1, col2 = st.columns(2)
    periodo = col1.text_input("Período", value=datetime.now().strftime("%B %Y"))
    excel_rel = gerar_relatorio(concluidas, periodo)
    col2.download_button("⬇ Exportar relatório Excel", data=excel_rel,
                         file_name=f"relatorio_factoring_{periodo.replace(' ','_')}.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         use_container_width=True, type="primary")
