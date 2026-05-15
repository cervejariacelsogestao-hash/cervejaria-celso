"""Sprint 2 — Caixa Diária: fecho por serviço com cálculo de discrepância."""

import streamlit as st
import pandas as pd
from datetime import datetime
from data.sheets_client import read_sheet, write_row, hoje_pt, hoje_iso, formatar_eur


def render():
    st.title("🧾 Caixa Diária")
    tab1, tab2 = st.tabs(["Registar fecho", "Histórico"])

    with tab1:
        st.subheader("Novo fecho de caixa")
        with st.form("fecho_caixa"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data", value=datetime.today())
                servico = st.selectbox("Serviço", ["Almoço", "Jantar"])
                total_pos = st.number_input("Total POS (€)", min_value=0.0, step=0.01, format="%.2f")
            with col2:
                cash = st.number_input("Cash contado (€)", min_value=0.0, step=0.01, format="%.2f")
                mb = st.number_input("Multibanco apurado (€)", min_value=0.0, step=0.01, format="%.2f")
                mbway = st.number_input("MBWay apurado (€)", min_value=0.0, step=0.01, format="%.2f")
                outros = st.number_input("Outros (€)", min_value=0.0, step=0.01, format="%.2f")
            obs = st.text_area("Observações")
            responsavel = st.text_input("Responsável")
            submeter = st.form_submit_button("Registar", type="primary", use_container_width=True)

        if submeter:
            total_apurado = cash + mb + mbway + outros
            discrepancia = total_apurado - total_pos
            disc_pct = (discrepancia / total_pos * 100) if total_pos > 0 else 0

            linha = [
                data.strftime("%Y-%m-%d"), servico, round(total_pos, 2),
                round(cash, 2), round(mb, 2), round(mbway, 2), round(outros, 2),
                round(discrepancia, 2), round(disc_pct, 2), obs, responsavel
            ]
            if write_row("caixa_diaria", linha):
                st.success(f"✅ Fecho registado! Discrepância: {formatar_eur(discrepancia)} ({disc_pct:.1f}%)")
                if abs(disc_pct) > 2:
                    st.warning(f"⚠️ Discrepância acima de 2% — verifica os valores.")
            else:
                st.error("Erro ao guardar.")

        # Preview em tempo real
        st.divider()
        st.caption("Preview da discrepância (antes de submeter)")
        if total_pos > 0:
            total_ap = cash + mb + mbway + outros
            disc = total_ap - total_pos
            pct = disc / total_pos * 100
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total apurado", formatar_eur(total_ap))
            col_b.metric("Discrepância", formatar_eur(disc))
            col_c.metric("Discrepância %", f"{pct:.2f}%")

    with tab2:
        st.subheader("Histórico de fechos")
        df = read_sheet("caixa_diaria")
        if df.empty:
            st.info("Ainda sem registos. Começa a registar na tab 'Registar fecho'.")
        else:
            for col in ["total_pos_eur","cash_contado_eur","mb_apurado_eur","mbway_apurado_eur","outros_eur","discrepancia_eur","discrepancia_pct"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            # Filtro por mês
            if "data" in df.columns:
                meses = sorted(df["data"].astype(str).str[:7].unique(), reverse=True)
                mes_sel = st.selectbox("Filtrar por mês", ["Todos"] + list(meses))
                if mes_sel != "Todos":
                    df = df[df["data"].astype(str).str[:7] == mes_sel]

            st.dataframe(df, use_container_width=True)

            # Resumo do período
            if "total_pos_eur" in df.columns:
                st.metric("Total faturado no período", formatar_eur(df["total_pos_eur"].sum()))
