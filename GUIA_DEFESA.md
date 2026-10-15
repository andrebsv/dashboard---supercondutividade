# Guia para a defesa oral

Este arquivo é só pra estudo da dupla, não precisa entregar. Os números batem com o notebook rodado na base tratada.

---

## 1. Contexto e escolha do dataset (Critério 1 — 15%)

**O que é supercondutividade:** abaixo de uma certa temperatura, a **temperatura crítica (Tc)**, alguns materiais passam a conduzir eletricidade com resistência zero. Aplicações: ressonância magnética, trens maglev, aceleradores de partículas, cabos sem perda de energia.

**Por que Tc importa tanto:** quanto mais alta, mais barato é resfriar o material.
- Abaixo de ~20 K precisa de hélio líquido (4,2 K), que é caro e escasso.
- A partir de **77 K** dá pra usar **nitrogênio líquido**, que é barato. Por isso 77 K é um marco físico, e é por isso que o dashboard tem a linha/indicador de 77 K.

**De onde vêm os dados:** artigo do Kam Hamidieh (2018), a partir do banco **SuperCon** do NIMS (instituto de materiais do Japão). São 21.263 registros e dois arquivos:
- `train.csv`: 81 atributos numéricos + `critical_temp`.
- `unique_m.csv`: a fórmula química (`material`) e a quantidade de cada um dos 86 elementos.

**Como os 81 atributos foram construídos:** 8 propriedades dos elementos (massa atômica, 1ª energia de ionização, raio atômico, densidade, afinidade eletrônica, calor de fusão, condutividade térmica e valência) × 10 estatísticas = 80, mais o `number_of_elements`.

As 10 estatísticas, usando a propriedade dos elementos que formam o material:

| Estatística | O que mede |
|---|---|
| mean | média simples dos elementos |
| wtd_mean | média ponderada pela proporção de cada elemento na fórmula |
| gmean / wtd_gmean | média geométrica (simples / ponderada) |
| entropy / wtd_entropy | entropia de Shannon: quanto a propriedade está "espalhada" entre os elementos (mais elementos com valores parecidos → maior) |
| range / wtd_range | amplitude (maior − menor) |
| std / wtd_std | desvio padrão |

Exemplo: no Y1Ba2Cu3O7 (o YBCO), a média simples da massa atômica trata Y, Ba, Cu e O igual; a ponderada dá mais peso ao O, que aparece 7 vezes.

**Justificativa da escolha:**
- Base grande (21 mil registros) e sem valores ausentes, o que deixa a análise focar em estatística e não em "limpar sujeira".
- Muitas variáveis numéricas contínuas → dá pra trabalhar distribuição, assimetria, correlação (Pearson e Spearman) e multicolinearidade.
- Tem uma variável-alvo clara (Tc) com significado físico e um limiar real (77 K).
- Tem problemas de qualidade interessantes de verdade (fórmulas repetidas com Tc diferente), que exigem decisão.

**Limitações (o professor adora isso):**
- Os atributos vêm **só da composição química**. Não tem estrutura cristalina, pressão aplicada nem método de síntese — e isso afeta muito o Tc.
- A mesma fórmula aparece com Tc diferentes (medições diferentes, amostras diferentes, pressões diferentes).
- O H₂S tem medições de 60 K e 185 K: o 185 K foi medido sob pressão altíssima (~150 GPa), o que o dataset não registra.
- Viés de pesquisa: cupratos foram muito estudados, então estão super-representados (o YBCO aparece 110 vezes).
- Algumas fórmulas parecem ter erro de digitação no banco original, ex.: `Bi2Sr2Ca2O` com Tc de 109 K provavelmente é um cuprato BSCCO com o Cu omitido. Não corrigimos porque não dá pra confirmar sem a fonte.

---

## 2. Tratamento dos dados (Critério 3 — 15%)

Todo tratamento está em `preparacao.py`, função `tratar_dados`. Resultado: **21.263 linhas → 15.136 linhas (uma por composição)**.

