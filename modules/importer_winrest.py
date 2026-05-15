"""Sprint 4 — Importar Winrest: parser de CSV do POS."""

import streamlit as st
import pandas as pd
import io
from data.sheets_client import read_sheet, write_row


MAPPING_COLUNAS = {
    "data": ["data", "date", "dia"],
    "servico": ["servico", "refeicao", "periodo", "meal"],
    "prato_id": ["prato_id", "artigo_id", "item_id", "code"],
    "quantidade": ["quantidade", "qty", "qtd", "quant"],
    "valor_total_eur": ["total", "valor", "amount", "preco_total", "value"],
    "metodo_pagamento": ["pagamento", "payment", "metodo"],
}


def _mapear_colunas(df_raw: pd.DataFrame) -> dict:
    mapeamento = {}
    cols_lower = {c: c.lower().strip() for c in df_raw.columns}
    for campo, alternativas in MAPPING_COLUNAS.items():
        for col, col_l in cols_lower.items():
            if any(alt in col_l for alt in alternativas):
                mapeamento[campo] = col
                break
    return mapeamento


def render():
    st.title("📥 Importar Winrest")
    st.caption("Importa o ficheiro CSV exportado do Winrest para popular as vendas diarias.")

    st.subheader("Como exportar do Winrest")
    with st.expander("Ver instruções"):
        st.markdown("""
1. No Winrest, vai a **Relatórios** → **Vendas por artigo**
2. Selecciona o período pretendido
3. Clica **Exportar** → **CSV**
4. Guarda o ficheiro e faz upload aqui abaixo
        """)

    uploaded = st.file_uploader("Upload CSV do Winrest", type=["csv", "txt"])

    if uploaded is None:
        st.info("Aguarda upload do ficheiro CSV.")
        return

    # Tentar ler com diferentes separadores
    content = uploaded.read()
    df_raw = None
    for sep in [";", ",", "\t", "|"]:
        try:
            df_raw = pd.read_csv(io.BytesIO(content), sep=sep, encoding="utf-8", dtype=str, on_bad_lines="skip")
            if len(df_raw.columns) > 2:
                break
        except Exception:
            pass
        try:
            df_raw = pd.read_csv(io.BytesIO(content), sep=sep, encoding="latin-1", dtype=str, on_bad_lines="skip")
            if len(df_raw.columns) > 2:
                break
        except Exception:
            pass

    if df_raw is None or df_raw.empty:
        st.error("Nao foi possivel ler o ficheiro. Verifica o formato.")
        return

    st.write(f"Ficheiro lido: **{len(df_raw)} linhas**, **{len(df_raw.columns)} colunas**")
    st.dataframe(df_raw.head(5), use_container_width=True)

    # Mapeamento de colunas
    st.subheader("Mapeamento de colunas")
    mapeamento_auto = _mapear_colunas(df_raw)

    col_opcoes = ["(ignorar)"] + list(df_raw.columns)
    mapeamento_final = {}
    c1, c2 = st.columns(2)
    campos = list(MAPPING_COLUNAS.keys())
    for i, campo in enumerate(campos):
        col = c1 if i % 2 == 0 else c2
        default_idx = col_opcoes.index(mapeamento_auto.get(campo, "(ignorar)")) if mapeamento_auto.get(campo,"(ignorar)") in col_opcoes else 0
        sel = col.selectbox(f"Campo '{campo}'", col_opcoes, index=default_idx)
        if sel != "(ignorar)":
            mapeamento_final[campo] = sel

    # Preview
    if len(mapeamento_final) >= 3:
        st.subheader("Preview da importacao")
        df_preview = pd.DataFrame()
        for campo, col in mapeamento_final.items():
            df_preview[campo] = df_raw[col]
        st.dataframe(df_preview.head(10), use_container_width=True)

        # Importar
        df_existente = read_sheet("vendas_diarias")
        chaves_existentes = set()
        if not df_existente.empty and all(c in df_existente.columns for c in ["data","prato_id"]):
            chaves_existentes = set(zip(df_existente["data"].astype(str), df_existente["prato_id"].astype(str)))

        if st.button("Importar para a base de dados", type="primary"):
            importadas = 0
            duplicadas = 0
            erros = 0
            progress = st.progress(0)
            for i, (_, row) in enumerate(df_preview.iterrows()):
                progress.progress((i+1)/len(df_preview))
                data = str(row.get("data","")).strip()
                prato_id = str(row.get("prato_id","")).strip()
                chave = (data, prato_id)
                if chave in chaves_existentes:
                    duplicadas += 1
                    continue
                linha = [
                    data,
                    str(row.get("servico","")).strip(),
                    prato_id,
                    str(row.get("quantidade","0")).replace(",",".").strip(),
                    str(row.get("valor_total_eur","0")).replace(",",".").strip(),
                    str(row.get("metodo_pagamento","")).strip(),
                ]
                if write_row("vendas_diarias", linha):
                    importadas += 1
                    chaves_existentes.add(chave)
                else:
                    erros += 1
            progress.empty()
            st.success(f"✅ Importadas: {importadas} | Duplicadas (ignoradas): {duplicadas} | Erros: {erros}")
    else:
        st.warning("Mapeia pelo menos os campos: data, prato_id, quantidade.")
