"""
Ponto de entrada da aplicação Cervejaria do Celso — Gestão Interna.
"""

import streamlit as st

st.set_page_config(
    page_title="Cervejaria do Celso — Gestão",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import login_form, logout, esta_autenticado, utilizador_actual, get_role, criar_admin_inicial

st.markdown("""
<style>
    [data-testid="stSidebar"] { min-width: 220px; max-width: 240px; }
    [data-testid="stMetricValue"] { color: #E8A427 !important; font-size: 1.6rem !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def _placeholder_modulo(titulo: str, mensagem: str):
    """Placeholder para módulos ainda não construídos."""
    st.title(titulo)
    st.info(f"🔧 {mensagem}")
    st.caption("Módulos construídos por sprints — em breve disponível.")


# -------------------------------------------------------------------
# Autenticação
# -------------------------------------------------------------------
if not esta_autenticado():
    login_form()
    st.stop()

criar_admin_inicial()

u = utilizador_actual()
role = get_role()

# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------
MODULOS = {
    "📊 Dashboard":         {"key": "dashboard",        "roles": ["admin","dono","gerente"]},
    "🧾 Caixa Diária":      {"key": "caixa_diaria",     "roles": ["admin","dono","gerente"]},
    "🍽️ Fichas Técnicas":   {"key": "fichas_tecnicas",  "roles": ["admin","dono"]},
    "📉 Food Cost":         {"key": "food_cost",        "roles": ["admin","dono"]},
    "📦 Stocks":            {"key": "stocks",           "roles": ["admin","dono"]},
    "🚚 Fornecedores":      {"key": "fornecedores",     "roles": ["admin","dono"]},
    "🗺️ Menu Engineering":  {"key": "menu_engineering", "roles": ["admin","dono"]},
    "👥 Pessoal":           {"key": "pessoal",          "roles": ["admin","dono"]},
    "📈 P&L Mensal":        {"key": "pnl",              "roles": ["admin","dono"]},
    "📥 Importar Winrest":  {"key": "importer_winrest", "roles": ["admin"]},
}

modulos_visiveis = {n: i for n, i in MODULOS.items() if role in i["roles"]}

with st.sidebar:
    st.markdown("### 🍺 Celso Gestão")
    st.caption(f"👤 {u.get('nome','Utilizador')} ({role})")
    st.divider()

    pagina = st.radio("Navegação", list(modulos_visiveis.keys()), label_visibility="collapsed")

    st.divider()
    if role == "admin":
        if st.button("⚙️ Setup Base de Dados", use_container_width=True):
            st.session_state["pagina_override"] = "setup"
    if st.button("🚪 Sair", use_container_width=True):
        logout()

# Override
if st.session_state.get("pagina_override") == "setup":
    pagina = "__setup__"
    st.session_state.pop("pagina_override", None)

# -------------------------------------------------------------------
# Roteamento
# -------------------------------------------------------------------
chave = modulos_visiveis.get(pagina, {}).get("key", "dashboard")

if pagina == "__setup__":
    st.title("⚙️ Setup — Inicializar Base de Dados")
    st.warning("Cria o Google Sheet com todas as worksheets. Seguro de correr mesmo que já exista.")
    if st.button("🚀 Inicializar Base de Dados", type="primary"):
        from data.schema import init_database, get_spreadsheet_url
        with st.spinner("A criar worksheets..."):
            init_database(verbose=True)
        st.success("✅ Concluído!")
        url = get_spreadsheet_url()
        if url:
            st.markdown(f"[📊 Abrir Google Sheet]({url})")

elif chave == "dashboard":
    try:
        from modules.dashboard import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("📊 Dashboard", "Módulo em construção — Sprint 2")

elif chave == "caixa_diaria":
    try:
        from modules.caixa_diaria import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("🧾 Caixa Diária", "Módulo em construção — Sprint 2")

elif chave == "fichas_tecnicas":
    try:
        from modules.fichas_tecnicas import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("🍽️ Fichas Técnicas", "Módulo em construção — Sprint 3")

elif chave == "food_cost":
    try:
        from modules.food_cost import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("📉 Food Cost", "Módulo em construção — Sprint 3")

elif chave == "stocks":
    try:
        from modules.stocks import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("📦 Stocks", "Módulo em construção — Sprint 5")

elif chave == "fornecedores":
    try:
        from modules.fornecedores import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("🚚 Fornecedores", "Módulo em construção — Sprint 5")

elif chave == "menu_engineering":
    try:
        from modules.menu_engineering import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("🗺️ Menu Engineering", "Módulo em construção — Sprint 4")

elif chave == "pessoal":
    try:
        from modules.pessoal import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("👥 Pessoal", "Módulo em construção — Sprint 6")

elif chave == "pnl":
    try:
        from modules.pnl import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("📈 P&L Mensal", "Módulo em construção — Sprint 6")

elif chave == "importer_winrest":
    try:
        from modules.importer_winrest import render; render()
    except (ImportError, ModuleNotFoundError):
        _placeholder_modulo("📥 Importar Winrest", "Módulo em construção — Sprint 4")