**2.1 Valores ausentes:** nenhum (`isna().sum()` = 0). Nada a fazer.

**2.2 Junção das duas bases:** antes de juntar, conferimos que o Tc é igual linha a linha nos dois arquivos. Se não fosse, o código levanta erro.

**2.3 Fórmulas repetidas com Tc diferente (decisão principal)**
- 15.542 fórmulas distintas, mas 7.982 linhas são de fórmulas que aparecem mais de uma vez.
- Dentro da mesma fórmula, **todos os 81 atributos são idênticos** (verificado no notebook). Só o Tc muda.
- Isso quer dizer que o mesmo "ponto x" aparece com vários "y". Se deixar assim, materiais muito estudados pesam muito mais: o YBCO contaria 110 vezes na média e nas correlações.
- **Decisão:** agrupar e usar a **mediana** do Tc.
- **Por que mediana e não média:** a mediana é robusta a valores extremos. Ex.: H₂S tem 60 K e 185 K; YBCO tem amplitude de quase 100 K entre medições.
- **Alternativas consideradas:** (a) manter tudo — superpondera materiais famosos; (b) média — sensível a medições extremas; (c) máximo — representaria o "melhor caso", mas exagera.
- **Não jogamos a informação fora:** criamos `qtd_medicoes` e `amplitude_medicoes`. No dashboard tem o filtro "Somente composições com uma única medição", que permite ver se a conclusão muda quando se tira os materiais agrupados.
- **Impacto:** média 34,4 → 33,6 K; mediana 20,0 → 19,0 K; máximo 185 → 143 K.

**2.4 Mesma composição escrita de jeitos diferentes**
- O `train.csv` sozinho tem 66 linhas duplicadas. Investigando: são coisas como `Si1V3` e `Si0.25V0.75` — é o mesmo composto (proporção 1:3), só escrito diferente.
- **Decisão:** a chave do agrupamento não é o texto da fórmula, e sim as **proporções normalizadas** de cada elemento (cada quantidade dividida pela soma). Assim `Si1V3` e `Si0.25V0.75` viram a mesma composição. Isso levou de 15.542 para 15.136.

**2.5 Valores atípicos**
- **No Tc:** pelo critério do IQR (limite = Q3 + 1,5·IQR), na base original só o H₂S (185 K) passava. Depois do agrupamento, **nenhum** valor de Tc é outlier.
- Valores < 1 K **não foram removidos**: são supercondutores convencionais reais (metais e ligas simples).
- **Nos atributos:** algumas colunas têm até ~16% de pontos fora do IQR (ex.: desvio padrão da densidade). **Decisão: manter.** Motivos: (1) são valores físicos reais, não erro de medição; (2) as distribuições são assimétricas e o IQR marca muito ponto como "outlier" nesse caso; (3) remover apagaria justamente grupos químicos inteiros (ex.: materiais com elementos pesados).

**2.6 Variáveis criadas**
- `familia` (regra química aproximada):
  - **Cuprato:** contém Cu e O.
  - **Base de ferro:** contém Fe e algum de As, Se, P, Te, S (pnictídeos/calcogenetos de ferro).
  - **Outros:** o resto (convencionais, MgB₂, hidretos etc.).
  - Limitação: é regra, não classificação oficial. "Outros" mistura muita coisa e pega as fórmulas com erro de digitação.
- `acima_77k`: Tc ≥ 77 K ou não.

---

## 3. Análise exploratória e conceitos (Critério 2 — 20%)

**Resumo do Tc (base tratada, n = 15.136):**

| Medida | Valor |
|---|---|
| Média | 33,6 K |
| Mediana | 19,0 K |
| Moda (arredondada) | 2 K |
| Desvio padrão | 33,9 K |
| Coef. de variação | ~101% |
| Q1 / Q3 / IQR | 5 / 61 / 56 K |
| Mín / Máx | ~0 / 143 K |
| Assimetria | 0,88 |
| Curtose (excesso) | −0,48 |

