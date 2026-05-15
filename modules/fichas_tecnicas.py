"""Sprint 3 — Fichas Técnicas: CRUD de pratos e receitas."""

import streamlit as st
import pandas as pd
from data.sheets_client import read_sheet, write_row, update_row, get_next_id, hoje_iso, formatar_eur


def render():
    st.title("🍽️ Fichas Técnicas")
    tab1, tab2, tab3 = st.tabs(["Pratos", "Ingredientes", "Receitas"])

    with tab1:
        _tab_pratos()
    with tab2:
        _tab_ingredientes()
    with tab3:
        _tab_receitas()


def _tab_pratos():
    st.subheader("Gestão de Pratos")
    df = read_sheet("pratos")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    st.divider()
    st.subheader("Adicionar prato")
    with st.form("novo_prato"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome do prato *")
            categoria = st.selectbox("Categoria", ["Entrada", "Principal", "Sobremesa", "Bebida", "Petisco"])
            preco = st.number_input("Preço de venda (€) *", min_value=0.0, step=0.5, format="%.2f")
        with c2:
            iva = st.selectbox("IVA (%)", [13, 23, 6])
            descricao = st.text_area("Descrição curta")
            signature = st.checkbox("Prato signature?")
        submeter = st.form_submit_button("Adicionar prato", type="primary")
    if submeter and nome and preco > 0:
        nid = get_next_id("pratos")
        if write_row("pratos", [nid, nome, categoria, round(preco, 2), iva, "TRUE", descricao, str(signature)]):
            st.success(f"✅ Prato '{nome}' adicionado (ID {nid})")
            st.rerun()


def _tab_ingredientes():
    st.subheader("Gestão de Ingredientes")
    df = read_sheet("ingredientes")
    df_forn = read_sheet("fornecedores")
    forn_opcoes = ["(nenhum)"]
    if not df_forn.empty and "id" in df_forn.columns and "nome" in df_forn.columns:
        forn_opcoes += [f"{row['id']} - {row['nome']}" for _, row in df_forn.iterrows()]
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    st.divider()
    st.subheader("Adicionar ingrediente")
    with st.form("novo_ing"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome *")
            categoria = st.selectbox("Categoria", ["Carne", "Peixe", "Marisco", "Vegetal", "Mercearia", "Bebida", "Laticínio", "Outros"])
            unidade = st.selectbox("Unidade base", ["kg", "l", "un", "g", "ml"])
        with c2:
            preco = st.number_input("Preço por unidade (€) *", min_value=0.0, step=0.01, format="%.4f")
            merma = st.number_input("Merma (%)", min_value=0.0, max_value=100.0, step=0.5)
            fornecedor = st.selectbox("Fornecedor principal", forn_opcoes)
        submeter = st.form_submit_button("Adicionar ingrediente", type="primary")
    if submeter and nome and preco > 0:
        nid = get_next_id("ingredientes")
        forn_id = fornecedor.split(" - ")[0] if fornecedor != "(nenhum)" else ""
        if write_row("ingredientes", [nid, nome, categoria, unidade, round(preco, 4), forn_id, hoje_iso(), round(merma, 2)]):
            st.success(f"✅ Ingrediente '{nome}' adicionado")
            st.rerun()


def _tab_receitas():
    st.subheader("Receitas (associação prato-ingredientes)")
    df_pratos = read_sheet("pratos")
    df_ings = read_sheet("ingredientes")
    df_fichas = read_sheet("fichas_tecnicas")

    if df_pratos.empty:
        st.warning("Primeiro adiciona pratos na tab 'Pratos'.")
        return
    if df_ings.empty:
        st.warning("Primeiro adiciona ingredientes na tab 'Ingredientes'.")
        return

    prato_opcoes = [f"{row['id']} - {row['nome']}" for _, row in df_pratos.iterrows()] if "id" in df_pratos.columns else []
    ing_opcoes = [f"{row['id']} - {row['nome']} ({row.get('unidade_base','un')})" for _, row in df_ings.iterrows()] if "id" in df_ings.columns else []

    # Ver receita de um prato
    prato_sel = st.selectbox("Ver receita do prato", prato_opcoes)
    if prato_sel and not df_fichas.empty:
        prato_id = prato_sel.split(" - ")[0]
        receita = df_fichas[df_fichas["prato_id"].astype(str) == str(prato_id)]
        if not receita.empty:
            st.dataframe(receita, use_container_width=True)
        else:
            st.info("Este prato ainda não tem receita registada.")

    st.divider()
    st.subheader("Adicionar linha de receita")
    with st.form("nova_receita"):
        c1, c2 = st.columns(2)
        with c1:
            prato = st.selectbox("Prato *", prato_opcoes)
            ing = st.selectbox("Ingrediente *", ing_opcoes)
        with c2:
            qtd = st.number_input("Quantidade bruta *", min_value=0.0, step=0.001, format="%.3f")
            notas = st.text_input("Notas")
        submeter = st.form_submit_button("Adicionar linha", type="primary")
    if submeter and prato and ing and qtd > 0:
        prato_id = prato.split(" - ")[0]
        prato_nome = prato.split(" - ")[1] if len(prato.split(" - ")) > 1 else ""
        ing_id = ing.split(" - ")[0]
        partes = ing.split(" - ")[1] if len(ing.split(" - ")) > 1 else ""
        unidade_ing = partes.split("(")[1].replace(")", "") if "(" in partes else "un"
        # Categoria do prato
        cat_prato = ""
        if not df_pratos.empty and "id" in df_pratos.columns:
            row_p = df_pratos[df_pratos["id"].astype(str) == str(prato_id)]
            if not row_p.empty: cat_prato = str(row_p.iloc[0].get("categoria",""))
        if write_row("fichas_tecnicas", [prato_id, prato_nome, cat_prato, ing_id, round(qtd, 3), unidade_ing, notas]):
            st.success(f"✅ Linha adicionada à receita de '{prato_nome}'")
            st.rerun()
