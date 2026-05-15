"""Sprint 6 — Pessoal: turnos, custos e produtividade."""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from data.sheets_client import read_sheet, write_row, get_next_id, hoje_iso, formatar_eur


def render():
    st.title("👥 Pessoal")
    tab1, tab2, tab3 = st.tabs(["Colaboradores", "Turnos", "Analise de Custos"])

    with tab1:
        _tab_colaboradores()
    with tab2:
        _tab_turnos()
    with tab3:
        _tab_custos()


def _tab_colaboradores():
    st.subheader("Equipa")
    df = read_sheet("colaboradores")
    df_activos = df[df["activo"].astype(str).str.upper() == "TRUE"] if not df.empty and "activo" in df.columns else df
    if not df_activos.empty:
        st.dataframe(df_activos, use_container_width=True)
        total_bruto = pd.to_numeric(df_activos.get("salario_bruto_mensal_eur", pd.Series([])), errors="coerce").fillna(0).sum()
        total_ss = total_bruto * 0.2375
        st.metric("Custo total mensal (salarios + SS 23.75%)", formatar_eur(total_bruto + total_ss))
    st.divider()
    st.subheader("Adicionar colaborador")
    with st.form("novo_colab"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome *")
            funcao = st.selectbox("Funcao", ["Chefe de Sala","Empregado de Mesa","Barman","Grelhador","Cozinheiro","Ajudante de Cozinha","Gerente","Outro"])
        with c2:
            salario = st.number_input("Salario bruto mensal (€)", min_value=700.0, step=50.0, value=1200.0)
            data_inicio = st.date_input("Data de inicio", value=datetime.today())
        submeter = st.form_submit_button("Adicionar", type="primary")
    if submeter and nome:
        nid = get_next_id("colaboradores")
        if write_row("colaboradores", [nid, nome, funcao, round(salario,2), data_inicio.strftime("%Y-%m-%d"), "TRUE"]):
            st.success(f"Colaborador '{nome}' adicionado")
            st.rerun()


def _tab_turnos():
    st.subheader("Registar turno")
    df_colab = read_sheet("colaboradores")
    df_activos = df_colab[df_colab["activo"].astype(str).str.upper() == "TRUE"] if not df_colab.empty and "activo" in df_colab.columns else df_colab

    if df_activos.empty:
        st.warning("Sem colaboradores activos.")
        return

    colab_opcoes = [f"{row['id']} - {row['nome']}" for _, row in df_activos.iterrows()] if "id" in df_activos.columns else []

    with st.form("novo_turno"):
        c1, c2 = st.columns(2)
        with c1:
            data_t = st.date_input("Data", value=datetime.today())
            colab = st.selectbox("Colaborador *", colab_opcoes)
            tipo_turno = st.selectbox("Tipo de turno", ["Almoco","Jantar","Duplo","Extra"])
        with c2:
            inicio = st.time_input("Hora inicio", value=datetime.strptime("10:00","%H:%M").time())
            fim = st.time_input("Hora fim", value=datetime.strptime("15:00","%H:%M").time())
        submeter = st.form_submit_button("Registar turno", type="primary")

    if submeter:
        colab_id = colab.split(" - ")[0]
        inicio_str = inicio.strftime("%H:%M")
        fim_str = fim.strftime("%H:%M")
        # Calcular horas
        h_inicio = inicio.hour + inicio.minute/60
        h_fim = fim.hour + fim.minute/60
        if h_fim < h_inicio: h_fim += 24  # turno passa da meia-noite
        horas = round(h_fim - h_inicio, 2)
        if write_row("turnos", [data_t.strftime("%Y-%m-%d"), colab_id, inicio_str, fim_str, horas, tipo_turno]):
            st.success(f"Turno de {horas}h registado")
            st.rerun()

    st.divider()
    df_turnos = read_sheet("turnos")
    if not df_turnos.empty:
        if "colaborador_id" in df_turnos.columns and not df_activos.empty:
            df_turnos = df_turnos.merge(
                df_activos[["id","nome"]].rename(columns={"id":"colaborador_id","nome":"Nome"}),
                on="colaborador_id", how="left"
            )
        # Filtro por semana
        if "data" in df_turnos.columns:
            semanas = sorted(pd.to_datetime(df_turnos["data"], errors="coerce").dt.isocalendar().week.unique(), reverse=True)
            st.subheader(f"Turnos recentes ({len(df_turnos)} registos)")
            st.dataframe(df_turnos.tail(30), use_container_width=True)


def _tab_custos():
    st.subheader("Analise de custos de pessoal")
    df_turnos = read_sheet("turnos")
    df_colab = read_sheet("colaboradores")
    df_caixa = read_sheet("caixa_diaria")

    if df_colab.empty:
        st.info("Sem colaboradores registados.")
        return

    # Custo mensal fixo
    df_activos = df_colab[df_colab["activo"].astype(str).str.upper() == "TRUE"] if "activo" in df_colab.columns else df_colab
    total_salarios = pd.to_numeric(df_activos.get("salario_bruto_mensal_eur", pd.Series([])), errors="coerce").fillna(0).sum() if not df_activos.empty else 0
    total_ss = total_salarios * 0.2375
    custo_total = total_salarios + total_ss

    c1, c2, c3 = st.columns(3)
    c1.metric("Salarios brutos/mes", formatar_eur(total_salarios))
    c2.metric("Seguranca Social (23.75%)", formatar_eur(total_ss))
    c3.metric("Custo total mensal", formatar_eur(custo_total))

    # Labor cost ratio
    if not df_caixa.empty and "total_pos_eur" in df_caixa.columns:
        mes_atual = hoje_iso()[:7]
        fat_mes = pd.to_numeric(df_caixa[df_caixa["data"].astype(str).str[:7] == mes_atual]["total_pos_eur"], errors="coerce").fillna(0).sum()
        if fat_mes > 0:
            labor_pct = custo_total / fat_mes * 100
            st.metric("Labor Cost % (mês actual)", f"{labor_pct:.1f}%", delta=f"{labor_pct-30:.1f}pp vs target 30%")

    # Horas por colaborador
    if not df_turnos.empty and "horas_trabalhadas" in df_turnos.columns:
        st.subheader("Horas trabalhadas por colaborador")
        df_turnos["horas_trabalhadas"] = pd.to_numeric(df_turnos["horas_trabalhadas"], errors="coerce").fillna(0)
        if "colaborador_id" in df_turnos.columns and not df_activos.empty:
            df_turnos = df_turnos.merge(
                df_activos[["id","nome"]].rename(columns={"id":"colaborador_id","nome":"Nome"}),
                on="colaborador_id", how="left"
            )
            horas_colab = df_turnos.groupby("Nome")["horas_trabalhadas"].sum().reset_index()
            st.dataframe(horas_colab, use_container_width=True)
