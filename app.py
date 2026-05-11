import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
import hashlib
import base64
from pathlib import Path

from db import (
    load_negs, save_neg, update_neg, delete_neg,
    load_fornecedores, save_fornecedor, update_fornecedor, delete_fornecedor,
    calcular_ganho, alcada_status, novo_id,
    STATUS_LABELS, APPROVERS
)
from excel import gerar_historico, gerar_relatorio

st.set_page_config(
    page_title="Grupo LLE — Factoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Logo ───────────────────────────────────────────────────────────────────────
def get_logo_b64():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        return base64.b64encode(logo_path.read_bytes()).decode()
    return None

LOGO_B64 = get_logo_b64()

# ── Cores ──────────────────────────────────────────────────────────────────────
AMARELO  = "#FAC319"
VERDE    = "#0F8C3B"
AZUL     = "#007FE0"
AZUL_ESC = "#041747"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
[data-testid="stSidebar"] {{
    min-width: 240px !important; max-width: 240px !important;
    background: {AZUL_ESC} !important;
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {{ color: rgba(255,255,255,0.85) !important; }}
[data-testid="stSidebar"] .stButton button {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #fff !important;
    text-align: left !important;
    border-radius: 7px !important;
    margin-bottom: 3px !important;
    font-size: 13px !important;
    padding: 8px 14px !important;
}}
[data-testid="stSidebar"] .stButton button:hover {{
    background: rgba(250,195,25,0.15) !important;
    border-color: {AMARELO} !important;
}}
[data-testid="stSidebar"] [data-testid="baseButton-primary"] {{
    background: {AMARELO} !important;
    color: {AZUL_ESC} !important;
    border: none !important;
    font-weight: 700 !important;
}}
[data-testid="baseButton-primary"] {{
    background: {AZUL_ESC} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 7px !important;
}}
[data-testid="baseButton-primary"]:hover {{
    background: {AZUL} !important;
}}
[data-testid="metric-container"] {{
    background: #f4f7fc;
    border-radius: 10px;
    padding: 14px 18px;
    border-left: 4px solid {AMARELO};
    box-shadow: 0 1px 4px rgba(4,23,71,0.07);
}}
h1 {{ color: {AZUL_ESC} !important; font-weight: 700 !important; }}
h2 {{ color: {AZUL_ESC} !important; font-weight: 600 !important; }}
h3 {{ color: {AZUL_ESC} !important; }}
.alcada-ok   {{ background:#edf7f1; color:#0a5c31; padding:12px 16px; border-radius:8px; font-size:13px; margin-bottom:12px; border-left:4px solid {VERDE}; }}
.alcada-warn {{ background:#fef9e7; color:#7d5c00; padding:12px 16px; border-radius:8px; font-size:13px; margin-bottom:12px; border-left:4px solid {AMARELO}; }}
.alcada-err  {{ background:#fdf0f0; color:#8b1a1a; padding:12px 16px; border-radius:8px; font-size:13px; margin-bottom:12px; border-left:4px solid #dc3545; }}
.timeline-item {{ border-left:3px solid {AMARELO}; padding:4px 0 10px 16px; margin-left:8px; font-size:13px; }}
.hbar {{ background:{AZUL_ESC}; padding:14px 22px; border-radius:10px; margin-bottom:22px; display:flex; align-items:center; gap:16px; }}
.hbar-title {{ color:#fff; font-size:20px; font-weight:700; }}
.hbar-sub {{ color:{AMARELO}; font-size:12px; margin-top:2px; }}
[data-testid="stExpander"] {{ border:1px solid #dde3ef !important; border-radius:9px !important; }}
hr {{ border-color:{AMARELO} !important; opacity:.25; }}
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def brl(v):
    return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def _hash(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def logo_img(height=36):
    if LOGO_B64:
        return f'<img src="data:image/png;base64,{LOGO_B64}" style="height:{height}px;" />'
    return f'<span style="color:#fff;font-weight:700;font-size:16px;">GRUPO LLE</span>'

def page_header(titulo, subtitulo=""):
    st.markdown(
        f'<div class="hbar">{logo_img(38)}'
        f'<div><div class="hbar-title">{titulo}</div>'
        f'{"<div class=hbar-sub>" + subtitulo + "</div>" if subtitulo else ""}</div></div>',
        unsafe_allow_html=True
    )

# ── Login ──────────────────────────────────────────────────────────────────────
def check_login(usuario, senha):
    usuarios = st.secrets.get("usuarios", {})
    h = usuarios.get(usuario)
    return h and _hash(senha) == h

def tela_login():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        if LOGO_B64:
            st.markdown(
                f'<div style="background:{AZUL_ESC};padding:28px 24px;border-radius:12px 12px 0 0;text-align:center;">'
                f'<img src="data:image/png;base64,{LOGO_B64}" style="max-width:210px;width:100%;" />'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown(
            f'<div style="background:#f4f7fc;border:1px solid #dde3ef;border-top:none;border-radius:0 0 12px 12px;padding:24px 24px 28px;">'
            f'<p style="text-align:center;color:#666;font-size:13px;margin:0 0 20px;">Negociação com Fornecedores</p>',
            unsafe_allow_html=True
        )
        with st.form("login_form"):
            usuario = st.selectbox("Usuário", ["Ana Lima", "Alexandre Vieira", "Beatriz Esteves", "Claudia Passos"])
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
    st.stop()

# ── Session state ──────────────────────────────────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"
if "negs" not in st.session_state:
    st.session_state.negs = load_negs()
if "fornecedores" not in st.session_state:
    st.session_state.fornecedores = load_fornecedores()

def reload():
    st.session_state.negs = load_negs()
    st.session_state.fornecedores = load_fornecedores()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="text-align:center;padding:18px 8px 10px;">'
        f'{logo_img(52)}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<p style="text-align:center;color:{AMARELO};font-size:11px;letter-spacing:.06em;margin:-4px 0 14px;text-transform:uppercase;">Negociação com Fornecedores</p>',
        unsafe_allow_html=True
    )
    st.divider()

    pendentes = sum(1 for n in st.session_state.negs if n["status"] == "pendente")
    label_aprov = f"🔴  Aprovações  ({pendentes})" if pendentes > 0 else "✅  Aprovações"

    menu = [
        ("📊  Dashboard",       "Dashboard"),
        ("➕  Nova negociação",  "Nova negociação"),
        ("📋  Negociações",      "Negociações"),
        (label_aprov,           "Aprovações"),
        ("🏢  Fornecedores",     "Fornecedores"),
        ("📈  Relatórios",       "Relatórios"),
    ]
    for label, key in menu:
        ativo = st.session_state.pagina == key
        if st.button(label, use_container_width=True, type="primary" if ativo else "secondary"):
            st.session_state.pagina = key
            reload()
            st.rerun()

    st.divider()
    st.markdown(f'<p style="font-size:11px;color:rgba(255,255,255,.5);margin-bottom:2px;text-transform:uppercase;letter-spacing:.05em;">Usuário</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:14px;font-weight:600;color:#fff;margin-bottom:12px;">👤 {st.session_state.usuario}</p>', unsafe_allow_html=True)
    if st.button("🚪  Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

pagina = st.session_state.pagina
negs = st.session_state.negs
fornecedores = st.session_state.fornecedores

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "Dashboard":
    page_header("Dashboard", "Visão geral das negociações")
    concluidas = [n for n in negs if n["status"] in ("concluida", "aprovada")]
    ganho_total = sum(float(n["ganho"]) for n in concluidas)
    taxa_media = (sum(float(n["taxa"]) for n in concluidas) / len(concluidas)) if concluidas else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Ganho total", brl(ganho_total))
    c2.metric("📋 Negociações", len(negs))
    c3.metric("📊 Taxa média", f"{taxa_media:.2f}%".replace(".",",") if taxa_media else "—")
    c4.metric("⏳ Aguardando aprovação", pendentes)

    st.divider()
    st.subheader("Últimas negociações")
    if not negs:
        st.info("Nenhuma negociação registrada ainda. Use **➕ Nova negociação** para começar.")
    else:
        rows = [{
            "Fornecedor": n["fornecedor"],
            "NF(s)": ", ".join(x["nf"] for x in (n["notas"] if isinstance(n["notas"], list) else [])),
            "Valor total": brl(n["valor_total"]),
            "Taxa": f"{float(n['taxa']):.2f}%".replace(".",","),
            "Ganho": brl(n["ganho"]),
            "Data": datetime.fromisoformat(n["criado_em"]).astimezone(__import__('datetime').timezone(__import__('datetime').timedelta(hours=-3))).strftime("%d/%m/%Y") if n.get("criado_em") else "—",
            "Status": STATUS_LABELS.get(n["status"], n["status"]),
        } for n in negs[:10]]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# NOVA NEGOCIAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Nova negociação":
    page_header("Nova negociação", "Registre a solicitação de adiantamento")

    forn_nomes = ["— Selecione o fornecedor —"] + [f["nome"] for f in fornecedores]
    forn_map = {f["nome"]: f for f in fornecedores}

    st.subheader("Fornecedor")
    col1, col2 = st.columns(2)
    forn_selecionado = col1.selectbox("Fornecedor", forn_nomes, label_visibility="collapsed")
    cnpj_auto = forn_map[forn_selecionado]["cnpj"] if forn_selecionado != "— Selecione o fornecedor —" else ""
    col2.text_input("CNPJ (automático)", value=cnpj_auto, disabled=True)

    if forn_selecionado == "— Selecione o fornecedor —":
        st.info("💡 Selecione um fornecedor. Não encontrou? Cadastre em **🏢 Fornecedores**.")

    # Notas fiscais — fora do form para calcular em tempo real
    st.subheader("Notas fiscais")
    num_notas = st.number_input("Quantidade de notas", min_value=1, max_value=20, value=1, step=1, key="num_notas")
    notas_input = []
    for i in range(int(num_notas)):
        st.markdown(f"**Nota {i+1}**")
        c1, c2, c3, c4 = st.columns(4)
        nf      = c1.text_input("Número NF *",   key=f"nf_{i}",    placeholder="NF-0000")
        venc    = c2.date_input("Vencimento *",   key=f"venc_{i}",  value=date.today(),
                                format="DD/MM/YYYY")
        valor   = c3.number_input("Valor (R$) *", key=f"valor_{i}", min_value=0.0, step=100.0, format="%.2f")
        desdobr = c4.text_input("Desdobramento",  key=f"desdobr_{i}", placeholder="ex: 1/3")
        notas_input.append({"id": str(uuid.uuid4())[:8], "nf": nf,
                            "vencimento": venc.strftime("%d/%m/%Y"), "valor": valor, "desdobramento": desdobr})

    valor_total = sum(float(n["valor"]) for n in notas_input)
    if valor_total > 0:
        st.markdown(f"**Total das notas: {brl(valor_total)}**")

    # Taxa e cálculos — fora do form para atualizar em tempo real
    st.subheader("Taxa negociada")
    taxa = st.slider("Taxa (%)", min_value=0.5, max_value=4.0, value=2.5, step=0.1,
                     format="%.1f%%", key="taxa_slider")
    ganho = calcular_ganho(valor_total, taxa)
    valor_pago = valor_total - ganho

    alc = alcada_status(taxa)
    if alc == "ok":
        st.markdown('<div class="alcada-ok">✅ <strong>Dentro da alçada (2% – 3%)</strong> — você pode concluir sem aprovação adicional.</div>', unsafe_allow_html=True)
    elif alc == "above":
        st.markdown('<div class="alcada-warn">⚠️ <strong>Acima do teto (3%)</strong> — favorável para nós, verifique se está correto.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alcada-err">🔒 <strong>Abaixo da alçada mínima (2%)</strong> — será enviado para aprovação automaticamente.</div>', unsafe_allow_html=True)

    col_calc, _ = st.columns([1, 3])
    calcular = col_calc.button("🔢 Calcular", use_container_width=True)

    if calcular or st.session_state.get("mostrar_calculo"):
        st.session_state["mostrar_calculo"] = True
        st.markdown("---")
        st.markdown("#### 📊 Resultado do cálculo")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Ganho estimado", brl(ganho))
        c2.metric("💳 Valor a pagar ao fornecedor", brl(valor_pago))
        c3.metric("📊 Desconto aplicado", f"{taxa:.1f}%".replace(".",","))
        st.markdown("---")

    obs = st.text_area("Observações / justificativa", placeholder="Contexto da negociação, posição do fornecedor...",
                       key="obs_neg")

    if st.button("💾 Registrar negociação", type="primary", use_container_width=True):
        erros = []
        if forn_selecionado == "— Selecione o fornecedor —": erros.append("Selecione um fornecedor.")
        for i, n in enumerate(notas_input):
            if not n["nf"].strip(): erros.append(f"Nota {i+1}: número da NF obrigatório.")
            if float(n["valor"]) <= 0: erros.append(f"Nota {i+1}: valor deve ser maior que zero.")
        if erros:
            for e in erros: st.error(e)
        else:
            from datetime import timezone, timedelta
            tz_br = timezone(timedelta(hours=-3))
            now = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M")
            now_iso = datetime.now(tz_br).isoformat()
            timeline = [{"at": now_iso, "msg": f"Registrada por {st.session_state.usuario}. Taxa: {taxa:.2f}%"}]
            if alc == "below":
                timeline.append({"at": now_iso, "msg": "Enviado para aprovação (taxa abaixo de 2%)."})
            neg = {
                "id": novo_id(), "fornecedor": forn_selecionado, "cnpj": cnpj_auto,
                "notas": notas_input, "taxa": taxa, "obs": obs.strip(),
                "valor_total": valor_total, "ganho": ganho, "valor_pago": valor_pago,
                "status": "pendente" if alc == "below" else "concluida",
                "criado_em": now_iso, "criado_por": st.session_state.usuario,
                "aprovador_id": None, "decisao_em": None, "timeline": timeline,
            }
            save_neg(neg)
            reload()
            st.session_state["mostrar_calculo"] = False
            st.success("✅ Negociação registrada!" + (" Enviada para aprovação." if alc == "below" else ""))
            st.balloons()

# ══════════════════════════════════════════════════════════════════════════════
# NEGOCIAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Negociações":
    page_header("Negociações", "Histórico completo")
    col1, col2, col3 = st.columns([3, 1, 1])
    busca = col1.text_input("Buscar", label_visibility="collapsed", placeholder="🔍  Buscar fornecedor ou NF...")
    filtro = col2.selectbox("Status", ["Todos","concluida","aprovada","pendente","recusada"], label_visibility="collapsed")
    col3.download_button("⬇ Excel", data=gerar_historico(negs),
                         file_name=f"historico_{datetime.now().strftime('%Y%m%d')}.xlsx",
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
            icon = {"concluida":"✅","aprovada":"✅","pendente":"⏳","recusada":"❌"}.get(n["status"],"•")
            with st.expander(f"{icon} **{n['fornecedor']}** — {', '.join(x['nf'] for x in notas_list)} — {brl(n['valor_total'])} — {STATUS_LABELS.get(n['status'], n['status'])}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Valor total", brl(n["valor_total"]))
                c2.metric("Taxa", f"{float(n['taxa']):.2f}%".replace(".",","))
                c3.metric("Ganho", brl(n["ganho"]))
                c4.metric("Criado por", n.get("criado_por","—"))
                if notas_list:
                    st.dataframe(pd.DataFrame([{"NF": x["nf"], "Vencimento": x["vencimento"],
                        "Valor": brl(x["valor"]), "Desdobramento": x.get("desdobramento","")}
                        for x in notas_list]), hide_index=True, use_container_width=True)
                if n.get("obs"): st.info(f"📝 {n['obs']}")
                for t in n.get("timeline", []):
                    try:
                        dt_obj = datetime.fromisoformat(t["at"])
                        from datetime import timezone, timedelta
                        dt_obj = dt_obj.astimezone(timezone(timedelta(hours=-3)))
                        dt = dt_obj.strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        dt = t["at"][:16]
                    st.markdown(f'<div class="timeline-item">🔵 <strong>{dt}</strong> — {t["msg"]}</div>', unsafe_allow_html=True)
                if st.button("🗑 Excluir", key=f"del_{n['id']}"):
                    delete_neg(n["id"]); reload(); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# APROVAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Aprovações":
    page_header("Aprovações pendentes", "Negociações abaixo de 2% aguardando autorização")
    pendentes_list = [n for n in negs if n["status"] == "pendente"]
    if not pendentes_list:
        st.success("✅ Tudo em dia! Não há aprovações pendentes.")
    else:
        for n in pendentes_list:
            notas_list = n["notas"] if isinstance(n["notas"], list) else []
            with st.container(border=True):
                c1, c2 = st.columns([3,1])
                c1.markdown(f"### {n['fornecedor']}")
                c1.caption(f"NF(s): {', '.join(x['nf'] for x in notas_list)} · {n.get('criado_por','—')} · {datetime.fromisoformat(n['criado_em']).strftime('%d/%m/%Y %H:%M')}")
                c2.error(f"⚠ {float(n['taxa']):.2f}% — abaixo da alçada".replace(".",","))
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Valor total", brl(n["valor_total"]))
                c2.metric(f"Ganho c/ {float(n['taxa']):.1f}%".replace(".",","), brl(n["ganho"]))
                ganho_2 = float(n["valor_total"]) * 0.02
                c3.metric("Ganho c/ 2,0%", brl(ganho_2))
                c4.metric("Diferença", f"- {brl(ganho_2 - float(n['ganho']))}")
                if n.get("obs"): st.info(f"📝 {n['obs']}")
                ca, cr, _ = st.columns([1, 1, 4])
                if ca.button("✅ Aprovar", key=f"aprov_{n['id']}", type="primary"):
                    from datetime import timezone, timedelta
                    now = datetime.now(timezone(timedelta(hours=-3))).isoformat()
                    tl = (n.get("timeline") or []) + [{"at": now, "msg": f"✓ Aprovada por {st.session_state.usuario}"}]
                    update_neg(n["id"], {"status": "aprovada", "decisao_em": now, "aprovador_id": st.session_state.usuario, "timeline": tl})
                    reload(); st.success("Aprovada!"); st.rerun()
                if cr.button("❌ Recusar", key=f"recus_{n['id']}"):
                    from datetime import timezone, timedelta
                    now = datetime.now(timezone(timedelta(hours=-3))).isoformat()
                    tl = (n.get("timeline") or []) + [{"at": now, "msg": f"✗ Recusada por {st.session_state.usuario}"}]
                    update_neg(n["id"], {"status": "recusada", "decisao_em": now, "aprovador_id": st.session_state.usuario, "timeline": tl})
                    reload(); st.warning("Recusada."); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FORNECEDORES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Fornecedores":
    page_header("Fornecedores", "Gerencie os fornecedores cadastrados")
    with st.expander("➕ Cadastrar novo fornecedor", expanded=len(fornecedores) == 0):
        with st.form("form_forn", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nome    = c1.text_input("Razão social / Nome *", placeholder="Ex: Gráfica Alfa LTDA")
            cnpj    = c2.text_input("CNPJ *", placeholder="00.000.000/0000-00")
            c3, c4  = st.columns(2)
            contato = c3.text_input("Contato (opcional)", placeholder="Nome do responsável")
            obs_f   = c4.text_input("Observações (opcional)")
            if st.form_submit_button("💾 Cadastrar", type="primary", use_container_width=True):
                if not nome.strip() or not cnpj.strip():
                    st.error("Nome e CNPJ são obrigatórios.")
                else:
                    save_fornecedor(nome, cnpj, contato, obs_f)
                    reload(); st.success(f"✅ {nome} cadastrado!"); st.rerun()
    st.divider()
    if not fornecedores:
        st.info("Nenhum fornecedor cadastrado ainda.")
    else:
        busca_f = st.text_input("Buscar", placeholder="🔍  Nome ou CNPJ...", label_visibility="collapsed")
        lista = [f for f in fornecedores if not busca_f or busca_f.lower() in f["nome"].lower() or busca_f in f.get("cnpj","")]
        st.caption(f"{len(lista)} fornecedor(es)")
        for f in lista:
            with st.expander(f"🏢 **{f['nome']}** — {f.get('cnpj','—')}"):
                c1, c2 = st.columns(2)
                nn = c1.text_input("Nome",    value=f["nome"],           key=f"fn_{f['id']}")
                nc = c2.text_input("CNPJ",    value=f.get("cnpj",""),    key=f"fc_{f['id']}")
                c3, c4 = st.columns(2)
                nct = c3.text_input("Contato",value=f.get("contato",""),key=f"fct_{f['id']}")
                no  = c4.text_input("Obs",    value=f.get("obs",""),    key=f"fo_{f['id']}")
                cb, cd, _ = st.columns([1, 1, 4])
                if cb.button("💾 Salvar", key=f"fs_{f['id']}", type="primary"):
                    update_fornecedor(f["id"], {"nome": nn, "cnpj": nc, "contato": nct, "obs": no})
                    reload(); st.success("Atualizado!"); st.rerun()
                if cd.button("🗑 Excluir", key=f"fd_{f['id']}"):
                    delete_fornecedor(f["id"]); reload(); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RELATÓRIOS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Relatórios":
    page_header("Relatórios", "Resultados para a diretoria")
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
    col2.download_button("⬇ Exportar relatório Excel", data=gerar_relatorio(concluidas, periodo),
                         file_name=f"relatorio_factoring_{periodo.replace(' ','_')}.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         use_container_width=True, type="primary")
