"""Cliente Google Sheets com cache e operacoes CRUD."""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = "16PwHAXMd_4khP1kAZ2lfxEwd_d8BDM3WY2yYixJG9Lw"


def _get_client():
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(credenciais)


def _get_sheet(nome_sheet):
    cliente = _get_client()
    try:
        spreadsheet = cliente.open_by_key(SPREADSHEET_ID)
        return spreadsheet.worksheet(nome_sheet)
    except gspread.WorksheetNotFound:
        st.error(f"Worksheet '{nome_sheet}' nao existe. Corre init_database() primeiro.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao abrir spreadsheet: {e}")
        st.stop()


@st.cache_data(ttl=60)
def read_sheet(nome_sheet):
    try:
        sheet = _get_sheet(nome_sheet)
        dados = sheet.get_all_records(default_blank="")
        if not dados:
            cabecalhos = sheet.row_values(1)
            return pd.DataFrame(columns=cabecalhos)
        return pd.DataFrame(dados)
    except Exception as e:
        st.warning(f"Nao foi possivel ler '{nome_sheet}': {e}")
        return pd.DataFrame()


def write_row(nome_sheet, linha):
    try:
        sheet = _get_sheet(nome_sheet)
        sheet.append_row(linha, value_input_option="USER_ENTERED")
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao escrever em '{nome_sheet}': {e}")
        return False


def update_row(nome_sheet, row_index, dados):
    try:
        sheet = _get_sheet(nome_sheet)
        linha_real = row_index + 2
        sheet.update(f"A{linha_real}", [dados])
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao actualizar linha {row_index} em '{nome_sheet}': {e}")
        return False


def delete_row(nome_sheet, row_index):
    try:
        sheet = _get_sheet(nome_sheet)
        linha_real = row_index + 2
        sheet.delete_rows(linha_real)
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao eliminar linha {row_index} em '{nome_sheet}': {e}")
        return False


def find_row(nome_sheet, coluna, valor):
    df = read_sheet(nome_sheet)
    if df.empty or coluna not in df.columns:
        return None
    resultado = df[df[coluna].astype(str) == str(valor)]
    if resultado.empty:
        return None
    return int(resultado.index[0])


def get_next_id(nome_sheet, coluna_id="id"):
    df = read_sheet(nome_sheet)
    if df.empty or coluna_id not in df.columns:
        return 1
    ids = pd.to_numeric(df[coluna_id], errors="coerce").dropna()
    return 1 if ids.empty else int(ids.max()) + 1


def hoje_iso():
    return datetime.today().strftime("%Y-%m-%d")


def hoje_pt():
    return datetime.today().strftime("%d/%m/%Y")


def iso_para_pt(data_iso):
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return data_iso


def pt_para_iso(data_pt):
    try:
        return datetime.strptime(data_pt, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return data_pt


def formatar_eur(valor):
    try:
        return f"\u20ac{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "\u20ac0,00"
