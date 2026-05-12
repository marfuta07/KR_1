import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

# Настройка логирования
logger = logging.getLogger("services")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("logs/reports.log", "w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def load_operations_data(file_path: str, file_format: str = "excel") -> pd.DataFrame:
    """Загружает данные из файла операций."""
    try:
        if file_format == "csv":
            df = pd.read_csv(file_path, encoding="utf-8")
        elif file_format == "excel":
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Формат файла должен быть 'csv' или 'excel'")
        logger.info(f"Данные загружены из {file_path}")
        return df
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        raise


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Преобразует даты и очищает данные."""
    # Преобразование колонок с датами с указанием формата
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], format="%d.%m.%Y", errors="coerce")

    # Очищаем данные: удаляем строки с пустыми суммами операций
    df.dropna(subset=["Сумма операции"], inplace=True)
    # Приводим сумму к числовому формату
    df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors="coerce")

    logger.info("Данные обработаны: даты преобразованы, пропуски удалены")
    return df


def spending_by_category(
    transactions: pd.DataFrame, category: str, reference_date: Optional[datetime] = None
) -> pd.DataFrame:
    if reference_date is None:
        reference_date = datetime.now()
    start_date = reference_date - timedelta(days=90)
    end_date = reference_date
    category_mask = transactions["Категория"].str.contains(category, case=False, na=False)
    mask = (
        ~transactions[["Дата операции", "Категория", "Сумма операции"]].isna().any(axis=1)
        & category_mask
        & (transactions["Дата операции"] >= start_date)
        & (transactions["Дата операции"] <= end_date)
        & (transactions["Сумма операции"] < 0)
    )
    filtered_transactions = transactions[mask]
    logger.info(
        f"Найдено {len(filtered_transactions)} транзакций "
        f"по категории '{category}' за последние 3 месяца "
        f"(до {reference_date.strftime('%d.%m.%Y')}"
    )
    return filtered_transactions


def main():
    # Путь к файлу
    file_path = r"C:/Users/User/PycharmProjects/KR_1/data/operations.xlsx"
    file_format = "excel"
    # 1. Загрузка данных
    df = load_operations_data(file_path, file_format)

    # 2. Предварительная обработка
    df = preprocess_data(df)

    # 3. Анализ трат по категории
    category = "Супермаркеты"

    # Вариант 1: с конкретной датой
    specific_date = datetime(2020, 10, 24)
    result = spending_by_category(df, category, specific_date)

    # Вариант 2: с текущей датой (раскомментировать, если нужно)
    # result = spending_by_category(df, category)

    if result.empty:
        print(f"\nВНИМАНИЕ: По категории '{category}' данных не найдено за последние 3 месяца!")
        print("Проверьте написание категории и наличие транзакций в указанный период.")
    else:
        print(f"\nТраты по категории: {category} (за последние 3 месяца до {specific_date.strftime('%d.%m.%Y')}):")
        print(result)
        total_spending = result["Сумма операции"].sum()
        print(f"\nОбщая сумма трат за последние 3 месяца: {total_spending:.2f} RUB")
        result.to_csv("spending_last_3_months.csv", index=False)
        logger.info("Результаты сохранены в 'spending_last_3_months.csv'")


if __name__ == "__main__":
    main()
