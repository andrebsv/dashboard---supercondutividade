import pandas as pd
import numpy as np

PASTA_DADOS = "dados"
TEMPERATURA_NITROGENIO_LIQUIDO = 77

PROPRIEDADES = {
    "atomic_mass": "Massa atômica",
    "fie": "Primeira energia de ionização",
    "atomic_radius": "Raio atômico",
    "Density": "Densidade",
    "ElectronAffinity": "Afinidade eletrônica",
    "FusionHeat": "Calor de fusão",
    "ThermalConductivity": "Condutividade térmica",
    "Valence": "Valência",
}

ESTATISTICAS = {
    "mean": "Média",
    "wtd_mean": "Média ponderada",
    "gmean": "Média geométrica",
    "wtd_gmean": "Média geométrica ponderada",
    "entropy": "Entropia",
    "wtd_entropy": "Entropia ponderada",
    "range": "Amplitude",
    "wtd_range": "Amplitude ponderada",
    "std": "Desvio padrão",
    "wtd_std": "Desvio padrão ponderado",
}

ORDEM_FAMILIAS = ["Cuprato", "Base de ferro", "Outros"]


def carregar_dados_brutos(pasta=PASTA_DADOS):
    atributos = pd.read_csv(f"{pasta}/train.csv")
    composicao = pd.read_csv(f"{pasta}/unique_m.csv")
    return atributos, composicao


def colunas_elementos(composicao):
    return [c for c in composicao.columns if c not in ("critical_temp", "material")]


def unir_bases(atributos, composicao):
    if not (atributos["critical_temp"].values == composicao["critical_temp"].values).all():
        raise ValueError("As duas bases não estão alinhadas linha a linha")
    base = atributos.copy()
    base["material"] = composicao["material"]
    elementos = colunas_elementos(composicao)
    base = pd.concat([base, composicao[elementos]], axis=1)
    return base, elementos


def classificar_familia(base):
    tem = lambda simbolo: base[simbolo] > 0
    cuprato = tem("Cu") & tem("O")
    base_ferro = tem("Fe") & (tem("As") | tem("Se") | tem("P") | tem("Te") | tem("S"))
    familia = np.select([cuprato, base_ferro], ["Cuprato", "Base de ferro"], default="Outros")
    return pd.Categorical(familia, categories=ORDEM_FAMILIAS, ordered=True)


def chave_composicao(base, elementos):
    proporcoes = base[elementos].div(base[elementos].sum(axis=1), axis=0).round(4)
    return proporcoes.apply(lambda linha: ";".join(f"{el}{v}" for el, v in linha[linha > 0].items()), axis=1)


def tratar_dados(atributos, composicao):
    base, elementos = unir_bases(atributos, composicao)
    base["composicao"] = chave_composicao(base, elementos)
    colunas_fixas = [c for c in base.columns if c not in ("critical_temp", "material", "composicao")]
    agrupado = base.groupby("composicao", as_index=False).agg(
        material=("material", "first"),
        critical_temp=("critical_temp", "median"),
        qtd_medicoes=("critical_temp", "size"),
        amplitude_medicoes=("critical_temp", lambda s: s.max() - s.min()),
    )
    caracteristicas = base.drop_duplicates("composicao")[["composicao"] + colunas_fixas]
    tratado = agrupado.merge(caracteristicas, on="composicao", how="left").drop(columns="composicao")
    tratado["familia"] = classificar_familia(tratado)
    tratado["acima_77k"] = np.where(
        tratado["critical_temp"] >= TEMPERATURA_NITROGENIO_LIQUIDO, "Tc ≥ 77 K", "Tc < 77 K"
    )
    return tratado, elementos


def carregar_dados_tratados(pasta=PASTA_DADOS):
    atributos, composicao = carregar_dados_brutos(pasta)
    return tratar_dados(atributos, composicao)


def nome_atributo(coluna):
    if coluna == "number_of_elements":
        return "Número de elementos"
    for chave_estat in sorted(ESTATISTICAS, key=len, reverse=True):
        prefixo = chave_estat + "_"
        if coluna.startswith(prefixo):
            propriedade = coluna[len(prefixo):]
            if propriedade in PROPRIEDADES:
                return f"{ESTATISTICAS[chave_estat]} — {PROPRIEDADES[propriedade]}"
    return coluna


def colunas_atributos(atributos):
    return [c for c in atributos.columns if c != "critical_temp"]
