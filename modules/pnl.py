"""Sprint 6 — P&L Mensal: demonstracao de resultados automatica."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.sheets_client import read_sheet, write_row, formatar_eur, hoje_iso


def calcular_pnl_mes(mes: str) -> dict:
    """Calcula o P&L de um mes a partir das sheets de dados."""
    df_caixa = read_sheet("caixa_diaria")
    df_custos = read_sheet("custos_fixos")
    df_colab = read_sheet("colaboradores")
    df_fichas = read_sheet("fichas_tecnicas")
    df_ings = read_sheet("ingredientes")
    df_vendas = read_sheet("vendas_diarias")

    result = {"mes": mes, "receita_total": 0, "food_cost_real": 0, "labor_cost": 0,
              "renda": 0, "energia": 0, "outros_opex": 0, "ebitda": 0,
              "food_cost_pct": 0, "labor_pct": 0, "ebitda_pct": 0}

    # Receita
    if not df_caixa.empty and "total_pos_eur" in df_caixa.columns:
        df_mes = df_caixa[df_caixa["data"].astype(str).str[:7] == mes]
        result["receita_total"] = pd.to_numeric(df_mes["total_pos_eur"], errors="coerce").fillna(0).sum()

    receita = result["receita_total"]
    if receita == 0:
        return result

    # Food cost real (de compras do mes)
    df_comp = read_sheet("compras")
    if not df_comp.empty and "data" in df_comp.columns and "valor_total_eur" in df_comp.columns:
        df_comp_mes = df_comp[df_comp["data"].astype(str).str[:7] == mes]
        iva_media = 0.13
        result["food_cost_real"] = pd.to_numeric(df_comp_mes["valor_total_eur"], errors="coerce").fillna(0).sum() / (1 + iva_media)

    # Labor cost (salarios + SS)
    if not df_colab.empty and "salario_bruto_mensal_eur" in df_colab.columns:
        activos = df_colab[df_colab["activo"].astype(str).str.upper() == "TRUE"] if "activo" in df_colab.columns else df_colab
        salarios = pd.to_numeric(activos["salario_bruto_mensal_eur"], errors="coerce").fillna(0).sum()
        result["labor_cost"] = salarios * 1.2375

    # Custos fixos do mes
    if not df_custos.empty and "mes" in df_custos.columns:
        df_cf_mes = df_custos[df_custos["mes"].astype(str).str[:7] == mes]
        for _, row in df_cf_mes.iterrows():
            cat = str(row.get("categoria","")).lower()
            val = pd.to_numeric(str(row.get("valor_eur",0)).replace(",","."), errors="coerce") or 0
            if "renda" in cat:
                result["renda"] += val
            elif any(x in cat for x in ["luz","agua","gas","energia"]):
                result["energia"] += val
            else:
                result["outros_opex"] += val

    # EBITDA
    total_custos = result["food_cost_real"] + result["labor_cost"] + result["renda"] + result["energia"] + result["outros_opex"]
    result["ebitda"] = receita - total_custos

    # Percentagens
    result["food_cost_pct"] = round(result["food_cost_real"] / receita * 100, 1) if receita > 0 else 0
    result["labor_pct"] = round(result["labor_cost"] / receita * 100, 1) if receita > 0 else 0
    result["ebitda_pct"] = round(result["ebitda"] / receita * 100, 1) if receita > 0 else 0

    return result


def render():
    st.title("📈 P&L Mensal")

    # Calcular meses disponiveis
    df_caixa = read_sheet("caixa_diaria")
    mes_atual = hoje_iso()[:7]

    if df_caixa.empty or "data" not in df_caixa.columns:
        meses_disponiveis = [mes_atual]
    else:
        meses_disponiveis = sorted(df_caixa["data"].astype(str).str[:7].unique().tolist(), reverse=True)
        if mes_atual not in meses_disponiveis:
            meses_disponiveis.insert(0, mes_atual)

    col1, col2 = st.columns([2, 1])
    with col1:
        mes_sel = st.selectbox("Periodo", meses_disponiveis)
    with col2:
        if st.button("Recalcular P&L", type="primary"):
            st.cache_data.clear()

    pnl = calcular_pnl_mes(mes_sel)
    receita = pnl["receita_total"]

    if receita == 0:
        st.warning(f"Sem dados de faturacao para {mes_sel}. Regista fechos de caixa primeiro.")
        # Permitir entrada manual de custos fixos
        _lancamento_custos_fixos(mes_sel)
        return

    # --- Demonstracao de Resultados ---
    st.subheader(f"Demonstracao de Resultados — {mes_sel}")

    linhas_dr = [
        ("Receita Total", receita, 100.0, False),
        ("Food Cost", -pnl["food_cost_real"], -pnl["food_cost_pct"], True),
        ("Margem Bruta", receita - pnl["food_cost_real"],
         (receita - pnl["food_cost_real"]) / receita * 100 if receita else 0, False),
        ("Labour Cost (Salarios + SS)", -pnl["labor_cost"], -pnl["labor_pct"], True),
        ("Renda", -pnl["renda"], -pnl["renda"]/receita*100 if receita else 0, True),
        ("Energia e Agua", -pnl["energia"], -pnl["energia"]/receita*100 if receita else 0, True),
        ("Outros Custos Operacionais", -pnl["outros_opex"], -pnl["outros_opex"]/receita*100 if receita else 0, True),
        ("EBITDA", pnl["ebitda"], pnl["ebitda_pct"], False),
    ]

    for nome, valor, pct, e_custo in linhas_dr:
        col_n, col_v, col_p = st.columns([3, 2, 1])
        is_ebitda = nome == "EBITDA"
        is_subtotal = nome in ["Margem Bruta", "EBITDA"]
        if is_subtotal:
            st.divider()
        with col_n:
            if is_subtotal:
                st.markdown(f"**{nome}**")
            else:
                st.write(nome)
        with col_v:
            color = "green" if valor >= 0 else "red"
            if is_subtotal:
                st.markdown(f"**{formatar_eur(abs(valor))}**")
            else:
                st.write(formatar_eur(abs(valor)))
        with col_p:
            st.write(f"{abs(pct):.1f}%")

    st.divider()

    # --- KPIs semaforo ---
    st.subheader("Semaforo de saude financeira")
    c1, c2, c3, c4 = st.columns(4)
    fc_icon = "✅" if pnl["food_cost_pct"] <= 33 else ("⚠️" if pnl["food_cost_pct"] <= 38 else "🔴")
    lab_icon = "✅" if pnl["labor_pct"] <= 30 else ("⚠️" if pnl["labor_pct"] <= 35 else "🔴")
    prime_cost = pnl["food_cost_pct"] + pnl["labor_pct"]
    prime_icon = "✅" if prime_cost <= 63 else ("⚠️" if prime_cost <= 68 else "🔴")
    ebitda_icon = "✅" if pnl["ebitda_pct"] >= 15 else ("⚠️" if pnl["ebitda_pct"] >= 10 else "🔴")

    c1.metric(f"{fc_icon} Food Cost", f"{pnl['food_cost_pct']:.1f}%", delta=f"{pnl['food_cost_pct']-33:.1f}pp vs 33%")
    c2.metric(f"{lab_icon} Labour Cost", f"{pnl['labor_pct']:.1f}%", delta=f"{pnl['labor_pct']-30:.1f}pp vs 30%")
    c3.metric(f"{prime_icon} Prime Cost", f"{prime_cost:.1f}%", delta=f"{prime_cost-63:.1f}pp vs 63%")
    c4.metric(f"{ebitda_icon} EBITDA", f"{pnl['ebitda_pct']:.1f}%", delta=f"{pnl['ebitda_pct']-15:.1f}pp vs 15%")

    # --- Grafico composicao de custos ---
    st.subheader("Composicao de Custos")
    custos_labels = ["Food Cost","Labour","Renda","Energia","Outros","EBITDA"]
    custos_vals = [pnl["food_cost_real"], pnl["labor_cost"], pnl["renda"], pnl["energia"], pnl["outros_opex"], max(pnl["ebitda"],0)]
    custos_vals = [v for v in custos_vals]
    fig = go.Figure(go.Pie(
        labels=custos_labels, values=custos_vals,
        hole=0.4,
        marker_colors=["#ef4444","#f97316","#a855f7","#3b82f6","#6b7280","#22c55e"]
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#F0F0F0",
        title=f"Distribuicao de {formatar_eur(receita)} de receita"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Historico 12 meses ---
    st.subheader("Evolucao dos ultimos 12 meses")
    historico = []
    for m in meses_disponiveis[:12]:
        p = calcular_pnl_mes(m)
        if p["receita_total"] > 0:
            historico.append(p)

    if len(historico) > 1:
        df_hist = pd.DataFrame(historico)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Receita", x=df_hist["mes"], y=df_hist["receita_total"], marker_color="#E8A427"))
        fig2.add_trace(go.Scatter(name="EBITDA %", x=df_hist["mes"], y=df_hist["ebitda_pct"], mode="lines+markers", yaxis="y2", marker_color="#22c55e"))
        fig2.update_layout(
            yaxis=dict(title="€"), yaxis2=dict(title="%", overlaying="y", side="right"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F0F0F0",
            legend=dict(orientation="h")
        )
        st.plotly_chart(fig2, use_container_width=True)

    # --- Lancamento de custos fixos ---
    _lancamento_custos_fixos(mes_sel)


def _lancamento_custos_fixos(mes: str):
    st.divider()
    st.subheader("Lancar custos fixos do mes")
    with st.form("custos_fixos"):
        c1, c2 = st.columns(2)
        with c1:
            categoria = st.selectbox("Categoria", ["Renda","Luz/Energia","Agua","Gas","Contabilidade","Seguros","Internet","Marketing","Limpeza","Outros"])
            valor = st.number_input("Valor (€)", min_value=0.0, step=10.0, format="%.2f")
        with c2:
            mes_custo = st.text_input("Mes (AAAA-MM)", value=mes)
            notas = st.text_input("Notas")
        submeter = st.form_submit_button("Lancar custo", type="primary")
    if submeter and valor > 0:
        if write_row("custos_fixos", [mes_custo, categoria, round(valor,2), notas]):
            st.success(f"Custo de {formatar_eur(valor)} lancado para {mes_custo}")
            st.rerun()
