"""Schema da base de dados."""

import streamlit as st
import gspread

SCHEMA = {
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
    ["food_cost_target_pct", "33", "Target food cost %"],
    ["labor_cost_target_pct", "30", "Target labor cost %"],
    ["ticket_medio_target_eur", "30", "Target ticket medio euros"],
    ["discrepancia_caixa_alerta_pct", "2", "Alerta discrepancia caixa %"],
    ["email_alertas", "cervejariacelsogestao@gmail.com", "Email alertas"],
    ["nome_restaurante", "Cervejaria do Celso", "Nome"],
    ["morada", "Campo de Ourique, Lisboa", "Morada"],
]

SPREADSHEET_ID = "16PwHAXMd_4khP1kAZ2lfxEwd_d8BDM3WY2yYixJG9Lw"


def _get_client():
    """Usa service_account_from_dict — API correcta para gspread v6."""
    info = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(info)


def init_database(verbose=True):
    resultado = {}
    try:
        gc = _get_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        if verbose:
            st.success(f"Ligado ao Sheet: {spreadsheet.title}")
    except Exception as e:
        if verbose:
            st.error(f"Erro ({type(e).__name__}): {repr(e)}")
        return {}

    sheets_existentes = [ws.title for ws in spreadsheet.worksheets()]

    for nome_ws, cabecalhos in SCHEMA.items():
        try:
            if nome_ws in sheets_existentes:
                if verbose: st.write(f"  skip {nome_ws}")
            else:
                ws = spreadsheet.add_worksheet(title=nome_ws, rows=1000, cols=len(cabecalhos)+2)
                ws.append_row(cabecalhos, value_input_option="USER_ENTERED")
                ws.format("1:1", {"textFormat": {"bold": True}})
                if verbose: st.write(f"  OK {nome_ws}")
                resultado[nome_ws] = "criada"
        except Exception as e:
            if verbose: st.error(f"  ERRO {nome_ws}: {repr(e)}")

    try:
        spreadsheet.del_worksheet(spreadsheet.worksheet("Sheet1"))
    except Exception:
        pass

    try:
        ws_config = spreadsheet.worksheet("config")
        if not ws_config.get_all_records():
            for linha in CONFIG_INICIAL:
                ws_config.append_row(linha)
    except Exception:
        pass

    return resultado


def get_spreadsheet_url():
    return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
