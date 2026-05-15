"""Sprint 4 — Menu Engineering: matriz popularidade x rentabilidade."""

import streamlit as st
import pandas as pd
import plotly.express as px
from data.sheets_client import read_sheet, formatar_eur
from modules.food_cost import calcular_food_cost_prato


def render():
    st.title("🗺️ Menu Engineering")
    st.caption("Classifica cada prato por popularidade e rentabilidade para optimizar a carta.")

    df_vendas = read_sheet("vendas_diarias")
    df_pratos = read_sheet("pratos")
    df_fichas = read_sheet("fichas_tecnicas")
    df_ings = read_sheet("ingredientes")

    if df_pratos.empty:
        st.warning("Sem pratos registados.")
        return

    # Calcular popularidade e margem por prato
    dados = []
    total_vendas = 0

    for _, prato in df_pratos.iterrows():
        if str(prato.get("activo","TRUE")).upper() != "TRUE":
            continue
        prato_id = str(prato.get("id",""))
        nome = prato.get("nome","")
        preco = float(str(prato.get("preco_venda_eur",0)).replace(",",".") or 0)

        # Quantidade vendida
        qtd_vendida = 0
        if not df_vendas.empty and "prato_id" in df_vendas.columns:
            v = df_vendas[df_vendas["prato_id"].astype(str) == prato_id]
            if not v.empty and "quantidade" in v.columns:
                qtd_vendida = pd.to_numeric(v["quantidade"], errors="coerce").fillna(0).sum()

        # Margem bruta
        fc_pct, _ = calcular_food_cost_prato(prato_id, df_fichas, df_ings, preco)
        if fc_pct is not None:
            custo = preco * fc_pct / 100
            margem = preco - custo
        else:
            margem = preco * 0.65  # Estimativa se nao houver ficha

        total_vendas += qtd_vendida
        dados.append({
            "id": prato_id, "nome": nome, "preco": preco,
            "qtd_vendida": qtd_vendida, "margem": margem,
            "fc_pct": fc_pct
        })

    if not dados:
        st.info("Sem dados suficientes para análise.")
        return

    # Classificar
    media_qtd = total_vendas / len(dados) if dados else 0
    media_margem = sum(d["margem"] for d in dados) / len(dados) if dados else 0

    for d in dados:
        pop = "Alta" if d["qtd_vendida"] >= media_qtd else "Baixa"
        rent = "Alta" if d["margem"] >= media_margem else "Baixa"
        if pop == "Alta" and rent == "Alta":
            d["quadrante"] = "⭐ Stars"
        elif pop == "Alta" and rent == "Baixa":
            d["quadrante"] = "💰 Cash Cows"
        elif pop == "Baixa" and rent == "Alta":
            d["quadrante"] = "🧩 Puzzles"
        else:
            d["quadrante"] = "🐕 Dogs"

    df_me = pd.DataFrame(dados)

    # Gráfico scatter
    st.subheader("Matriz Popularidade × Rentabilidade")
    if df_me["qtd_vendida"].sum() > 0:
        fig = px.scatter(
            df_me, x="margem", y="qtd_vendida", text="nome",
            color="quadrante",
            color_discrete_map={"⭐ Stars":"#E8A427","💰 Cash Cows":"#22c55e","🧩 Puzzles":"#3b82f6","🐕 Dogs":"#ef4444"},
            labels={"margem":"Margem Bruta (€)","qtd_vendida":"Quantidade Vendida"},
            title="Menu Engineering Matrix"
        )
        fig.add_vline(x=media_margem, line_dash="dash", line_color="gray")
        fig.add_hline(y=media_qtd, line_dash="dash", line_color="gray")
        fig.update_traces(textposition="top center")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F0F0F0")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de vendas ainda. Importa vendas do Winrest para ver a matriz.")

    # Tabela por quadrante
    st.subheader("Pratos por quadrante")
    cols = ["nome","quadrante","qtd_vendida","margem","preco","fc_pct"]
    cols_ex = [c for c in cols if c in df_me.columns]
    df_show = df_me[cols_ex].sort_values("quadrante")
    df_show = df_show.rename(columns={"nome":"Prato","quadrante":"Quadrante","qtd_vendida":"Qtd Vendida","margem":"Margem €","preco":"Preco €","fc_pct":"FC %"})
    st.dataframe(df_show, use_container_width=True)

    # Recomendações
    st.subheader("Recomendações")
    for quad, rec in [
        ("⭐ Stars", "Mantém e promove. São os teus melhores pratos."),
        ("💰 Cash Cows", "Sao populares mas pouco rentaveis. Tenta subir preço ou reduzir custo."),
        ("🧩 Puzzles", "Boa margem mas pouca saida. Destaca no menu e treina a equipa a sugerir."),
        ("🐕 Dogs", "Pouca venda e pouca margem. Considera retirar da carta."),
    ]:
        pratos = [d["nome"] for d in dados if d["quadrante"] == quad]
        if pratos:
            with st.expander(f"{quad} — {rec}"):
                for p in pratos:
                    st.write(f"• {p}")
