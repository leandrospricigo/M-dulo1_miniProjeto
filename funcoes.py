# =============================================================================
# funcoes.py — Módulo de funções auxiliares para o pipeline ETL da Olist
# =============================================================================
# Bibliotecas permitidas: csv, re, datetime (todas nativas do Python)
# Nenhuma dependência externa (sem pandas, numpy, etc.)
# =============================================================================

import csv
import re
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. LEITURA DE ARQUIVO CSV
# -----------------------------------------------------------------------------

def read_csv(filepath: str) -> tuple[list[str], list[dict]]:
    
    headers = []
    rows = []

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for row in reader:
            rows.append(dict(row))

    return list(headers), rows


# -----------------------------------------------------------------------------
# 2. TRATAMENTO DE DADOS AUSENTES — PRODUTOS
# -----------------------------------------------------------------------------

def calculate_column_average(rows: list[dict], column: str) -> float:
    values = []
    for row in rows:
        val = row.get(column, "").strip()
        if val:
            try:
                values.append(float(val))
            except ValueError:
                pass  

    return round(sum(values) / len(values), 2) if values else 0.0


def fill_missing_category(value: str) -> str:
    """
    Preenche o nome de categoria vazio/nulo com a string padrão "Sem Categoria".
    
    """
    if not value or not value.strip():
        return "Sem Categoria"
    return value


def handle_physical_dimensions(row: dict, averages: dict) -> tuple[dict, bool]:
    """
    Trata valores nulos nas colunas de dimensões físicas do produto.

    Estratégia escolhida — IMPUTAÇÃO PELA MÉDIA:
        Substituir nulos pela média da coluna, calculada previamente sobre
        todos os registros válidos. Essa abordagem é preferível ao descarte
        porque: (1) preserva o volume total de dados para treinamento de modelos;
        (2) a média é uma estimativa central razoável para dimensões de produtos
        que tendem a ter distribuição unimodal (a maioria dos produtos é "normal");
        (3) descartar linhas com nulos em múltiplas colunas de dimensão poderia
        eliminar uma fração significativa do dataset, introduzindo viés de seleção.
    
    """
    dimension_cols = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    corrected = False
    for col in dimension_cols:
        val = row.get(col, "").strip()
        if not val:
            row[col] = str(averages.get(col, 0.0))
            corrected = True

    return row, corrected


# -----------------------------------------------------------------------------
# 3. PADRONIZAÇÃO DE STRINGS E REGEX
# -----------------------------------------------------------------------------

# Padrão compilado para remover caracteres que não sejam letras (a-z, acentuadas),
# dígitos, espaços simples ou underscores — adequado para nomes de categorias.
_CATEGORY_CLEANUP_PATTERN = re.compile(r"[^a-záéíóúàâêôãõüç\d _]", re.IGNORECASE)
_MULTIPLE_SPACES_PATTERN = re.compile(r"\s{2,}")


def clean_category_name(name: str) -> str:
    """
    Normaliza o nome de uma categoria:
      1. Remove espaços no início/fim (.strip()).
      2. Converte para minúsculas (.lower()).
      3. Remove caracteres especiais e pontuação indevida via regex.
      4. Colapsa múltiplos espaços internos em um único espaço.   
    """
    name = name.strip()
    name = name.lower()
    name = _CATEGORY_CLEANUP_PATTERN.sub("", name)
    name = _MULTIPLE_SPACES_PATTERN.sub(" ", name)
    return name.strip()


# -----------------------------------------------------------------------------
# 4. PROCESSAMENTO COMPLETO DO DATASET DE PRODUTOS
# -----------------------------------------------------------------------------

def process_products(rows: list[dict]) -> tuple[list[dict], dict]:
    """
    Executa o pipeline de sanitização nos registros de produtos:
      - Preenche categorias vazias.
      - Normaliza nomes de categorias (lower, strip, regex).
      - Imputa dimensões físicas nulas pela média.

    Args:
        rows: Lista de dicionários brutos lidos do CSV de produtos.

    Returns:
        Tupla (rows_processadas, stats) onde stats contém contadores do relatório.
    """
    stats = {
        "total_linhas": len(rows),
        "categorias_corrigidas": 0,
        "dimensoes_corrigidas": 0,
    }

    # Calcula médias das dimensões antes de qualquer imputação
    dimension_cols = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    averages = {col: calculate_column_average(rows, col) for col in dimension_cols}

    processed = []
    for row in rows:
        # --- Categoria ---
        original_category = row.get("product_category_name", "")
        filled_category = fill_missing_category(original_category)
        if filled_category != original_category:
            stats["categorias_corrigidas"] += 1

        row["product_category_name"] = clean_category_name(filled_category)

        # --- Dimensões físicas ---
        row, dim_corrected = handle_physical_dimensions(row, averages)
        if dim_corrected:
            stats["dimensoes_corrigidas"] += 1

        processed.append(row)

    return processed, stats


# -----------------------------------------------------------------------------
# 5. LÓGICA DE REGRA DE NEGÓCIO — PEDIDOS
# -----------------------------------------------------------------------------

