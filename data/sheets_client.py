"""Cliente Google Sheets com cache e CRUD."""

import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

SPREADSHEET_ID = "16PwHAXMd_4khP1kAZ2lfxEwd_d8BDM3WY2yYixJG9Lw"


def _get_client():
    info = {k: v for k, v in st.secrets["gcp_service_account"].items()}
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    return gspread.service_account_from_dict(info)


def _get_sheet(nome_sheet):
    try:
        gc = _get_client()
        sp = gc.open_by_key(SPREADSHEET_ID)
        return sp.worksheet(nome_sheet)
    except gspread.WorksheetNotFound:
        st.error(f"Worksheet '{nome_sheet}' nao existe.")
        st.stop()
    except Exception as e:
        st.error(f"Erro sheet '{nome_sheet}': {repr(e)}")
        st.stop()


@st.cache_data(ttl=60)
def read_sheet(nome_sheet):
    try:
        sheet = _get_sheet(nome_sheet)
        dados = sheet.get_all_records(default_blank="")
        if not dados:
            return pd.DataFrame(columns=sheet.row_values(1))
        return pd.DataFrame(dados)
    except Exception as e:
        st.warning(f"Erro ler '{nome_sheet}': {e}")
        return pd.DataFrame()


def write_row(nome_sheet, linha):
    try:
        _get_sheet(nome_sheet).append_row(linha, value_input_option="USER_ENTERED")
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro escrever: {e}")
        return False


def update_row(nome_sheet, row_index, dados):
    try:
        _get_sheet(nome_sheet).update(f"A{row_index+2}", [dados])
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro actualizar: {e}")
        return False


def delete_row(nome_sheet, row_index):
    try:
        _get_sheet(nome_sheet).delete_rows(row_index + 2)
        read_sheet.clear()
        return True
    except Exception as e:
        st.error(f"Erro eliminar: {e}")
        return False


def find_row(nome_sheet, coluna, valor):
    df = read_sheet(nome_sheet)
    if df.empty or coluna not in df.columns:
        return None
    r = df[df[coluna].astype(str) == str(valor)]
    return int(r.index[0]) if not r.empty else None


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


def iso_para_pt(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return d


def pt_para_iso(d):
    try:
        return datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return d


def formatar_eur(v):
    try:
        s = f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"EUR {s}"
    except Exception:
        return "EUR 0,00"
