import csv
import os

# Importa todas as funções auxiliares do módulo de suporte
from funcoes import (
    read_csv,
    process_products,
    check_delivery_hypothesis,
    format_approval_dates,
    print_report,
)


# -----------------------------------------------------------------------------
# CONFIGURAÇÃO — caminhos dos arquivos de entrada
# -----------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PRODUCTS_CSV = os.path.join(BASE_DIR, "olist_products_dataset.csv")
ORDERS_CSV   = os.path.join(BASE_DIR, "olist_orders_dataset.csv")

# Arquivos de saída com os dados sanitizados (gerados ao final do pipeline)
PRODUCTS_OUTPUT = os.path.join(BASE_DIR, "olist_products_sanitized.csv")
ORDERS_OUTPUT   = os.path.join(BASE_DIR, "olist_orders_sanitized.csv")


# -----------------------------------------------------------------------------
# FUNÇÕES DE SAÍDA — escrita dos CSVs sanitizados
# -----------------------------------------------------------------------------

def write_csv(filepath: str, headers: list[str], rows: list[dict]) -> None:
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  → Arquivo salvo: {os.path.basename(filepath)}")


# -----------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# -----------------------------------------------------------------------------

def run_pipeline() -> None:
   
    print("\n" + "=" * 60)
    print("  INICIANDO PIPELINE ETL")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # ETAPA 1: PROCESSAMENTO DO DATASET DE PRODUTOS
    # -------------------------------------------------------------------------
    print("\n[1/4] Lendo e sanitizando produtos...")

    if not os.path.exists(PRODUCTS_CSV):
        print(f"  ERRO: arquivo não encontrado → {PRODUCTS_CSV}")
        print("  Certifique-se de que olist_products_dataset.csv está na mesma pasta.")
        return

    product_headers, product_rows = read_csv(PRODUCTS_CSV)
    print(f"  {len(product_rows)} registros lidos de '{os.path.basename(PRODUCTS_CSV)}'.")

    # Aplica todo o pipeline de sanitização de produtos (categorias + dimensões)
    clean_products, products_stats = process_products(product_rows)

    # -------------------------------------------------------------------------
    # ETAPA 2: PROCESSAMENTO DO DATASET DE PEDIDOS
    # -------------------------------------------------------------------------
    print("\n[2/4] Lendo e sanitizando pedidos...")

    if not os.path.exists(ORDERS_CSV):
        print(f"  ERRO: arquivo não encontrado → {ORDERS_CSV}")
        print("  Certifique-se de que olist_orders_dataset.csv está na mesma pasta.")
        return

    order_headers, order_rows = read_csv(ORDERS_CSV)
    print(f"  {len(order_rows)} registros lidos de '{os.path.basename(ORDERS_CSV)}'.")

    # 2a. Formatação de datas de aprovação (ISO → DD/MM/AAAA)
    order_rows = format_approval_dates(order_rows)

    # 2b. Verificação da hipótese de negócio sobre datas de entrega nulas
    normal_orders, missing_delivery_orders, orders_stats = check_delivery_hypothesis(order_rows)

    # -------------------------------------------------------------------------
    # ETAPA 3: RELATÓRIO DE STATUS
    # -------------------------------------------------------------------------
    print("\n[3/4] Gerando relatório de sanitização...")
    print_report(products_stats, orders_stats)

    # -------------------------------------------------------------------------
    # ETAPA 4: PERSISTÊNCIA DOS DADOS SANITIZADOS
    # -------------------------------------------------------------------------
    print("[4/4] Salvando arquivos sanitizados...")

    write_csv(PRODUCTS_OUTPUT, product_headers, clean_products)

    # Para pedidos: salva todos os registros (normais + sem entrega) já com as
    # datas formatadas. O analista pode usar os contadores do relatório para
    # filtrar manualmente se necessário.
    all_clean_orders = normal_orders + missing_delivery_orders
    write_csv(ORDERS_OUTPUT, order_headers, all_clean_orders)

    print("\n  Pipeline concluído com sucesso! ✔")


# -----------------------------------------------------------------------------
# PONTO DE ENTRADA
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    run_pipeline()