def check_delivery_hypothesis(rows: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """
    Separa os pedidos com data de entrega ausente e verifica a hipótese da Olist:
    "As datas de entrega nulas ocorrem OBRIGATORIAMENTE porque o status é 'canceled'?"

    Estruturas condicionais (if/elif/else) são usadas para classificar cada registro
    em três grupos:
      A) Entrega preenchida → registro normal.
      B) Entrega nula E status "canceled" → confirma a hipótese.
      C) Entrega nula E status DIFERENTE de "canceled" → REFUTA a hipótese
         (ex.: pedidos em trânsito, aprovados, etc. que ainda não foram entregues).

    Args:
        rows: Lista de dicionários brutos lidos do CSV de pedidos.

    Returns:
        Tupla (registros_normais, registros_sem_entrega, stats_hipotese).
    """
    normal = []
    sem_entrega = []

    stats = {
        "total_linhas": len(rows),
        "sem_entrega_total": 0,
        "cancelados_sem_entrega": 0,    # Confirma hipótese
        "nao_cancelados_sem_entrega": 0,  # Refuta hipótese
        "pedidos_cancelados_total": 0,
    }

    for row in rows:
        delivery = row.get("order_delivered_customer_date", "").strip()
        status = row.get("order_status", "").strip().lower()

        if status == "canceled":
            stats["pedidos_cancelados_total"] += 1

        if delivery:
            # Caso A: entrega presente — fluxo normal
            normal.append(row)
        else:
            # Caso B ou C: entrega ausente
            stats["sem_entrega_total"] += 1

            if status == "canceled":
                # Caso B: hipótese CONFIRMADA para este registro
                stats["cancelados_sem_entrega"] += 1
            else:
                # Caso C: hipótese REFUTADA — status diferente de "canceled"
                stats["nao_cancelados_sem_entrega"] += 1

            sem_entrega.append(row)

    return normal, sem_entrega, stats


# -----------------------------------------------------------------------------
# 6. FORMATAÇÃO TEMPORAL
# -----------------------------------------------------------------------------

def format_date_to_br(date_str: str) -> str:
    """
    Converte uma data/hora no formato ISO "AAAA-MM-DD HH:MM:SS" para o formato
    brasileiro simplificado "DD/MM/AAAA", utilizando o módulo nativo datetime.

    Se a string estiver vazia ou em formato inválido, retorna "Data inválida"
    para não interromper o pipeline.

    Args:
        date_str: String de data bruta, ex.: "2017-05-16 15:05:35".

    Returns:
        String formatada, ex.: "16/05/2017", ou "Data inválida".
    """
    if not date_str or not date_str.strip():
        return "Data inválida"

    # Tenta o formato completo com hora; se falhar, tenta só a data
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue

    return "Data inválida"


def format_approval_dates(rows: list[dict]) -> list[dict]:
    """
    Aplica format_date_to_br em cada registro de pedido, convertendo a coluna
    order_approved_at do formato ISO para o formato brasileiro DD/MM/AAAA.

    Args:
        rows: Lista de dicionários de pedidos.

    Returns:
        Lista de dicionários com a coluna order_approved_at reformatada.
    """
    for row in rows:
        raw_date = row.get("order_approved_at", "")
        row["order_approved_at"] = format_date_to_br(raw_date)
    return rows


# -----------------------------------------------------------------------------
# 7. RELATÓRIO DE STATUS MANUAL
# -----------------------------------------------------------------------------

def print_report(products_stats: dict, orders_stats: dict) -> None:
    """
    Exibe na tela um sumário estatístico do pipeline de sanitização,
    construído manualmente via contadores acumulados durante o processamento.

    Inclui também a análise da hipótese de negócio sobre datas de entrega nulas.

    Args:
        products_stats: Estatísticas retornadas por process_products().
        orders_stats:   Estatísticas retornadas por check_delivery_hypothesis().
    """
    separator = "=" * 60

    print(f"\n{separator}")
    print("  RELATÓRIO DE SANITIZAÇÃO — PIPELINE ETL OLIST")
    print(separator)

    # --- Produtos ---
    print("\n📦 DATASET DE PRODUTOS")
    print(f"  Total de linhas processadas : {products_stats['total_linhas']}")
    print(f"  Categorias nulas corrigidas : {products_stats['categorias_corrigidas']}")
    print(f"  Dimensões físicas imputadas : {products_stats['dimensoes_corrigidas']}")

    # --- Pedidos ---
    print("\n🛒 DATASET DE PEDIDOS")
    print(f"  Total de linhas processadas : {orders_stats['total_linhas']}")
    print(f"  Pedidos sem data de entrega : {orders_stats['sem_entrega_total']}")
    print(f"  Cancelados sem entrega      : {orders_stats['cancelados_sem_entrega']}")
    print(f"  Não cancelados sem entrega  : {orders_stats['nao_cancelados_sem_entrega']}")
    print(f"  Total de cancelados         : {orders_stats['pedidos_cancelados_total']}")

    # --- Análise da hipótese ---
    print("\n🔍 HIPÓTESE DE NEGÓCIO")
    total_sem = orders_stats["sem_entrega_total"]
    cancelados_sem = orders_stats["cancelados_sem_entrega"]
    nao_cancelados_sem = orders_stats["nao_cancelados_sem_entrega"]

    if total_sem == 0:
        print("  Nenhum registro sem data de entrega encontrado.")
    else:
        pct_confirma = round((cancelados_sem / total_sem) * 100, 2)
        pct_refuta = round((nao_cancelados_sem / total_sem) * 100, 2)

        print(
            f"  {pct_confirma}% dos registros sem entrega são cancelados "
            f"({cancelados_sem}/{total_sem})."
        )
        print(
            f"  {pct_refuta}% sem entrega possuem outro status "
            f"({nao_cancelados_sem}/{total_sem})."
        )

        if nao_cancelados_sem == 0:
            print(
                "\n  ✅ HIPÓTESE CONFIRMADA: todas as datas de entrega nulas\n"
                "     correspondem a pedidos com status 'canceled'."
            )
        else:
            print(
                "\n  ❌ HIPÓTESE REFUTADA: existem pedidos sem data de entrega\n"
                "     cujo status NÃO é 'canceled'. Investigação necessária."
            )

    print(f"\n{separator}")
    print("  Base sanitizada. Pipeline concluído com sucesso.")
    print(f"{separator}\n")
