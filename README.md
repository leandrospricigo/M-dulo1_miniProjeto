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

Uma Inteligência Artificial só consegue aprender de verdade se as informações que damos a ela forem limpas e organizadas. Se ensinarmos o sistema usando dados cheios de erros — como informações faltando, datas erradas ou categorias bagunçadas —, ele vai começar a "decorar" esses erros em vez de entender como o negócio funciona na vida real. É o famoso **overfitting**:: o sistema parece perfeito nos testes, mas falha feio quando vai para a prática. Corrigir esses problemas antes, como preencher as informações que faltam sobre o tamanho ou peso de um produto, impede que o sistema tire conclusões totalmente erradas sobre entregas ou recomendações.

Além disso, dados mal cuidados criam visões distorcidas. Por exemplo, se o sistema ignorasse a enorme quantidade de pedidos que estão sem data de entrega simplesmente porque ainda estão a caminho (e não porque foram cancelados), ele nunca aprenderia a calcular prazos de verdade. Organizar essas informações com antecedência dá ao especialista a chance de decidir o que fazer com os dados incompletos. No fim das contas, organizar e limpar os dados não é só um trabalho de faxina: é a base que garante que a Inteligência Artificial seja segura e confiável para tomar decisões sozinha.
