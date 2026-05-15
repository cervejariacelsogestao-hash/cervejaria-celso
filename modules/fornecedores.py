"""Sprint 5 — Fornecedores: CRUD, faturas e conta-corrente."""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from data.sheets_client import read_sheet, write_row, get_next_id, formatar_eur, hoje_iso


def render():
    st.title("🚚 Fornecedores")
    tab1, tab2, tab3 = st.tabs(["Fornecedores", "Faturas", "Conta-Corrente"])
    with tab1:
        _tab_fornecedores()
    with tab2:
        _tab_faturas()
    with tab3:
        _tab_conta_corrente()


def _tab_fornecedores():
    st.subheader("Fornecedores registados")
    df = read_sheet("fornecedores")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    st.divider()
    st.subheader("Adicionar fornecedor")
    with st.form("novo_forn"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome *")
            categoria = st.selectbox("Categoria", ["Talho","Peixaria","Marisco","Mercearia","Vinho","Cerveja","Horticola","Lacticinios","Outros"])
            contacto = st.text_input("Contacto (tel/email)")
        with c2:
            prazo = st.number_input("Prazo de pagamento (dias)", min_value=0, max_value=90, value=30)
            desconto = st.number_input("Desconto negociado (%)", min_value=0.0, max_value=50.0, step=0.5)
            notas = st.text_area("Notas")
        submeter = st.form_submit_button("Adicionar", type="primary")
    if submeter and nome:
        nid = get_next_id("fornecedores")
        if write_row("fornecedores", [nid, nome, contacto, categoria, prazo, round(desconto,2), notas]):
            st.success(f"Fornecedor '{nome}' adicionado (ID {nid})")
            st.rerun()


def _tab_faturas():
    st.subheader("Lancar fatura")
    df_forn = read_sheet("fornecedores")
    if df_forn.empty:
        st.warning("Primeiro adiciona fornecedores.")
        return

    forn_opcoes = [f"{row['id']} - {row['nome']}" for _, row in df_forn.iterrows()] if "id" in df_forn.columns else []

    with st.form("nova_fatura"):
        c1, c2 = st.columns(2)
        with c1:
            forn = st.selectbox("Fornecedor *", forn_opcoes)
            data_fatura = st.date_input("Data da fatura", value=datetime.today())
            nr_fatura = st.text_input("Numero da fatura")
        with c2:
            valor = st.number_input("Valor total (€) *", min_value=0.0, step=0.01, format="%.2f")
            iva = st.number_input("IVA (€)", min_value=0.0, step=0.01, format="%.2f")
            prazo_dias = st.number_input("Prazo pagamento (dias)", min_value=0, value=30)
        submeter = st.form_submit_button("Lancar fatura", type="primary")

    if submeter and valor > 0:
        forn_id = forn.split(" - ")[0]
        data_venc = (data_fatura + timedelta(days=prazo_dias)).strftime("%Y-%m-%d")
        nid = get_next_id("compras")
        if write_row("compras", [nid, data_fatura.strftime("%Y-%m-%d"), forn_id, nr_fatura, round(valor,2), round(iva,2), data_venc, "", "pendente", ""]):
            st.success(f"Fatura lancada! Vencimento: {data_venc}")
            st.rerun()

    st.divider()
    st.subheader("Faturas recentes")
    df_comp = read_sheet("compras")
    if not df_comp.empty:
        # Enriquecer com nome do fornecedor
        if "fornecedor_id" in df_comp.columns and not df_forn.empty:
            df_comp = df_comp.merge(
                df_forn[["id","nome"]].rename(columns={"id":"fornecedor_id","nome":"Fornecedor"}),
                on="fornecedor_id", how="left"
            )
        # Marcar vencidas
        hoje = date.today().strftime("%Y-%m-%d")
        if "data_vencimento" in df_comp.columns and "estado" in df_comp.columns:
            df_comp["alerta"] = df_comp.apply(
                lambda r: "🔴 Vencida" if str(r.get("estado","")) == "pendente" and str(r.get("data_vencimento","")) < hoje else "", axis=1
            )
        st.dataframe(df_comp.tail(30), use_container_width=True)


def _tab_conta_corrente():
    st.subheader("Conta-Corrente por Fornecedor")
    df_comp = read_sheet("compras")
    df_forn = read_sheet("fornecedores")

    if df_comp.empty or df_forn.empty:
        st.info("Sem faturas registadas.")
        return

    hoje = date.today().strftime("%Y-%m-%d")

    for _, forn in df_forn.iterrows():
        forn_id = str(forn.get("id",""))
        nome = forn.get("nome","")
        faturas = df_comp[df_comp["fornecedor_id"].astype(str) == forn_id] if "fornecedor_id" in df_comp.columns else pd.DataFrame()
        if faturas.empty:
            continue
        for col in ["valor_total_eur"]:
            if col in faturas.columns:
                faturas[col] = pd.to_numeric(faturas[col], errors="coerce").fillna(0)
        total_divida = faturas[faturas["estado"] == "pendente"]["valor_total_eur"].sum() if "estado" in faturas.columns else 0
        vencidas = faturas[(faturas["estado"] == "pendente") & (faturas["data_vencimento"].astype(str) < hoje)]["valor_total_eur"].sum() if all(c in faturas.columns for c in ["estado","data_vencimento"]) else 0
        with st.expander(f"{nome} — Divida: {formatar_eur(total_divida)} (vencida: {formatar_eur(vencidas)})"):
            cols_show = [c for c in ["data","numero_factura","valor_total_eur","data_vencimento","estado"] if c in faturas.columns]
            st.dataframe(faturas[cols_show], use_container_width=True)
            if st.button(f"Marcar todas pagas — {nome}", key=f"pagar_{forn_id}"):
                from data.sheets_client import find_row, update_row
                faturas_pend = faturas[faturas["estado"] == "pendente"] if "estado" in faturas.columns else pd.DataFrame()
                for _, fat in faturas_pend.iterrows():
                    idx = find_row("compras", "id", fat.get("id",""))
                    if idx is not None:
                        linha = [fat.get(c,"") for c in ["id","data","fornecedor_id","numero_factura","valor_total_eur","iva_eur","data_vencimento"]] + [hoje_iso(), "pago", fat.get("ficheiro_link","")]
                        update_row("compras", idx, linha)
                st.success("Faturas marcadas como pagas!")
                st.rerun()
