"""Sprint 5 — Stocks: inventario e controlo de movimentos."""

import streamlit as st
import pandas as pd
from datetime import datetime
from data.sheets_client import read_sheet, write_row, hoje_iso, hoje_pt, formatar_eur


def render():
    st.title("📦 Stocks")
    tab1, tab2, tab3 = st.tabs(["Inventário", "Movimentos", "Análise de Quebras"])

    with tab1:
        _tab_inventario()
    with tab2:
        _tab_movimentos()
    with tab3:
        _tab_quebras()


def _tab_inventario():
    st.subheader("Contagem de inventário")
    df_ings = read_sheet("ingredientes")
    if df_ings.empty:
        st.warning("Sem ingredientes. Adiciona em Fichas Tecnicas.")
        return

    st.info("Preenche a quantidade fisicamente contada para cada ingrediente.")
    with st.form("inventario"):
        contagens = {}
        for _, ing in df_ings.iterrows():
            ing_id = str(ing.get("id",""))
            nome = ing.get("nome","")
            unidade = ing.get("unidade_base","un")
            contagens[ing_id] = st.number_input(
                f"{nome} ({unidade})", min_value=0.0, step=0.001, format="%.3f", key=f"inv_{ing_id}"
            )
        responsavel = st.text_input("Responsavel")
        submeter = st.form_submit_button("Guardar inventario", type="primary")

    if submeter:
        data_inv = hoje_iso()
        erros = 0
        for ing_id, qtd in contagens.items():
            ing_row = df_ings[df_ings["id"].astype(str) == ing_id]
            if ing_row.empty:
                continue
            preco = float(str(ing_row.iloc[0].get("preco_actual_eur_unidade",0)).replace(",",".") or 0)
            valor = qtd * preco
            if not write_row("inventarios", [data_inv, ing_id, round(qtd,3), round(valor,2), responsavel]):
                erros += 1
        if erros == 0:
            st.success(f"Inventario de {hoje_pt()} guardado!")
            st.rerun()
        else:
            st.warning(f"Inventario guardado com {erros} erros.")

    # Ultimo inventario
    st.divider()
    st.subheader("Ultimo inventario registado")
    df_inv = read_sheet("inventarios")
    if not df_inv.empty and "data" in df_inv.columns:
        ultima_data = df_inv["data"].max()
        df_ultimo = df_inv[df_inv["data"] == ultima_data]
        # Enriquecer com nomes
        if "ingrediente_id" in df_ultimo.columns and not df_ings.empty:
            df_ultimo = df_ultimo.merge(
                df_ings[["id","nome","unidade_base"]].rename(columns={"id":"ingrediente_id","nome":"Nome","unidade_base":"Unidade"}),
                on="ingrediente_id", how="left"
            )
        st.caption(f"Data: {ultima_data}")
        st.dataframe(df_ultimo, use_container_width=True)
        if "valor_eur" in df_ultimo.columns:
            total = pd.to_numeric(df_ultimo["valor_eur"], errors="coerce").fillna(0).sum()
            st.metric("Valor total em stock", formatar_eur(total))
    else:
        st.info("Ainda nao ha inventarios registados.")


def _tab_movimentos():
    st.subheader("Registar movimento de stock")
    df_ings = read_sheet("ingredientes")
    if df_ings.empty:
        st.warning("Sem ingredientes.")
        return

    ing_opcoes = [f"{row['id']} - {row['nome']}" for _, row in df_ings.iterrows()] if "id" in df_ings.columns else []

    with st.form("mov_stock"):
        c1, c2 = st.columns(2)
        with c1:
            data = st.date_input("Data", value=datetime.today())
            ing = st.selectbox("Ingrediente", ing_opcoes)
            tipo = st.selectbox("Tipo", ["entrada", "saida_quebra", "inventario", "ajuste"])
        with c2:
            quantidade = st.number_input("Quantidade", min_value=0.0, step=0.001, format="%.3f")
            referencia = st.text_input("Referencia (ex: nr factura, motivo)")
        submeter = st.form_submit_button("Registar movimento", type="primary")

    if submeter and quantidade > 0:
        ing_id = ing.split(" - ")[0]
        ing_row = df_ings[df_ings["id"].astype(str) == ing_id]
        preco = float(str(ing_row.iloc[0].get("preco_actual_eur_unidade",0)).replace(",",".") or 0) if not ing_row.empty else 0
        valor = quantidade * preco
        if write_row("stock_movimentos", [data.strftime("%Y-%m-%d"), ing_id, tipo, round(quantidade,3), round(valor,2), referencia]):
            st.success("Movimento registado!")
            st.rerun()

    st.divider()
    st.subheader("Historico de movimentos")
    df_mov = read_sheet("stock_movimentos")
    if not df_mov.empty:
        if "ingrediente_id" in df_mov.columns and not df_ings.empty:
            df_mov = df_mov.merge(
                df_ings[["id","nome"]].rename(columns={"id":"ingrediente_id","nome":"Ingrediente"}),
                on="ingrediente_id", how="left"
            )
        st.dataframe(df_mov.tail(50), use_container_width=True)
    else:
        st.info("Sem movimentos registados.")


