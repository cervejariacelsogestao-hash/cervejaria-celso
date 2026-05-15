"""Autenticacao com roles e fallback bootstrap para admin inicial."""

import hashlib
import functools
import streamlit as st


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


ADMIN_EMAIL = "cervejariacelsogestao@gmail.com"
ADMIN_PW_HASH = _hash_password("celso2024")


def _verificar_credenciais(email: str, password: str):
    from data.sheets_client import read_sheet, write_row
    try:
        df = read_sheet("users")
    except Exception:
        df = None

    pw_hash = _hash_password(password)

    # Fallback bootstrap: se nao ha utilizadores, criar admin e autenticar
    if df is None or df.empty:
        if email.lower() == ADMIN_EMAIL and pw_hash == ADMIN_PW_HASH:
            try:
                write_row("users", [ADMIN_EMAIL, "Admin", "admin", "TRUE", ADMIN_PW_HASH])
            except Exception:
                pass
            return {"email": ADMIN_EMAIL, "nome": "Admin", "role": "admin", "activo": "TRUE"}
        return None

    utilizador = df[
        (df["email"].str.lower() == email.lower()) &
        (df["activo"].astype(str).str.upper() == "TRUE")
    ]

    if utilizador.empty:
        # Fallback: se e o admin e a sheet nao tem o admin, criar e autenticar
        if email.lower() == ADMIN_EMAIL and pw_hash == ADMIN_PW_HASH:
            try:
                write_row("users", [ADMIN_EMAIL, "Admin", "admin", "TRUE", ADMIN_PW_HASH])
            except Exception:
                pass
            return {"email": ADMIN_EMAIL, "nome": "Admin", "role": "admin", "activo": "TRUE"}
        return None

    u = utilizador.iloc[0].to_dict()
    pw_guardada = str(u.get("password_hash", ""))

    if not pw_guardada:
        return u
    if pw_guardada == pw_hash or pw_guardada == password:
        return u
    return None


def login_form():
    st.markdown("""
    <div style='text-align:center;padding:2rem 0 1rem 0;'>
      <h1 style='color:#E8A427;font-size:2rem;'>🍺 Cervejaria do Celso</h1>
      <p style='color:#888;font-size:0.9rem;'>Gestão Interna</p>
    </div>""", unsafe_allow_html=True)


def logout():
    for key in ["user", "autenticado"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def utilizador_actual():
    return st.session_state.get("user")


def esta_autenticado() -> bool:
    return st.session_state.get("autenticado", False)


def get_role():
    u = utilizador_actual()
    if u:
        return str(u.get("role", "")).lower()
    return None


def require_role(*roles_permitidos: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not esta_autenticado():
                st.error("Nao autenticado.")
                st.stop()
            role_actual = get_role()
            if role_actual not in [r.lower() for r in roles_permitidos]:
                st.warning(f"Sem permissao. Necessario: {', '.join(roles_permitidos)}.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def pode_aceder(roles_permitidos: list) -> bool:
    return get_role() in [r.lower() for r in roles_permitidos]


def criar_admin_inicial():
    from data.sheets_client import read_sheet, write_row
    try:
        df = read_sheet("users")
        if df.empty:
            write_row("users", [ADMIN_EMAIL, "Admin", "admin", "TRUE", ADMIN_PW_HASH])
    except Exception:
        pass
