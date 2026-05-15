"""Ponto de entrada da aplicacao Cervejaria do Celso."""

import streamlit as st

st.set_page_config(
    page_title="Cervejaria do Celso - Gestao",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import logout, esta_autenticado, utilizador_actual, get_role, _verificar_credenciais, ADMIN_EMAIL, ADMIN_PW_HASH

st.markdown("""
<style>
    [data-testid="stSidebar"] { min-width: 220px; max-width: 240px; }
    [data-testid="stMetricValue"] { color: #E8A427 !important; font-size: 1.6rem !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def _placeholder_modulo(titulo, mensagem):
    st.title(titulo)
    st.info(f"Modulo em construcao: {mensagem}")


def _pagina_login():
    st.markdown("""<div style='text-align:center;padding:2rem 0 1rem 0;'>
      <h1 style='color:#E8A427;font-size:2rem;'>🍺 Cervejaria do Celso</h1>
      <p style='color:#888;font-size:0.9rem;'>Gestao Interna</p>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.expander("⚙️ Primeira instalacao? Clica aqui"):
            st.caption("Cria as worksheets no Google Sheet. So e preciso uma vez.")
            if st.button("🚀 Inicializar Base de Dados", type="primary", key="btn_setup"):
                try:
                    from data.schema import init_database, get_spreadsheet_url
                    from data.sheets_client import read_sheet, write_row
                    with st.spinner("A criar worksheets..."):
                        init_database(verbose=True)
                    df = read_sheet("users")
                    admin_emails = df["email"].str.lower().tolist() if not df.empty and "email" in df.columns else []
                    if ADMIN_EMAIL not in admin_emails:
                        write_row("users", [ADMIN_EMAIL, "Admin", "admin", "TRUE", ADMIN_PW_HASH])
                        st.write("  Admin criado")
                    st.success(f"Pronto! Login: {ADMIN_EMAIL} / celso2024")
                    url = get_spreadsheet_url()
                    if url: st.markdown(f"[Abrir Sheet]({url})")
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.divider()

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="email@exemplo.com")
            password = st.text_input("Password", type="password")
            submeter = st.form_submit_button("Entrar", use_container_width=True)

        if submeter:
            if not email or not password:
                st.error("Preenche email e password.")
            else:
                utilizador = _verificar_credenciais(email, password)
                if utilizador:
                    st.session_state["user"] = utilizador
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Email ou password incorrectos.")


if not esta_autenticado():
    _pagina_login()
    st.stop()

u = utilizador_actual()
role = get_role()

MODULOS = {
    "📊 Dashboard":     {"key": "dashboard",        "roles": ["admin","dono","gerente"]},
    "🧾 Caixa Diaria":  {"key": "caixa_diaria",     "roles": ["admin","dono","gerente"]},
    "Fichas Tecnicas":  {"key": "fichas_tecnicas",  "roles": ["admin","dono"]},
    "📉 Food Cost":     {"key": "food_cost",        "roles": ["admin","dono"]},
    "📦 Stocks":        {"key": "stocks",           "roles": ["admin","dono"]},
    "Fornecedores":     {"key": "fornecedores",     "roles": ["admin","dono"]},
    "Menu Engineering": {"key": "menu_engineering", "roles": ["admin","dono"]},
    "👥 Pessoal":       {"key": "pessoal",          "roles": ["admin","dono"]},
    "📈 P&L Mensal":    {"key": "pnl",              "roles": ["admin","dono"]},
    "Importar Winrest": {"key": "importer_winrest", "roles": ["admin"]},
}

modulos_visiveis = {n: i for n, i in MODULOS.items() if role in i["roles"]}

with st.sidebar:
    st.markdown("### 🍺 Celso Gestao")
    st.caption(f"👤 {u.get('nome','Utilizador')} ({role})")
    st.divider()
    pagina = st.radio("Navegacao", list(modulos_visiveis.keys()), label_visibility="collapsed")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        logout()

chave = modulos_visiveis.get(pagina, {}).get("key", "dashboard")

mods = {"dashboard":"📊 Dashboard","caixa_diaria":"🧾 Caixa Diaria","fichas_tecnicas":"Fichas Tecnicas","food_cost":"📉 Food Cost","stocks":"📦 Stocks","fornecedores":"Fornecedores","menu_engineering":"Menu Engineering","pessoal":"👥 Pessoal","pnl":"📈 P&L Mensal","importer_winrest":"Importar Winrest"}
sprints = {"dashboard":"2","caixa_diaria":"2","fichas_tecnicas":"3","food_cost":"3","stocks":"5","fornecedores":"5","menu_engineering":"4","pessoal":"6","pnl":"6","importer_winrest":"4"}

try:
    mod = __import__(f"modules.{chave}", fromlist=["render"])
    mod.render()
except (ImportError, ModuleNotFoundError):
    _placeholder_modulo(mods.get(chave, chave), f"Sprint {sprints.get(chave,'?')}")
