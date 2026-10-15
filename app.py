import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from preparacao import (
    carregar_dados_tratados,
    nome_atributo,
    PROPRIEDADES,
    ESTATISTICAS,
    ORDEM_FAMILIAS,
    TEMPERATURA_NITROGENIO_LIQUIDO,
)

st.set_page_config(page_title="Supercondutores — Temperatura Crítica", layout="wide")

CORES_FAMILIA = {"Cuprato": "#d1495b", "Base de ferro": "#edae49", "Outros": "#00798c"}


@st.cache_data
def obter_dados():
    dados, elementos = carregar_dados_tratados()
    dados["familia"] = dados["familia"].astype(str)
    return dados, elementos


@st.cache_data
def presenca_elementos(dados, elementos):
    return dados[elementos] > 0


def montar_coluna(estatistica, propriedade):
    return f"{estatistica}_{propriedade}"


dados, elementos = obter_dados()
presenca = presenca_elementos(dados, elementos)
elementos_existentes = [el for el in elementos if presenca[el].any()]
colunas_numericas = ["number_of_elements"] + [
    montar_coluna(e, p) for p in PROPRIEDADES for e in ESTATISTICAS
]

st.title("Temperatura crítica de materiais supercondutores")

with st.sidebar:
    st.header("Filtros")
    familias_sel = st.multiselect("Família do material", ORDEM_FAMILIAS, default=ORDEM_FAMILIAS)
    min_el, max_el = int(dados["number_of_elements"].min()), int(dados["number_of_elements"].max())
    faixa_elementos = st.slider("Número de elementos", min_el, max_el, (min_el, max_el))
    tc_max = float(dados["critical_temp"].max())
    faixa_tc = st.slider("Temperatura crítica (K)", 0.0, float(round(tc_max + 1)), (0.0, float(round(tc_max + 1))))
    elementos_obrig = st.multiselect("Contém os elementos", elementos_existentes)
    elementos_excl = st.multiselect("Não contém os elementos", elementos_existentes)
    apenas_unica = st.checkbox("Somente composições com uma única medição", value=False)

filtro = (
    dados["familia"].isin(familias_sel)
    & dados["number_of_elements"].between(*faixa_elementos)
    & dados["critical_temp"].between(*faixa_tc)
)
for el in elementos_obrig:
    filtro &= presenca[el]
for el in elementos_excl:
    filtro &= ~presenca[el]
if apenas_unica:
    filtro &= dados["qtd_medicoes"] == 1

df = dados[filtro]

if df.empty:
    st.warning("Nenhum material atende aos filtros selecionados.")
    st.stop()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Materiais", f"{len(df):,}".replace(",", "."))
k2.metric("Média de Tc (K)", f"{df['critical_temp'].mean():.1f}")
k3.metric("Mediana de Tc (K)", f"{df['critical_temp'].median():.1f}")
k4.metric("Desvio padrão (K)", f"{df['critical_temp'].std():.1f}" if len(df) > 1 else "—")
k5.metric("Máximo de Tc (K)", f"{df['critical_temp'].max():.1f}")
k6.metric(f"% com Tc ≥ {TEMPERATURA_NITROGENIO_LIQUIDO} K", f"{(df['critical_temp'] >= TEMPERATURA_NITROGENIO_LIQUIDO).mean() * 100:.1f}%")

aba_dist, aba_rel, aba_corr, aba_comp, aba_tabela = st.tabs(
    ["Distribuição", "Relação entre atributo e Tc", "Correlações", "Composição química", "Dados"]
)

