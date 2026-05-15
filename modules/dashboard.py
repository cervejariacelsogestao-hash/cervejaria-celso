"""Sprint 2 — Dashboard principal com KPIs diarios e mensais."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data.sheets_client import read_sheet, formatar_eur, hoje_iso


def render():
    st.title("📊 Dashboard")

    # --- Dados ---
    try:
        df_caixa = read_sheet("caixa_diaria")
        df_vendas = read_sheet("vendas_diarias")
        df_config = read_sheet("config")
    except Exception as e:
        st.error(f"Erro a carregar dados: {e}")
        return

    # Config targets
    config = {}
    if not df_config.empty and "chave" in df_config.columns:
        config = dict(zip(df_config["chave"], df_config["valor"]))
    ticket_target = float(config.get("ticket_medio_target_eur", 30))
    fc_target = float(config.get("food_cost_target_pct", 33))
    disc_alerta = float(config.get("discrepancia_caixa_alerta_pct", 2))

    hoje = hoje_iso()
    mes_atual = hoje[:7]

    # --- KPIs do dia ---
    st.subheader("Hoje")
    caixa_hoje = pd.DataFrame()
    if not df_caixa.empty and "data" in df_caixa.columns:
        caixa_hoje = df_caixa[df_caixa["data"].astype(str) == hoje]

    fat_hoje = 0.0
    disc_hoje = 0.0
    if not caixa_hoje.empty:
        for col in ["total_pos_eur", "cash_contado_eur", "mb_apurado_eur", "mbway_apurado_eur", "outros_eur"]:
            if col in caixa_hoje.columns:
                caixa_hoje[col] = pd.to_numeric(caixa_hoje[col], errors="coerce").fillna(0)
        if "total_pos_eur" in caixa_hoje.columns:
            fat_hoje = caixa_hoje["total_pos_eur"].sum()
        if "discrepancia_eur" in caixa_hoje.columns:
            disc_hoje = pd.to_numeric(caixa_hoje["discrepancia_eur"], errors="coerce").fillna(0).sum()

    vendas_hoje = pd.DataFrame()
    if not df_vendas.empty and "data" in df_vendas.columns:
        vendas_hoje = df_vendas[df_vendas["data"].astype(str) == hoje]
    couverts_hoje = int(vendas_hoje["quantidade"].sum()) if not vendas_hoje.empty and "quantidade" in vendas_hoje.columns else 0
    ticket_hoje = (fat_hoje / couverts_hoje) if couverts_hoje > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturação Hoje", formatar_eur(fat_hoje))
    col2.metric("Couverts", couverts_hoje)
    col3.metric("Ticket Médio", formatar_eur(ticket_hoje), delta=f"{ticket_hoje - ticket_target:+.1f}€ vs target")
    disc_color = "normal" if abs(disc_hoje) < disc_alerta else "inverse"
    col4.metric("Discrepância Caixa", formatar_eur(disc_hoje))

    if abs(disc_hoje) > disc_alerta:
        st.warning(f"⚠️ Discrepância de {formatar_eur(disc_hoje)} acima do limite de {disc_alerta}%!")

    st.divider()

    # --- KPIs do mês ---
    st.subheader(f"Mês actual ({mes_atual})")
    caixa_mes = pd.DataFrame()
    if not df_caixa.empty and "data" in df_caixa.columns:
        caixa_mes = df_caixa[df_caixa["data"].astype(str).str[:7] == mes_atual]

    fat_mes = 0.0
    if not caixa_mes.empty and "total_pos_eur" in caixa_mes.columns:
        fat_mes = pd.to_numeric(caixa_mes["total_pos_eur"], errors="coerce").fillna(0).sum()

    dias_mes = len(caixa_mes["data"].unique()) if not caixa_mes.empty and "data" in caixa_mes.columns else 1
    fat_dia_medio = fat_mes / max(dias_mes, 1)

    vendas_mes = pd.DataFrame()
    if not df_vendas.empty and "data" in df_vendas.columns:
        vendas_mes = df_vendas[df_vendas["data"].astype(str).str[:7] == mes_atual]
    couverts_mes = int(vendas_mes["quantidade"].sum()) if not vendas_mes.empty and "quantidade" in vendas_mes.columns else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Faturação do Mês", formatar_eur(fat_mes))
    m2.metric("Dias registados", dias_mes)
    m3.metric("Média diária", formatar_eur(fat_dia_medio))
    m4.metric("Couverts do mês", couverts_mes)

    st.divider()

    # --- Gráfico faturação 30 dias ---
    if not df_caixa.empty and "data" in df_caixa.columns and "total_pos_eur" in df_caixa.columns:
        df_plot = df_caixa.copy()
        df_plot["total_pos_eur"] = pd.to_numeric(df_plot["total_pos_eur"], errors="coerce").fillna(0)
        df_plot["data"] = pd.to_datetime(df_plot["data"], errors="coerce")
        df_plot = df_plot.dropna(subset=["data"])
        df_plot = df_plot[df_plot["data"] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
        df_daily = df_plot.groupby("data")["total_pos_eur"].sum().reset_index()
        if not df_daily.empty:
            fig = px.bar(df_daily, x="data", y="total_pos_eur",
                        title="Faturação diária — últimos 30 dias",
                        labels={"data": "Data", "total_pos_eur": "€"},
                        color_discrete_sequence=["#E8A427"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="#F0F0F0", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de faturação nos últimos 30 dias. Começa a registar na Caixa Diária.")
    else:
        st.info("Sem dados ainda. Começa a registar na Caixa Diária.")

    # --- Discrepâncias recentes ---
    if not df_caixa.empty and "discrepancia_eur" in df_caixa.columns:
        df_disc = df_caixa.copy()
        df_disc["discrepancia_eur"] = pd.to_numeric(df_disc["discrepancia_eur"], errors="coerce").fillna(0)
        df_disc_alert = df_disc[abs(df_disc["discrepancia_eur"]) > 0]
        if not df_disc_alert.empty:
            st.subheader("Últimas discrepâncias de caixa")
            cols_show = [c for c in ["data","servico","total_pos_eur","discrepancia_eur","observacoes"] if c in df_disc_alert.columns]
            st.dataframe(df_disc_alert[cols_show].tail(10), use_container_width=True)
