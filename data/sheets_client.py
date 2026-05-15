"""
Cliente Google Sheets — wrapper sobre gspread com cache e operações CRUD.
Todas as leituras têm cache de 60 segundos para reduzir chamadas à API.
"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_client() -> gspread.Client:
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(credenciais)


def _get_sheet(nome_sheet: str) -> gspread.Worksheet:
    cliente = _get_client()
    nome_spreadsheet = st.secrets["app"]["sheet_name"]
    try:
        spreadsheet = cliente.open(nome_spreadsheet)
        return spreadsheet.worksheet(nome_sheet)
    except gspread.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{nome_spreadsheet}' não encontrado. Corre init_database() primeiro.")
        st.stop()
    except gspread.WorksheetNotFound:
        st.error(f"Worksheet '{nome_sheet}' não existe. Corre init_database() primeiro.")
        st.stop()


@st.cache_data(ttl=60)
def read_sheet(nome_sheet: str) -> pd.DataFrame:
    try:
        sheet = _get_sheet(nome_sheet)
        dados = sheet.get_all_records(default_blank="")
        if not dados:
            cabecalhos = sheet.row_values(1)
            return pd.DataFrame(columns=cabecalhos)
        return pd.DataFrame(dados)
    except Exception as e:
        st.warning(f"Não foi possível ler '{nome_sheet}': {e}")
        return pd.DataFrame()


def write_row(nome_sheet: str, linha: list) -> bool:
    try:
        sheet = _get_sheet(nome_sheet)
        sheet.append_row(linha, value_input_option="USER_ENTERED")
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao escrever em '{nome_sheet}': {e}")
        return False


def update_row(nome_sheet: str, row_index: int, dados: list) -> bool:
    try:
        sheet = _get_sheet(nome_sheet)
        linha_real = row_index + 2
        sheet.update(f"A{linha_real}", [dados])
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao actualizar linha {row_index} em '{nome_sheet}': {e}")
        return False


def delete_row(nome_sheet: str, row_index: int) -> bool:
    try:
        sheet = _get_sheet(nome_sheet)
        linha_real = row_index + 2
        sheet.delete_rows(linha_real)
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao eliminar linha {row_index} em '{nome_sheet}': {e}")
        return False


def find_row(nome_sheet: str, coluna: str, valor) -> int | None:
    df = read_sheet(nome_sheet)
    if df.empty or coluna not in df.columns:
        return None
    resultado = df[df[coluna].astype(str) == str(valor)]
    if resultado.empty:
        return None
    return int(resultado.index[0])


def get_next_id(nome_sheet: str, coluna_id: str = "id") -> int:
    df = read_sheet(nome_sheet)
    if df.empty or coluna_id not in df.columns:
        return 1
    ids_existentes = pd.to_numeric(df[coluna_id], errors="coerce").dropna()
    if ids_existentes.empty:
        return 1
    return int(ids_existentes.max()) + 1


def hoje_iso() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def hoje_pt() -> str:
    return datetime.today().strftime("%d/%m/%Y")


def iso_para_pt(data_iso: str) -> str:
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return data_iso


def pt_para_iso(data_pt: str) -> str:
    try:
        return datetime.strptime(data_pt, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return data_pt


def formatar_eur(valor) -> str:
    try:
        return f"€{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "€0,00"