with aba_dist:
    c1, c2 = st.columns([1, 3])
    with c1:
        bins = st.slider("Número de classes do histograma", 10, 150, 60)
        separar = st.checkbox("Separar por família", value=False)
        mostrar_linha = st.checkbox(f"Mostrar linha de {TEMPERATURA_NITROGENIO_LIQUIDO} K", value=False)
    with c2:
        fig_hist = px.histogram(
            df, x="critical_temp", nbins=bins,
            color="familia" if separar else None,
            color_discrete_map=CORES_FAMILIA,
            category_orders={"familia": ORDEM_FAMILIAS},
            barmode="overlay" if separar else "relative",
            opacity=0.7 if separar else 1,
            labels={"critical_temp": "Temperatura crítica (K)", "familia": "Família"},
            title="Distribuição da temperatura crítica",
        )
        fig_hist.update_layout(yaxis_title="Quantidade de materiais")
        if mostrar_linha:
            fig_hist.add_vline(x=TEMPERATURA_NITROGENIO_LIQUIDO, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_hist, width="stretch")

    agrupar_por = st.radio("Comparar Tc por", ["Família", "Número de elementos"], horizontal=True)
    eixo_x = "familia" if agrupar_por == "Família" else "number_of_elements"
    fig_box = px.box(
        df.sort_values("number_of_elements"), x=eixo_x, y="critical_temp",
        color="familia" if agrupar_por == "Família" else None,
        color_discrete_map=CORES_FAMILIA,
        category_orders={"familia": ORDEM_FAMILIAS},
        points=False,
        labels={"critical_temp": "Temperatura crítica (K)", "familia": "Família", "number_of_elements": "Número de elementos"},
        title=f"Temperatura crítica por {agrupar_por.lower()}",
    )
    fig_box.update_xaxes(type="category")
    st.plotly_chart(fig_box, width="stretch")

with aba_rel:
    c1, c2, c3 = st.columns(3)
    prop_sel = c1.selectbox("Propriedade", list(PROPRIEDADES), format_func=PROPRIEDADES.get, index=6)
    estat_sel = c2.selectbox("Estatística", list(ESTATISTICAS), format_func=ESTATISTICAS.get, index=9)
    cor_por = c3.selectbox("Colorir por", ["Família", "Número de elementos", "Nenhum"])
    coluna_x = montar_coluna(estat_sel, prop_sel)
    escala_log = st.checkbox("Eixo Y em escala logarítmica", value=False)

    cor = {"Família": "familia", "Número de elementos": "number_of_elements", "Nenhum": None}[cor_por]
    amostra = df.sample(min(len(df), 8000), random_state=42)
    fig_disp = px.scatter(
        amostra, x=coluna_x, y="critical_temp", color=cor,
        color_discrete_map=CORES_FAMILIA,
        category_orders={"familia": ORDEM_FAMILIAS},
        opacity=0.45, log_y=escala_log,
        hover_data=["material"],
        labels={coluna_x: nome_atributo(coluna_x), "critical_temp": "Temperatura crítica (K)", "familia": "Família", "number_of_elements": "Nº de elementos"},
        title=f"{nome_atributo(coluna_x)} × Temperatura crítica",
    )
    fig_disp.update_traces(marker_size=5)
    st.plotly_chart(fig_disp, width="stretch")

    if len(df) > 2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Correlação de Pearson", f"{df[coluna_x].corr(df['critical_temp']):.3f}")
        m2.metric("Correlação de Spearman", f"{df[coluna_x].corr(df['critical_temp'], method='spearman'):.3f}")
        m3.metric("Pontos exibidos", f"{len(amostra):,}".replace(",", "."))

    fig_hist_attr = px.histogram(
        df, x=coluna_x, nbins=60, color=cor if cor == "familia" else None,
        color_discrete_map=CORES_FAMILIA, barmode="overlay", opacity=0.7,
        category_orders={"familia": ORDEM_FAMILIAS},
        labels={coluna_x: nome_atributo(coluna_x), "familia": "Família"},
        title=f"Distribuição de {nome_atributo(coluna_x).lower()}",
    )
    fig_hist_attr.update_layout(yaxis_title="Quantidade de materiais")
    st.plotly_chart(fig_hist_attr, width="stretch")

