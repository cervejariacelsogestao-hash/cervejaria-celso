"""
Schema da base de dados — define e cria as 16 worksheets do Google Sheet.
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SCHEMA: dict[str, list[str]] = {
    "config": ["chave", "valor", "descricao"],
    "users": ["email", "nome", "role", "activo", "password_hash"],
    "ingredientes": ["id", "nome", "categoria", "unidade_base", "preco_actual_eur_unidade", "fornecedor_principal_id", "data_ultima_atualizacao", "merma_pct"],
    "fichas_tecnicas": ["prato_id", "prato_nome", "categoria_prato", "ingrediente_id", "quantidade_bruta", "unidade", "notas"],
    "pratos": ["id", "nome", "categoria", "preco_venda_eur", "iva_pct", "activo", "descricao_curta", "signature"],
    "vendas_diarias": ["data", "servico", "prato_id", "quantidade", "valor_total_eur", "metodo_pagamento"],
    "caixa_diaria": ["data", "servico", "total_pos_eur", "cash_contado_eur", "mb_apurado_eur", "mbway_apurado_eur", "outros_eur", "discrepancia_eur", "discrepancia_pct", "observacoes", "responsavel"],
    "fornecedores": ["id", "nome", "contacto", "categoria", "prazo_pagamento_dias", "desconto_negociado_pct", "notas"],
    "compras": ["id", "data", "fornecedor_id", "numero_factura", "valor_total_eur", "iva_eur", "data_vencimento", "data_pagamento", "estado", "ficheiro_link"],
    "compras_linhas": ["compra_id", "ingrediente_id", "quantidade", "unidade", "preco_unitario_eur", "valor_linha_eur"],
    "stock_movimentos": ["data", "ingrediente_id", "tipo", "quantidade", "valor_eur", "referencia"],
    "inventarios": ["data", "ingrediente_id", "quantidade_contada", "valor_eur", "responsavel"],
    "colaboradores": ["id", "nome", "funcao", "salario_bruto_mensal_eur", "data_inicio", "activo"],
    "turnos": ["data", "colaborador_id", "inicio_hh_mm", "fim_hh_mm", "horas_trabalhadas", "tipo_turno"],
    "custos_fixos": ["mes", "categoria", "valor_eur", "notas"],
    "pnl_mensal": ["mes", "receita_total", "food_cost_real", "food_cost_pct", "labor_cost", "labor_pct", "renda", "energia", "outros_opex", "ebitda", "ebitda_pct"],
}

CONFIG_INICIAL = [
    ["food_cost_target_pct", "33", "Target de food cost em percentagem"],
    ["labor_cost_target_pct", "30", "Target de labor cost em percentagem"],
    ["prime_cost_target_pct", "63", "Target de prime cost (food+labor) em percentagem"],
    ["iva_comida_pct", "13", "IVA aplicável a comida (%)"],
    ["iva_bebida_alc_pct", "23", "IVA aplicável a bebidas alcoólicas (%)"],
    ["iva_bebida_nalc_pct", "23", "IVA aplicável a bebidas não alcoólicas (%)"],
    ["ticket_medio_target_eur", "30", "Target de ticket médio em euros"],
    ["discrepancia_caixa_alerta_pct", "2", "Percentagem de discrepância que dispara alerta"],
    ["email_alertas", "cervejariacelsogestao@gmail.com", "Email para alertas"],
    ["nome_restaurante", "Cervejaria do Celso", "Nome do restaurante"],
    ["morada", "Campo de Ourique, Lisboa", "Morada"],
]


def _get_client() -> gspread.Client:
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(credenciais)


def init_database(verbose: bool = True) -> dict:
    nome_sheet = st.secrets["app"]["sheet_name"]
    cliente = _get_client()
    resultado = {}

    try:
        spreadsheet = cliente.open(nome_sheet)
        if verbose:
            st.info(f"Spreadsheet '{nome_sheet}' já existe. A verificar worksheets...")
    except gspread.SpreadsheetNotFound:
        spreadsheet = cliente.create(nome_sheet)
        email_admin = st.secrets["app"]["admin_email"]
        spreadsheet.share(email_admin, perm_type="user", role="writer")
        if verbose:
            st.success(f"Spreadsheet '{nome_sheet}' criado e partilhado com {email_admin}")

    sheets_existentes = [ws.title for ws in spreadsheet.worksheets()]

    for nome_ws, cabecalhos in SCHEMA.items():
        try:
            if nome_ws in sheets_existentes:
                resultado[nome_ws] = "já existe"
                if verbose:
                    st.write(f"  ⏭ {nome_ws} — já existe")
            else:
                ws = spreadsheet.add_worksheet(title=nome_ws, rows=1000, cols=len(cabecalhos) + 2)
                ws.append_row(cabecalhos, value_input_option="USER_ENTERED")
                ws.format("1:1", {"textFormat": {"bold": True}})
                resultado[nome_ws] = "criada"
                if verbose:
                    st.write(f"  ✅ {nome_ws} — criada")
        except Exception as e:
            resultado[nome_ws] = f"erro: {e}"
            if verbose:
                st.error(f"  ❌ {nome_ws} — erro: {e}")

    try:
        sheet1 = spreadsheet.worksheet("Sheet1")
        spreadsheet.del_worksheet(sheet1)
    except Exception:
        pass

    try:
        ws_config = spreadsheet.worksheet("config")
        dados_actuais = ws_config.get_all_records()
        if not dados_actuais:
            for linha in CONFIG_INICIAL:
                ws_config.append_row(linha)
            if verbose:
                st.success("Configurações iniciais criadas.")
    except Exception as e:
        if verbose:
            st.warning(f"Não foi possível popular config: {e}")

    return resultado


def get_spreadsheet_url() -> str:
    nome_sheet = st.secrets["app"]["sheet_name"]
    cliente = _get_client()
    try:
        spreadsheet = cliente.open(nome_sheet)
        return spreadsheet.url
    except Exception:
        return ""
