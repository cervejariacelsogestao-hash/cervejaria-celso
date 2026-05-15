"""
Autenticação — login por email + password (hash sha256).
Roles: admin, dono, gerente.
"""

import hashlib
import functools
import streamlit as st
from data.sheets_client import read_sheet


def _hash_password(password: str) -> str:
    """Devolve hash sha256 da password."""
    return hashlib.sha256(password.encode()).hexdigest()


def _verificar_credenciais(email: str, password: str) -> dict | None:
    """
    Verifica email e password contra a sheet 'users'.
    Devolve o utilizador (dict) se correcto, None caso contrário.
    """
    df = read_sheet("users")
    if df.empty:
        return None

    utilizador = df[
        (df["email"].str.lower() == email.lower()) &
        (df["activo"].astype(str).str.upper() == "TRUE")
    ]

    if utilizador.empty:
        return None

    u = utilizador.iloc[0].to_dict()

    # Verificar password — aceita hash ou texto simples (para setup inicial)
    password_hash = _hash_password(password)
    password_guardada = str(u.get("password_hash", ""))

    # Se não há password guardada, aceitar qualquer coisa em modo setup
    if not password_guardada:
        return u

    if password_guardada == password_hash or password_guardada == password:
        return u

    return None


def login_form():
    """
    Mostra o formulário de login.
    Guarda utilizador em st.session_state['user'] se autenticado.
    """
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <h1 style='color: #E8A427; font-size: 2rem;'>🍺 Cervejaria do Celso</h1>
            <p style='color: #888; font-size: 0.9rem;'>Gestão Interna</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="email@exemplo.com")
            password = st.text_input("Password", type="password")
            submeter = st.form_submit_button("Entrar", use_container_width=True)

        if submeter:
            if not email or not password:
                st.error("Preenche email e password.")
                return

            utilizador = _verificar_credenciais(email, password)
            if utilizador:
                st.session_state["user"] = utilizador
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Email ou password incorrectos.")


def logout():
    """Termina a sessão."""
    for key in ["user", "autenticado"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def utilizador_actual() -> dict | None:
    """Devolve o utilizador da sessão actual ou None."""
    return st.session_state.get("user")


def esta_autenticado() -> bool:
    """Verifica se há sessão activa."""
    return st.session_state.get("autenticado", False)


def get_role() -> str | None:
    """Devolve o role do utilizador actual."""
    u = utilizador_actual()
    if u:
        return str(u.get("role", "")).lower()
    return None


def require_role(*roles_permitidos: str):
    """
    Decorator que verifica se o utilizador tem um dos roles permitidos.
    Uso: @require_role("admin", "dono")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not esta_autenticado():
                st.error("Não autenticado.")
                st.stop()
            role_actual = get_role()
            if role_actual not in [r.lower() for r in roles_permitidos]:
                st.warning(
                    f"Sem permissão para aceder a esta secção. "
                    f"Necessário: {', '.join(roles_permitidos)}. "
                    f"O teu role: {role_actual}."
                )
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def pode_aceder(roles_permitidos: list[str]) -> bool:
    """Verifica inline se o utilizador actual pode aceder a algo."""
    return get_role() in [r.lower() for r in roles_permitidos]


def criar_admin_inicial():
    """
    Cria o utilizador admin inicial se a sheet users estiver vazia.
    Chamado automaticamente pelo app.py no primeiro arranque.
    """
    from data.sheets_client import write_row
    df = read_sheet("users")
    if not df.empty:
        return  # Já há utilizadores

    # Criar admin com password temporária (deve ser alterada)
    email_admin = st.secrets["app"]["admin_email"]
    password_temp = _hash_password("celso2024")

    write_row("users", [
        email_admin,
        "Admin",
        "admin",
        "TRUE",
        password_temp,
    ])
    st.info(
        f"Utilizador admin criado: {email_admin} / password: celso2024  "
        "**Altera a password depois do primeiro login.**"
    )