**Como interpretar:**
- **Moda < mediana < média** → assimetria positiva (cauda à direita). O coeficiente de assimetria 0,88 confirma.
- **CV ≈ 101%** → dispersão enorme; o desvio padrão é do tamanho da média. A média sozinha representa mal a base.
- **Curtose negativa** → distribuição mais "achatada" que a normal (platicúrtica). Isso acontece porque a distribuição é **bimodal**: um pico enorme entre 0 e 10 K e um segundo pico entre ~75 e 95 K.
- Os dois picos são basicamente duas populações: os supercondutores convencionais (Tc baixo) e os cupratos (Tc alto). É por isso que o filtro/separação por família no histograma faz sentido.

**Correlação:**
- **Pearson:** mede relação **linear**. Vai de −1 a 1.
- **Spearman:** correlação de Pearson aplicada aos **postos (rankings)**. Mede relação **monotônica** (sempre cresce ou sempre decresce, mesmo que não em linha reta) e é menos sensível a outliers.
- Quando o Spearman é bem maior que o Pearson, a relação é monotônica mas não linear. Acontece aqui: média ponderada da valência tem Pearson −0,63 e Spearman −0,74; amplitude do raio atômico 0,66 vs 0,76.

**Atributos mais correlacionados com Tc:**

| Atributo | Pearson | Spearman |
|---|---|---|
| Desvio padrão ponderado — condutividade térmica | 0,72 | 0,71 |
| Amplitude — condutividade térmica | 0,69 | 0,72 |
| Amplitude — raio atômico | 0,66 | 0,76 |
| Média ponderada — valência | −0,63 | −0,74 |
| Número de elementos | 0,63 | 0,70 |
| Média geométrica — densidade | −0,55 | −0,60 |

**Multicolinearidade:** os próprios atributos são muito correlacionados entre si (ex.: desvio padrão ponderado da condutividade térmica × média ponderada da valência = −0,75). Muitas colunas carregam quase a mesma informação. Por isso o heatmap existe no dashboard.

**Correlação não é causalidade** — e aqui tem um exemplo concreto (ver padrões abaixo).

---

## 4. Padrões nos dados (Critério 5 — 15%)

1. **Família explica muito do Tc.** Mediana: cuprato 62 K, base de ferro 19 K, outros ~4 K. Dos cupratos, ~35% têm Tc ≥ 77 K; dos à base de ferro, **0%** (máximo 61,4 K); de "Outros", ~0,2%.
2. **Número de elementos × Tc:** a mediana sobe de ~3–6 K (1 a 3 elementos) para ~44 K (5 elementos) e ~61 K (6 elementos). Materiais simples quase nunca têm Tc alto.
3. **Padrão não evidente — confundimento (paradoxo de Simpson leve):** na base toda, número de elementos tem Spearman 0,70 com Tc. **Dentro de cada família**, cai para 0,14–0,20. O mesmo com o desvio padrão ponderado da condutividade térmica: 0,72 na base toda, 0,32 nos cupratos, ~0,04 em "Outros". Ou seja, boa parte da correlação geral acontece porque os cupratos têm muitos elementos **e** Tc alto ao mesmo tempo. A família é uma variável de confusão. Dá pra mostrar isso ao vivo no dashboard: filtra só uma família e olha a correlação na aba "Relação entre atributo e Tc".
4. **Elementos:** materiais com Hg, Ca, Ba, Tl e Cu têm mediana de Tc muito maior que os sem esses elementos (Hg: 83 K com vs ~18 K sem). São os elementos dos cupratos de Tc mais alto (os recordes da base são Hg-Ba-Ca-Cu-O, 143 K).
5. **Valência média baixa** está associada a Tc mais alto (correlação negativa), e de novo isso é bem mais forte na base inteira do que dentro de cada família.
6. **Medições repetidas variam muito:** das composições com mais de uma medição, a mediana da amplitude é ~2 K, mas há casos de ~100 K (YBCO). Isso mostra que a composição sozinha não define o Tc — estrutura, oxigenação e pressão contam.

---

## 5. Visualizações e por que cada uma existe (Critério 4 — 15%)

