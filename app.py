"""Ponto de entrada — Cervejaria do Celso Gestao Interna."""

import streamlit as st

st.set_page_config(
    page_title="Cervejaria do Celso",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import logout, esta_autenticado, utilizador_actual, get_role, _verificar_credenciais, ADMIN_EMAIL, ADMIN_PW_HASH

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');
:root{--amber:#C8862A;--amber-l:#E8A844;--amber-d:#7A4F14;--bg:#0D0D0D;--s1:#161616;--s2:#1E1E1E;--s3:#252525;--bdr:#2A2A2A;--txt:#E8E0D5;--muted:#8A8070;--green:#4CAF7D;--red:#E05555;--r:10px}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;color:var(--txt)!important}
.stApp{background:var(--bg)!important;background-image:radial-gradient(ellipse at 20% 0%,rgba(200,134,42,.07) 0%,transparent 55%),radial-gradient(ellipse at 80% 100%,rgba(200,134,42,.04) 0%,transparent 45%)!important}
[data-testid="stSidebar"]{background:var(--s1)!important;border-right:1px solid var(--bdr)!important;min-width:235px!important;max-width:235px!important}
h1,h2,h3{font-family:'Playfair Display',serif!important;letter-spacing:-.01em!important}
h1{font-size:1.8rem!important;font-weight:700!important}
h2{font-size:1.25rem!important;font-weight:600!important}
[data-testid="stHeading"] h1{border-bottom:2px solid var(--amber-d)!important;padding-bottom:.5rem!important;margin-bottom:1.5rem!important}
[data-testid="stMetric"]{background:var(--s2)!important;border:1px solid var(--bdr)!important;border-radius:var(--r)!important;padding:1rem 1.25rem!important;transition:border-color .2s!important}
[data-testid="stMetric"]:hover{border-color:var(--amber-d)!important}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-size:.7rem!important;font-weight:500!important;text-transform:uppercase!important;letter-spacing:.09em!important}
[data-testid="stMetricValue"]{color:var(--amber-l)!important;font-size:1.55rem!important;font-weight:500!important;font-family:'DM Sans',sans-serif!important}
.stButton>button{background:linear-gradient(135deg,var(--amber) 0%,#A06820 100%)!important;color:#0D0D0D!important;border:none!important;border-radius:8px!important;font-weight:600!important;font-family:'DM Sans',sans-serif!important;transition:all .2s!important}
.stButton>button:hover{background:linear-gradient(135deg,var(--amber-l) 0%,var(--amber) 100%)!important;transform:translateY(-1px)!important;box-shadow:0 4px 16px rgba(200,134,42,.28)!important}
[data-testid="stFormSubmitButton"]>button{background:linear-gradient(135deg,var(--amber) 0%,#A06820 100%)!important;color:#0D0D0D!important;border:none!important;border-radius:8px!important;font-weight:700!important;width:100%!important}
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>div>textarea{background:var(--s2)!important;border:1px solid var(--bdr)!important;border-radius:8px!important;color:var(--txt)!important;transition:border-color .2s!important}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:var(--amber)!important;box-shadow:0 0 0 2px rgba(200,134,42,.15)!important}
.stTextInput label,.stNumberInput label,.stSelectbox label,.stTextArea label,.stDateInput label,.stTimeInput label,.stCheckbox label{color:var(--muted)!important;font-size:.75rem!important;font-weight:500!important;text-transform:uppercase!important;letter-spacing:.06em!important}
.stTabs [data-baseweb="tab-list"]{background:var(--s1)!important;border-bottom:1px solid var(--bdr)!important;gap:0!important}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--muted)!important;border-bottom:2px solid transparent!important;padding:.55rem 1.1rem!important;font-weight:500!important;font-size:.82rem!important;font-family:'DM Sans',sans-serif!important;transition:all .15s!important}
.stTabs [aria-selected="true"]{color:var(--amber)!important;border-bottom-color:var(--amber)!important}
[data-testid="stDataFrame"]{border:1px solid var(--bdr)!important;border-radius:var(--r)!important;overflow:hidden!important}
.stAlert{border-radius:var(--r)!important;font-size:.83rem!important}
[data-testid="stSuccess"]{background:rgba(76,175,125,.1)!important;border-color:rgba(76,175,125,.3)!important;color:#4CAF7D!important}
[data-testid="stWarning"]{background:rgba(200,134,42,.1)!important;border-color:rgba(200,134,42,.3)!important}
[data-testid="stError"]{background:rgba(224,85,85,.1)!important;border-color:rgba(224,85,85,.3)!important;color:#E05555!important}
[data-testid="stExpander"]{background:var(--s2)!important;border:1px solid var(--bdr)!important;border-radius:var(--r)!important}
[data-testid="stExpander"] summary{color:var(--muted)!important;font-size:.82rem!important;font-weight:500!important}
[data-testid="stExpander"] summary:hover{color:var(--amber)!important}
[data-testid="stForm"]{background:var(--s2)!important;border:1px solid var(--bdr)!important;border-radius:var(--r)!important;padding:1.2rem!important}
hr{border-color:var(--bdr)!important;opacity:1!important}
.stCaption{color:var(--muted)!important;font-size:.72rem!important}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--s1)}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--amber-d)}
.stProgress>div>div>div{background:linear-gradient(90deg,var(--amber-d),var(--amber))!important}
footer,#MainMenu{display:none!important}
header{visibility:hidden!important}
</style>
"""


def _placeholder_modulo(titulo, mensagem):
    st.title(titulo)
    st.info(f"Em construcao: {mensagem}")


def _pagina_login():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;padding:3rem 0 2rem;'>
        <span style='font-size:3.5rem;filter:drop-shadow(0 0 20px rgba(200,134,42,.4));'>🍺</span>
        <h1 style='font-family:Playfair Display,serif;font-size:2.4rem;font-weight:700;
                   color:#E8A844;letter-spacing:-.02em;margin:.6rem 0 .2rem;'>
            Cervejaria do Celso
        </h1>
        <p style='color:#8A8070;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;margin:0;'>
            Gestao Interna
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.expander("⚙️ Primeira instalacao?"):
            st.caption("Cria as worksheets no Google Sheet.")
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
                    st.success(f"Pronto! Login: {ADMIN_EMAIL} / celso2024")
                    url = get_spreadsheet_url()
                    if url: st.markdown(f"[Abrir Sheet]({url})")
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

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


# Autenticacao
if not esta_autenticado():
    _pagina_login()
    st.stop()

# Injectar CSS global apos login
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

u = utilizador_actual()
role = get_role()

MODULOS = {
    "📊  Dashboard":        {"key": "dashboard",        "roles": ["admin","dono","gerente"]},
    "🧾  Caixa Diaria":     {"key": "caixa_diaria",     "roles": ["admin","dono","gerente"]},
    "🍽️  Fichas Tecnicas":  {"key": "fichas_tecnicas",  "roles": ["admin","dono"]},
    "📉  Food Cost":        {"key": "food_cost",        "roles": ["admin","dono"]},
    "📦  Stocks":           {"key": "stocks",           "roles": ["admin","dono"]},
    "🚚  Fornecedores":     {"key": "fornecedores",     "roles": ["admin","dono"]},
    "🗺️  Menu Engineering": {"key": "menu_engineering", "roles": ["admin","dono"]},
    "👥  Pessoal":          {"key": "pessoal",          "roles": ["admin","dono"]},
    "📈  P&L Mensal":       {"key": "pnl",              "roles": ["admin","dono"]},
    "📥  Importar Winrest": {"key": "importer_winrest", "roles": ["admin"]},
}

modulos_visiveis = {n: i for n, i in MODULOS.items() if role in i["roles"]}

with st.sidebar:
    st.markdown(f"""
    <div style='padding:.2rem 0 1.4rem;border-bottom:1px solid #2A2A2A;margin-bottom:1.2rem;'>
        <div style='font-family:Playfair Display,serif;font-size:1.05rem;font-weight:700;
                    color:#E8A844;letter-spacing:-.01em;'>🍺 Celso Gestao</div>
        <div style='font-size:.68rem;color:#8A8070;margin-top:3px;
                    text-transform:uppercase;letter-spacing:.1em;'>
            {u.get('nome','Admin')} &middot; {role}
        </div>
    </div>
    """, unsafe_allow_html=True)

    pagina = st.radio("nav", list(modulos_visiveis.keys()), label_visibility="collapsed")

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    if st.button("🚪  Sair", use_container_width=True):
        logout()

chave = modulos_visiveis.get(pagina, {}).get("key", "dashboard")

try:
    mod = __import__(f"modules.{chave}", fromlist=["render"])
    mod.render()
except (ImportError, ModuleNotFoundError):
    _placeholder_modulo(pagina.strip(), "Em breve")
except Exception as e:
    st.error(f"Erro: {e}")
    import traceback
    st.code(traceback.format_exc())
