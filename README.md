# Dashboard — Temperatura crítica de supercondutores

## Estrutura

    projeto/
    ├── dados/
    │   ├── train.csv
    │   └── unique_m.csv
    ├── preparacao.py
    ├── analise_exploratoria.ipynb
    ├── app.py
    └── requirements.txt

`preparacao.py` contém todo o carregamento e tratamento em Pandas. O notebook e o dashboard importam as mesmas funções, então a base que aparece no dashboard é exatamente a base analisada no notebook.

## Como rodar (Windows)

    cd caminho\para\projeto
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    streamlit run app.py

O navegador abre em http://localhost:8501.

Para a análise exploratória:

    jupyter notebook analise_exploratoria.ipynb

## Fonte dos dados

Hamidieh, K. (2018). A data-driven statistical model for predicting the critical temperature of a superconductor. Computational Materials Science, 154, 346–354. Dados originais do banco SuperCon (NIMS, Japão), disponibilizados no UCI Machine Learning Repository e no Kaggle.