**Indicadores do topo (KPIs):** quantidade de materiais, média, mediana, desvio padrão, máximo e % acima de 77 K, sempre recalculados com o filtro. Média e mediana lado a lado deixam a assimetria visível.

**Aba Distribuição**
- **Histograma do Tc:** objetivo é mostrar a **forma da distribuição** (assimetria, bimodalidade). Histograma porque a variável é contínua. Opção de separar por família mostra que os picos vêm de populações diferentes. Linha de 77 K opcional.
- **Boxplot por família / por número de elementos:** objetivo é **comparar** mediana, quartis e dispersão entre grupos. Boxplot porque resume 5 números e compara grupos lado a lado melhor que vários histogramas.

**Aba Relação entre atributo e Tc**
- **Dispersão (atributo escolhido × Tc):** objetivo é mostrar a **relação** entre duas variáveis contínuas. O usuário escolhe propriedade e estatística (os 80 atributos). Cor por família revela o confundimento. Mostra Pearson e Spearman do filtro atual. Amostra de até 8.000 pontos pra não travar.
- **Histograma do atributo:** objetivo é ver a **distribuição do atributo** escolhido (ajuda a entender por que Pearson e Spearman divergem).

**Aba Correlações**
- **Barras horizontais de correlação com Tc:** objetivo é **ranquear** quais atributos se associam mais ao Tc. Barras horizontais porque os nomes são longos; cor divergente (vermelho/azul) pra separar positivo de negativo. Dá pra trocar Pearson/Spearman.
- **Heatmap:** objetivo é mostrar **multicolinearidade** entre atributos escolhidos pelo usuário.

**Aba Composição química**
- **Barras agrupadas com e sem cada elemento:** objetivo é **comparar** o Tc típico de materiais que contêm vs não contêm cada elemento. Tem mínimo de ocorrências pra não comparar elemento que aparece em 3 materiais.
- **Frequência dos elementos:** objetivo é mostrar a **representatividade** — quais elementos dominam a base filtrada (e o viés de pesquisa).

**Aba Dados:** tabela filtrada e download.

**Imparcialidade:** nenhum texto no dashboard diz o que concluir; só títulos descritivos e números.

---

## 6. "O código do Pandas é o mesmo do dashboard?"

Sim. O Streamlit é Python, então ele importa o Pandas normalmente. O `preparacao.py` tem as funções de carregar e tratar. O notebook usa essas funções pra fazer a análise; o `app.py` usa as mesmas funções pra montar a base que o dashboard filtra. Os filtros do dashboard são só filtros booleanos do Pandas (`dados[filtro]`) e cada gráfico é refeito com o DataFrame filtrado.

O `@st.cache_data` faz o tratamento rodar uma vez só (leva ~4 s), não a cada clique.

---

## 7. Perguntas prováveis

- **Por que não removeram outliers?** Porque no Tc não sobrou nenhum após o agrupamento, e nos atributos eles são valores físicos reais; o IQR marca demais em distribuições assimétricas.
- **Por que mediana no agrupamento?** Robustez a medições extremas (H₂S, YBCO).
- **Qual a diferença entre Pearson e Spearman e quando usar cada?** Linear vs monotônica; Spearman quando a relação não é linear ou há valores extremos.
- **A correlação de 0,72 significa que a condutividade térmica causa Tc alto?** Não. Dentro de cada família a correlação cai muito; a família está por trás das duas coisas.
- **O que significa curtose negativa aqui?** Distribuição achatada, por causa dos dois picos (bimodal).
- **Por que 77 K?** Ponto de ebulição do nitrogênio líquido; acima disso o resfriamento é barato.
- **Qual a principal limitação?** Só composição química; sem estrutura, pressão e síntese, então materiais com mesma fórmula podem ter Tc bem diferentes.
- **Por que essa regra de família?** Cupratos são definidos por planos de Cu-O; os à base de ferro por Fe com pnictogênios/calcogênios. É aproximação, e o "Outros" é heterogêneo.
