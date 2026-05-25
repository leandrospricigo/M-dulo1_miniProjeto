# Pipeline ETL de Sanitização de Dados — Olist
A Olist, uma das maiores plataformas de e-commerce do Brasil, gera diariamente milhões de registros de pedidos e produtos. Porém, dados extraídos de sistemas reais chegam frequentemente com inconsistências: categorias em branco, dimensões físicas ausentes, datas em formatos incorretos e pedidos com status contraditórios.
Este projeto implementa um pipeline de ETL (Extract, Transform, Load) em Python puro — sem uso de bibliotecas externas como pandas — para sanitizar dois datasets reais da Olist:
## Descrição do Projeto

| Arquivo                        | Conteúdo                                 |
|-------------------------------|------------------------------------------|
| `olist_products_dataset.csv`  | Catálogo de produtos (categoria, dimensões, fotos) |
| `olist_orders_dataset.csv`    | Registro de pedidos (status, datas, aprovação)     |

O script realiza cinco operações técnicas:

1. **Preenchimento de nulos** em `product_category_name` com `"Sem Categoria"` e **imputação pela média** nas dimensões físicas.
2. **Normalização de strings** via `.lower()`, `.strip()` e expressões regulares (módulo `re`).
3. **Validação de hipótese de negócio**: pedidos sem data de entrega são *necessariamente* cancelados?
4. **Conversão de datas** do formato ISO (`AAAA-MM-DD HH:MM:SS`) para o padrão brasileiro (`DD/MM/AAAA`) com o módulo `datetime`.
5. **Relatório estatístico manual** com totais de registros processados, nulos corrigidos e cancelamentos identificados.

---

## Estrutura do Projeto

```
mini_projeto1/
├── main.py                          # Orquestrador do pipeline
├── funcoes.py                       # Módulo com todas as funções auxiliares
├── olist_products_dataset.csv       # Dataset de entrada (baixar — ver abaixo)
├── olist_orders_dataset.csv         # Dataset de entrada (baixar — ver abaixo)
├── olist_products_sanitized.csv     # Saída gerada pelo pipeline
├── olist_orders_sanitized.csv       # Saída gerada pelo pipeline
└── README.md                        # Esta documentação
```

---

## Guia de Execução

### Pré-requisitos

- Python 3.10 ou superior.
- olist_orders_dataset = 'https://raw.githubusercontent.com/fiesc-junior-prado/mine_projeto_bloco_1/refs/heads/main/olist_orders_dataset.csv'.
- olist_products_dataset = 'https://raw.githubusercontent.com/fiesc-junior-prado/mine_projeto_bloco_1/refs/heads/main/olist_products_dataset.csv'.

### Passo a passo

```bash
# 1. Clone ou baixe os arquivos do projeto
#    (ou copie main.py, funcoes.py para uma pasta de sua escolha)

# 2. Coloque os CSVs da Olist na mesma pasta:
#    olist_products_dataset.csv
#    olist_orders_dataset.csv

# 3. Execute o pipeline
python main.py
```

### Saída esperada no terminal

```
============================================================
  INICIANDO PIPELINE ETL — OLIST DATA SANITIZATION
============================================================

[1/4] Lendo e sanitizando produtos...
  32951 registros lidos de 'olist_products_dataset.csv'.

[2/4] Lendo e sanitizando pedidos...
  99441 registros lidos de 'olist_orders_dataset.csv'.

[3/4] Gerando relatório de sanitização...

============================================================
  RELATÓRIO DE SANITIZAÇÃO — PIPELINE ETL OLIST
============================================================

📦 DATASET DE PRODUTOS
  Total de linhas processadas : 32951
  Categorias nulas corrigidas : 610
  Dimensões físicas imputadas : 2

🛒 DATASET DE PEDIDOS
  Total de linhas processadas : 99441
  Pedidos sem data de entrega : 2965
  Cancelados sem entrega      : 625
  Não cancelados sem entrega  : 2340
  Total de cancelados         : 625

🔍 HIPÓTESE DE NEGÓCIO
  21.08% dos registros sem entrega são cancelados (625/2965).
  78.92% sem entrega possuem outro status (2340/2965).

  ❌ HIPÓTESE NEGADA: existem pedidos sem data de entrega
     cujo status NÃO é 'canceled'. Investigação necessária.

[4/4] Salvando arquivos sanitizados...
  → Arquivo salvo: olist_products_sanitized.csv
  → Arquivo salvo: olist_orders_sanitized.csv

  Pipeline concluído com sucesso! ✔
```

---

## Reflexão Teórica: Qualidade de Dados e Machine Learning

A qualidade dos dados de entrada é o fator mais determinante na capacidade de generalização de um modelo de Machine Learning. Quando alimentamos um algoritmo com registros que contêm valores nulos não tratados, categorias inconsistentes ou datas malformadas, o modelo aprende padrões que existem apenas como artefatos da sujeira nos dados — não como regras reais do negócio. Esse fenômeno é uma das causas mais comuns de **overfitting**: o modelo "decora" ruído em vez de aprender a estrutura subjacente dos dados, apresentando alta acurácia no conjunto de treino e desempenho fraco em produção. A imputação de nulos pela média (adotada neste pipeline para as dimensões físicas) e o preenchimento explícito de categorias ausentes impedem que o algoritmo crie um "cluster oculto" de produtos sem dimensão, que distorceria qualquer modelo de recomendação ou estimativa de frete.

Além do overfitting, dados brutos carregam **viés de representação**. Se ignorarmos os 79,12% de pedidos sem data de entrega que *não* são cancelados — fato comprovado pelo pipeline ao refutar a hipótese de negócio —, um modelo de previsão de prazo nunca aprenderia a lidar com pedidos legítimos em trânsito, faturados ou em processamento, introduzindo um viés sistemático nas suas estimativas. A separação explícita e a contagem desses registros permitem que o Cientista de Dados tome uma decisão informada: imputar, descartar ou criar uma feature auxiliar antes de injetar os dados no modelo. Em resumo, um ETL bem construído não é apenas higiene de dados — é a fundação que determina se um modelo de IA será confiável o suficiente para apoiar decisões automatizadas em produção.