def _tab_quebras():
    st.subheader("Analise de quebras")
    st.caption("Compara o stock teorico (baseado em vendas e fichas tecnicas) com o inventario real.")

    df_inv = read_sheet("inventarios")
    df_vendas = read_sheet("vendas_diarias")
    df_fichas = read_sheet("fichas_tecnicas")
    df_ings = read_sheet("ingredientes")
    df_compras = read_sheet("compras_linhas")

    if df_inv.empty or df_ings.empty:
        st.info("Necessario ter pelo menos 1 inventario e ingredientes registados.")
        return

    # Calcular stock teorico por ingrediente
    resultados = []
    for _, ing in df_ings.iterrows():
        ing_id = str(ing.get("id",""))
        nome = ing.get("nome","")
        unidade = ing.get("unidade_base","un")

        # Entradas (compras)
        entradas = 0.0
        if not df_compras.empty and "ingrediente_id" in df_compras.columns:
            comp_ing = df_compras[df_compras["ingrediente_id"].astype(str) == ing_id]
            if not comp_ing.empty and "quantidade" in comp_ing.columns:
                entradas = pd.to_numeric(comp_ing["quantidade"], errors="coerce").fillna(0).sum()

        # Saidas teoricas (fichas tecnicas x vendas)
        saidas_teoricas = 0.0
        if not df_fichas.empty and not df_vendas.empty and "prato_id" in df_fichas.columns:
            fichas_ing = df_fichas[df_fichas["ingrediente_id"].astype(str) == ing_id]
            for _, linha_ft in fichas_ing.iterrows():
                prato_id = str(linha_ft.get("prato_id",""))
                qtd_por_porcao = float(str(linha_ft.get("quantidade_bruta",0)).replace(",",".") or 0)
                if "prato_id" in df_vendas.columns:
                    vendas_prato = df_vendas[df_vendas["prato_id"].astype(str) == prato_id]
                    total_vendido = pd.to_numeric(vendas_prato.get("quantidade", pd.Series([0])), errors="coerce").fillna(0).sum() if not vendas_prato.empty else 0
                    saidas_teoricas += qtd_por_porcao * total_vendido

        # Inventario real (ultimo)
        inv_real = 0.0
        if "ingrediente_id" in df_inv.columns:
            ultima_data = df_inv["data"].max()
            inv_ing = df_inv[(df_inv["data"] == ultima_data) & (df_inv["ingrediente_id"].astype(str) == ing_id)]
            if not inv_ing.empty and "quantidade_contada" in inv_ing.columns:
                inv_real = pd.to_numeric(inv_ing["quantidade_contada"], errors="coerce").fillna(0).sum()

        stock_teorico = entradas - saidas_teoricas
        quebra = stock_teorico - inv_real
        quebra_pct = (quebra / stock_teorico * 100) if stock_teorico > 0 else 0

        if entradas > 0 or saidas_teoricas > 0:
            resultados.append({
                "Ingrediente": nome, "Unidade": unidade,
                "Entradas": round(entradas,3), "Saidas teoricas": round(saidas_teoricas,3),
                "Stock teorico": round(stock_teorico,3), "Inventario real": round(inv_real,3),
                "Quebra": round(quebra,3), "Quebra %": round(quebra_pct,1),
                "Alerta": "🔴" if abs(quebra_pct) > 10 else ("⚠️" if abs(quebra_pct) > 5 else "✅")
            })

    if resultados:
        df_q = pd.DataFrame(resultados).sort_values("Quebra %", ascending=False)
        st.dataframe(df_q, use_container_width=True)
        alertas = [r for r in resultados if "🔴" in r["Alerta"]]
        if alertas:
            st.warning(f"⚠️ {len(alertas)} ingrediente(s) com quebra acima de 10%: {', '.join(r['Ingrediente'] for r in alertas)}")
    else:
        st.info("Sem dados suficientes para calcular quebras.")
