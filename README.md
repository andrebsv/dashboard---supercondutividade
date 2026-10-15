# 🌡️ Superconductivity Critical Temperature Analysis & Dashboard

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

Este projeto realiza uma **Análise Exploratória de Dados (EDA)** detalhada e constrói um **Dashboard Interativo** para investigar e prever a **Temperatura Crítica ($T_c$)** de materiais supercondutores.

O objetivo principal é compreender os fatores físico-químicos e estequiométricos que influenciam a supercondutividade, com ênfase na identificação de materiais com $T_c \ge 77\text{ K}$ (limiar de viabilidade económica utilizando nitrogénio líquido).

---

## 👥 Integrantes do Projeto

* **André Bispo**
* **Marco Matheus**

---

## 📌 Principais Descobertas e Insights Físicos

1. **Taxonomia dos Supercondutores**:
   * **Cupratos** ($Cu + O$): Dominam a categoria de alta temperatura ($T_c$), com **$35,3\%$** dos seus compostos atingindo ou superando o limiar viável de $77\text{ K}$.
   * **Pnictetos / Base de Ferro** ($Fe + As/Se/P/Te/S$) e **Outros**: Apresentam baixas temperaturas críticas (mediana em torno de $19\text{ K}$ e $4,2\text{ K}$, respetivamente).
2. **Correlatos Físico-Químicos de Destaque**:
   * **Maior Correlação Positiva ($r \approx +0,72$)**: `wtd_std_ThermalConductivity` (Desvio Padrão Ponderado da Condutividade Térmica), indicando que a heterogeneidade térmica na estrutura cristalina favorece altas $T_c$.
   * **Maior Correlação Negativa ($r \approx -0,63$)**: `wtd_mean_Valence` (Média Ponderada da Valência), sugerindo que altas densidades de elétrons de valência tendem a suprimir a temperatura crítica.
3. **Impacto Elementar**:
   * Elementos como **Cobre ($Cu$)**, **Bismuto ($Bi$)**, **Ítrio ($Y$)** e **Oxigénio ($O$)** atuam como os principais impulsionadores do aumento de $T_c$.

---

## 🧹 Pipeline de Limpeza e Tratamento de Dados (`preparacao.py`)

A base bruta original continha $21.263$ amostras obtidas da literatura. O script de preparação aplica uma série de tratamentos para evitar contaminação e *data leakage*:

* **Alinhamento e Validação**: Cruzamento linha a linha entre características físico-químicas (`train.csv`) e fórmula química textual (`unique_m.csv`).
* **Normalização Estequiométrica**: Conversão de proporções para frações molares arredondadas, unificando sinónimos quimicamente equivalentes (ex: $Si_{0.25}V_{0.75}$ e $Si_1V_3$).
* **Agregação sem Perda de Dados**: Consolidação de $21.263$ linhas em **$15.136$ composições únicas**, utilizando a **mediana estatística** para definir a $T_c$ de compostos com múltiplas medições.
* **Engenharia de Features**: Criação de classificadores de família (`Cuprato`, `Base de ferro`, `Outros`), indicador de viabilidade económica (`acima_77k`) e métricas de incerteza de medição.

---

## 🖥️ Dashboard Interativo (`app.py`)

Desenvolvido em **Streamlit** e **Plotly**, o dashboard permite explorar os dados tratados através de 5 abas dinâmicas:

1. **📊 Distribuição**: Histograma personalizável e Boxplots comparativos por família ou número de elementos.
2. **📈 Relação Atributo × $T_c$**: Gráficos de dispersão interativos entre qualquer uma das 81 propriedades físicas e a $T_c$, com cálculo de correlação em tempo real (Pearson e Spearman).
3. **🔗 Correlações**: Ranking de atributos mais impactantes e Matriz de Correlação (*Heatmap*) para identificação de multicolinearidade.
4. **🧪 Composição Química**: Análise comparativa do impacto de cada elemento químico na $T_c$ (composição com vs. sem o elemento).
5. **📁 Dados**: Tabela interativa com filtros aplicados e exportação de relatórios customizados em formato CSV.

---

## 📂 Estrutura do Repositório

```text
.
├── dados/
│   ├── train.csv         # Dados brutos com atributos físico-químicos (21.263 x 82)
│   └── unique_m.csv      # Dados brutos com fórmulas químicas e elementos (21.263 x 88)
├── preparacao.py         # Pipeline de ETL, tratamento, agregação e utilitários
├── app.py                # Aplicação Streamlit do Dashboard interativo
├── README.md             # Documentação do projeto
└── requirements.txt      # Dependências do projeto