with aba_corr:
    c1, c2, c3 = st.columns(3)
    metodo = c1.radio("Método", ["pearson", "spearman"], format_func=str.capitalize, horizontal=True)
    qtd_top = c2.slider("Quantidade de atributos", 5, 40, 15)
    ordenar = c3.radio("Ordenar por", ["Valor absoluto", "Valor"], horizontal=True)

    if len(df) > 2:
        correlacoes = df[colunas_numericas].corrwith(df["critical_temp"], method=metodo).dropna()
        if ordenar == "Valor absoluto":
            selecionadas = correlacoes.reindex(correlacoes.abs().sort_values(ascending=False).index).head(qtd_top)
        else:
            selecionadas = correlacoes.sort_values(ascending=False).head(qtd_top)
        tabela_corr = pd.DataFrame({
            "atributo": [nome_atributo(c) for c in selecionadas.index],
            "correlacao": selecionadas.values,
        }).iloc[::-1]
        fig_barras = px.bar(
            tabela_corr, x="correlacao", y="atributo", orientation="h",
            color="correlacao", color_continuous_scale="RdBu", range_color=[-1, 1],
            labels={"correlacao": f"Correlação ({metodo.capitalize()})", "atributo": ""},
            title="Correlação dos atributos com a temperatura crítica",
        )
        fig_barras.update_layout(height=max(400, 28 * len(tabela_corr)))
        st.plotly_chart(fig_barras, width="stretch")

        padrao_heatmap = [c for c in ["wtd_std_ThermalConductivity", "range_atomic_radius", "number_of_elements", "wtd_mean_Valence", "gmean_Density"] if c in colunas_numericas]
        escolhidas = st.multiselect(
            "Atributos da matriz de correlação", colunas_numericas,
            default=padrao_heatmap, format_func=nome_atributo,
        )
        if len(escolhidas) >= 2:
            matriz = df[escolhidas + ["critical_temp"]].corr(method=metodo)
            rotulos = [nome_atributo(c) for c in escolhidas] + ["Temperatura crítica"]
            fig_mapa = go.Figure(go.Heatmap(
                z=matriz.values, x=rotulos, y=rotulos, zmin=-1, zmax=1,
                colorscale="RdBu", text=matriz.round(2).values, texttemplate="%{text}",
            ))
            fig_mapa.update_layout(title="Matriz de correlação entre atributos", height=150 + 55 * len(rotulos))
            st.plotly_chart(fig_mapa, width="stretch")

with aba_comp:
    c1, c2 = st.columns(2)
    min_ocorrencias = c1.slider("Mínimo de materiais contendo o elemento", 10, 1000, 200, step=10)
    medida = c2.radio("Medida", ["Mediana", "Média"], horizontal=True)
    funcao = "median" if medida == "Mediana" else "mean"

    presenca_filtrada = presenca.loc[df.index, elementos_existentes]
    contagem = presenca_filtrada.sum()
    validos = contagem[contagem >= min_ocorrencias].index
    if len(validos) == 0:
        st.info("Nenhum elemento atinge o mínimo de ocorrências com os filtros atuais.")
    else:
        linhas = []
        for el in validos:
            linhas.append({
                "elemento": el,
                "materiais": int(contagem[el]),
                "com": getattr(df.loc[presenca_filtrada[el], "critical_temp"], funcao)(),
                "sem": getattr(df.loc[~presenca_filtrada[el], "critical_temp"], funcao)(),
            })
        tabela_el = pd.DataFrame(linhas).sort_values("com", ascending=False)
        longa = tabela_el.melt(id_vars=["elemento", "materiais"], value_vars=["com", "sem"], var_name="grupo", value_name="tc")
        longa["grupo"] = longa["grupo"].map({"com": "Contém o elemento", "sem": "Não contém o elemento"})
        fig_el = px.bar(
            longa, x="elemento", y="tc", color="grupo", barmode="group",
            hover_data=["materiais"],
            color_discrete_sequence=["#30638e", "#b8c4cc"],
            labels={"tc": f"{medida} de Tc (K)", "elemento": "Elemento", "grupo": ""},
            title=f"{medida} da temperatura crítica com e sem cada elemento",
        )
        st.plotly_chart(fig_el, width="stretch")

    frequencia = contagem.sort_values(ascending=False).head(30).rename("materiais").rename_axis("elemento").reset_index()
    fig_freq = px.bar(
        frequencia, x="elemento", y="materiais",
        labels={"elemento": "Elemento", "materiais": "Quantidade de materiais"},
        title="Elementos mais frequentes nos materiais filtrados",
    )
    fig_freq.update_layout(yaxis_title="Quantidade de materiais")
    st.plotly_chart(fig_freq, width="stretch")

with aba_tabela:
    colunas_tabela = ["material", "critical_temp", "familia", "number_of_elements", "qtd_medicoes", "amplitude_medicoes"]
    st.dataframe(
        df[colunas_tabela].rename(columns={
            "material": "Material", "critical_temp": "Tc (K)", "familia": "Família",
            "number_of_elements": "Nº de elementos", "qtd_medicoes": "Medições", "amplitude_medicoes": "Amplitude entre medições (K)",
        }),
        width="stretch", hide_index=True,
    )
    st.download_button(
        "Baixar dados filtrados (CSV)",
        df[colunas_tabela].to_csv(index=False).encode("utf-8"),
        file_name="supercondutores_filtrado.csv", mime="text/csv",
    )
