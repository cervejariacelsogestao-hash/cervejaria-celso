"""Ponto de entrada da aplicação Cervejaria do Celso — Gestão Interna."""

import streamlit as st

st.set_page_config(
    page_title="Cervejaria do Celso — Gestão",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import logout, esta_autenticado, utilizador_actual, get_role

st.markdown("""
<style>
    [data-testid="stSidebar"] { min-width: 220px; max-width: 240px; }
    [data-testid="stMetricValue"] { color: #E8A427 !important; font-size: 1.6rem !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def _placeholder_modulo(titulo: str, mensagem: str):
    st.title(titulo)
    st.info(f"🔧 {mensagem}")
    st.caption("Módulos construídos por sprints — em breve disponível.")


def _pagina_login():
    """Página de login com botão de setup integrado."""
    st.markdown("""
    <div style='text-align:center;padding:2rem 0 1rem 0;'>
      <h1 style='color:#E8A427;font-size:2rem;'>🍺 Cervejaria do Celso</h1>
      <p style='color:#888;font-size:0.9rem;'>Gestão Interna</p>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Botão de setup — SEMPRE visível, acima do login
        with st.expander("⚙️ Primeira instalação? Clica aqui"):
            st.caption("Cria o Google Sheet com todas as worksheets. Só precisa de ser feito uma vez.")
            if st.button("🚀 Inicializar Base de Dados", type="primary", key="btn_setup"):
                try:
                    from data.schema import init_database, get_spreadsheet_url
                    import hashlib
                    from data.sheets_client import write_row, read_sheet
                    with st.spinner("A criar Google Sheet..."):
                        init_database(verbose=True)
                    # Criar admin inicial
                    df = read_sheet("users")
                    if df.empty:
                        pw = hashlib.sha256("celso2024".encode()).hexdigest()
                        write_row("users", ["cervejariacelsogestao@gmail.com", "Admin", "admin", "TRUE", pw])
                    st.success("✅ Pronto! Faz login com:\n\n📧 cervejariacelsogestao@gmail.com\n\n🔑 celso2024")
                    url = get_spreadsheet_url()
                    if url:
                        st.markdown(f"[📊 Abrir Google Sheet]({url})")
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.divider()

        # Formulário de login
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="email@exemplo.com")
            password = st.text_input("Password", type="password")
            submeter = st.form_submit_button("Entrar", use_container_width=True)

        if submeter:
            if not email or not password:
                st.error("Preenche email e password.")
                return
            try:
                import hashlib
                from data.sheets_client import read_sheet
                df = read_sheet("users")
                if df.empty:
                    st.error("Base de dados não inicializada. Usa o botão de setup acima.")
                    return
                pw_hash = hashlib.sha256(password.encode()).hexdigest()
                utilizador = df[
                    (df["email"].str.lower() == email.lower()) &
                    (df["activo"].astype(str).str.upper() == "TRUE")
                ]
                if utilizador.empty:
                    st.error("Email ou password incorrectos.")
                    return
                u = utilizador.iloc[0].to_dict()
                pw_guardada = str(u.get("password_hash", ""))
                if pw_guardada == pw_hash or pw_guardada == password or not pw_guardada:
                    st.session_state["user"] = u
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Email ou password incorrectos.")
            except Exception as e:
                st.error(f"Erro ao ligar à base de dados: {e}")


# -------------------------------------------------------------------
# Autenticação
# -------------------------------------------------------------------
if not esta_autenticado():
    _pagina_login()
    st.stop()

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
    if st.button("🚪 Sair", use_container_width=True):
        logout()

chave = modulos_visiveis.get(pagina, {}).get("key", "dashboard")

if chave == "dashboard":
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
