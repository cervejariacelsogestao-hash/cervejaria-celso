"""Sprint 3 — Food Cost: calculo por prato com codigo de cor."""

import streamlit as st
import pandas as pd
from data.sheets_client import read_sheet, formatar_eur


def calcular_food_cost_prato(prato_id, df_fichas, df_ings, preco_venda):
    """Calcula food cost de um prato a partir da ficha tecnica."""
    if df_fichas.empty or df_ings.empty:
        return None, []
    linhas = df_fichas[df_fichas["prato_id"].astype(str) == str(prato_id)]
    if linhas.empty:
        return None, []
    custo_total = 0.0
    detalhe = []
    for _, linha in linhas.iterrows():
        ing_id = str(linha.get("ingrediente_id", ""))
        qtd = float(str(linha.get("quantidade_bruta", 0)).replace(",", ".") or 0)
        ing_row = df_ings[df_ings["id"].astype(str) == ing_id]
        if ing_row.empty:
            continue
        preco_unit = float(str(ing_row.iloc[0].get("preco_actual_eur_unidade", 0)).replace(",", ".") or 0)
        merma = float(str(ing_row.iloc[0].get("merma_pct", 0)).replace(",", ".") or 0) / 100
        custo_linha = qtd * preco_unit * (1 + merma)
        custo_total += custo_linha
        detalhe.append({
            "Ingrediente": ing_row.iloc[0].get("nome", ing_id),
            "Qtd": qtd,
            "Preco unit": formatar_eur(preco_unit),
            "Merma %": f"{merma*100:.1f}%",
            "Custo": formatar_eur(custo_linha)
        })
    fc_pct = (custo_total / preco_venda * 100) if preco_venda > 0 else None
    return fc_pct, detalhe


def render():
    st.title("📉 Food Cost")

    df_pratos = read_sheet("pratos")
    df_fichas = read_sheet("fichas_tecnicas")
    df_ings = read_sheet("ingredientes")

    if df_pratos.empty:
        st.warning("Sem pratos registados. Vai a Fichas Tecnicas para criar pratos.")
        return

    # Tabela geral de food cost
    st.subheader("Food Cost por Prato")
    resultados = []
    for _, prato in df_pratos.iterrows():
        if str(prato.get("activo","TRUE")).upper() != "TRUE":
            continue
        prato_id = str(prato.get("id", ""))
        nome = prato.get("nome", "")
        preco = float(str(prato.get("preco_venda_eur", 0)).replace(",", ".") or 0)
        categoria = prato.get("categoria", "")
        fc_pct, _ = calcular_food_cost_prato(prato_id, df_fichas, df_ings, preco)
        if fc_pct is not None:
            fc_custo = preco * fc_pct / 100
            margem = preco - fc_custo
            resultados.append({
                "Prato": nome,
                "Categoria": categoria,
                "Preco Venda": preco,
                "Custo": round(fc_custo, 2),
                "Food Cost %": round(fc_pct, 1),
                "Margem Bruta": round(margem, 2),
                "Status": "✅" if fc_pct <= 33 else ("⚠️" if fc_pct <= 38 else "🔴")
            })
        else:
            resultados.append({
                "Prato": nome, "Categoria": categoria, "Preco Venda": preco,
                "Custo": None, "Food Cost %": None, "Margem Bruta": None, "Status": "❓ Sem receita"
            })

    if resultados:
        df_res = pd.DataFrame(resultados).sort_values("Food Cost %", ascending=True, na_position="last")
        st.dataframe(df_res, use_container_width=True)

        # Métricas resumo
        validos = [r for r in resultados if r["Food Cost %"] is not None]
        if validos:
            fc_medio = sum(r["Food Cost %"] for r in validos) / len(validos)
            col1, col2, col3 = st.columns(3)
            col1.metric("Food Cost Médio", f"{fc_medio:.1f}%", delta=f"{fc_medio-33:.1f}pp vs target 33%")
            col2.metric("Pratos dentro do target", f"{sum(1 for r in validos if r['Food Cost %'] <= 33)}/{len(validos)}")
            col3.metric("Pratos sem receita", f"{sum(1 for r in resultados if r['Food Cost %'] is None)}")
    else:
        st.info("Nenhum prato com ficha tecnica completa. Vai a Fichas Tecnicas para adicionar receitas.")

    st.divider()

    # Detalhe de um prato
    st.subheader("Detalhe por prato")
    prato_opcoes = [f"{r['Prato']}" for r in resultados if r["Food Cost %"] is not None]
    if prato_opcoes:
        prato_sel_nome = st.selectbox("Selecciona prato", prato_opcoes)
        prato_match = df_pratos[df_pratos["nome"] == prato_sel_nome]
        if not prato_match.empty:
            prato_id = str(prato_match.iloc[0]["id"])
            preco = float(str(prato_match.iloc[0].get("preco_venda_eur", 0)).replace(",", ".") or 0)
            fc_pct, detalhe = calcular_food_cost_prato(prato_id, df_fichas, df_ings, preco)
            if detalhe:
                fc_custo = preco * fc_pct / 100
                col1, col2, col3 = st.columns(3)
                col1.metric("Preco de venda", formatar_eur(preco))
                col2.metric("Custo total", formatar_eur(fc_custo))
                col3.metric("Food Cost %", f"{fc_pct:.1f}%")
                st.dataframe(pd.DataFrame(detalhe), use_container_width=True)

    # Atualizar preços de ingredientes
    st.divider()
    st.subheader("Actualizar preço de ingrediente")
    if not df_ings.empty:
        ing_opcoes = [f"{row['id']} - {row['nome']}" for _, row in df_ings.iterrows()] if "id" in df_ings.columns else []
        with st.form("update_preco"):
            ing_sel = st.selectbox("Ingrediente", ing_opcoes)
            novo_preco = st.number_input("Novo preço (€/unidade)", min_value=0.0, step=0.001, format="%.4f")
            submeter = st.form_submit_button("Actualizar")
        if submeter and novo_preco > 0:
            from data.sheets_client import find_row, update_row, hoje_iso
            ing_id = ing_sel.split(" - ")[0]
            idx = find_row("ingredientes", "id", ing_id)
            if idx is not None:
                ing_row = df_ings[df_ings["id"].astype(str) == str(ing_id)].iloc[0]
                linha = [
                    ing_row.get("id"), ing_row.get("nome"), ing_row.get("categoria"),
                    ing_row.get("unidade_base"), round(novo_preco, 4),
                    ing_row.get("fornecedor_principal_id"), hoje_iso(), ing_row.get("merma_pct", 0)
                ]
                if update_row("ingredientes", idx, linha):
                    st.success(f"Preco actualizado para {formatar_eur(novo_preco)}")
                    st.rerun()
