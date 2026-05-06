import pandas as pd
import json
import logging

df_transactions = None

logger = logging.getLogger("services")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("logs/services.log", "w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def load_transactions(filepath: str = "C:/Users/User/PycharmProjects/KR_1/data/operations.xlsx") -> None:
    """Загружает транзакции из Excel. Вызывается один раз при старте."""
    global df_transactions
    try:
        df = pd.read_excel(filepath, sheet_name=0)
        for col in ["Категория", "Описание", "Номер карты"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        df_transactions = df
        logger.info("Транзакции загружены: %d записей", len(df))
    except Exception as e:
        logger.error("Ошибка загрузки транзакций: %s", str(e))
        df_transactions = pd.DataFrame()


def search_transactions(query: str) -> str:
    """
    Ищет транзакции, где запрос встречается в 'Описание' или 'Категория'.
    Возвращает JSON с найденными транзакциями.

    :param query: Строка поиска (регистронезависимо)
    :return: JSON-строка: {"transactions": [...]}
    """
    if not query or not query.strip():
        logger.warning("Пустой запрос в search_transactions")
        return json.dumps({"transactions": []}, ensure_ascii=False, indent=4)

    query = query.strip().lower()
    logger.info("Поиск транзакций по запросу: '%s'", query)

    if df_transactions is None or df_transactions.empty:
        logger.error("Данные по транзакциям не загружены")
        return json.dumps({"error": "Данные не загружены"}, ensure_ascii=False, indent=4)

    mask = df_transactions["Категория"].str.lower().str.contains(query, na=False) | df_transactions[
        "Описание"
    ].str.lower().str.contains(query, na=False)
    found = df_transactions[mask].copy()

    logger.info("Найдено %d транзакций по запросу '%s'", len(found), query)

    result = []
    for _, row in found.iterrows():
        date_str = row["Дата операции"]
        if pd.notna(date_str) and isinstance(date_str, pd.Timestamp):
            date_str = date_str.strftime("%d.%m.%Y")
        else:
            date_str = ""

        amount = row["Сумма операции"]
        amount = float(amount) if pd.notna(amount) else 0.0

        transaction = {
            "date": date_str,
            "amount": round(float(amount), 2),
            "category": str(row["Категория"]) if pd.notna(row["Категория"]) else "",
            "description": str(row["Описание"]) if pd.notna(row["Описание"]) else "",
            "card": str(row["Номер карты"]).strip() if pd.notna(row["Номер карты"]) else None,
        }
        result.append(transaction)

    return json.dumps({"transactions": result}, ensure_ascii=False, indent=4)


load_transactions()

# Ищем
result = search_transactions("Фастфуд")
print(result)
