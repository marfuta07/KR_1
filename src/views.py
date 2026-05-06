import pandas as pd
from typing import List, Dict,Any
import yfinance as yf
import logging
import json
import requests
from datetime import datetime


logger = logging.getLogger("views")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("logs/views.log", "w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


# === 1. Функция: Приветствие по времени ===
def get_greeting(hour: int) -> str:
    """Возвращает приветствие в зависимости от времени суток."""
    if not 0 <= hour <= 23:
        logger.error("Некорректный час: %s", hour)
        raise ValueError("Час должен быть в диапазоне от 0 до 23")

    if 6 <= hour < 12:
        greeting = "Доброе утро"
    elif 12 <= hour < 18:
        greeting = "Добрый день"
    elif 18 <= hour < 24:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"

    logger.info("Приветствие по часу %d: '%s'", hour, greeting)
    return greeting


# == = 2.Функция: Обработка карт  и кешбэка == =
def process_cards(df: pd.DataFrame) -> List[Dict]:
    """Обрабатывает данные по картам: расходы и кешбэк."""
    logger.info("Начало обработки данных по картам. Всего строк: %d", len(df))
    cards:List[Dict[str, Any]] =[]
    # Фильтруем только расходы (отрицательные суммы)
    spending = df[df["Сумма операции"] < 0].copy()
    logger.debug("Количество расходов (отрицательных сумм): %d", len(spending))
    # Обработка номера карты: замена NaN, удаление * и извлечение последних 4 цифр
    spending["card_last_digits"] = spending["Номер карты"].fillna("").str.replace("*", "").str[-4:]
    # Убираем строки, где номер карты пустой
    spending = spending[spending["card_last_digits"] != ""]
    # Группируем по последним цифрам карты
    grouped = spending.groupby("card_last_digits")["Сумма операции"].sum()
    logger.debug("Обнаружено карт: %d", len(grouped))
    cards = []

    for last_digits, total in grouped.items():
        total_spent = abs(total)  # Сумма расходов
        cashback = round(total_spent * 0.01, 2)  # 1 рубль на 100 рублей
        cards.append({"last_digits": last_digits, "total_spent": round(total_spent, 2), "cashback": cashback})
        logger.debug("Карта %s: потрачено %.2f, кешбэк %.2f", last_digits, total_spent, cashback)

    logger.info("Обработка карт завершена. Найдено карт: %d", len(cards))
    return cards


# === 3. Функция: Топ-5 транзакций по модулю суммы ===
def get_top_transactions(df: pd.DataFrame) -> List[Dict]:
    """Формирует топ-5 транзакций по модулю суммы."""
    # Исключаем категории "Бонусы" и "Переводы"
    filtered = df[~df["Категория"].str.strip().str.lower().isin(["бонусы", "переводы"])].copy()
    # Убираем строки с NaN в "Категория", если такие есть
    filtered = filtered.dropna(subset=["Категория"])
    # Добавляем столбец с модулем суммы
    filtered["abs_amount"] = filtered["Сумма операции"].abs()
    # Берём топ-5 по модулю суммы
    top_5 = filtered.nlargest(5, "abs_amount")

    transactions = []
    for _, row in top_5.iterrows():
        transactions.append(
            {
                "date": row["Дата операции"].strftime("%d.%m.%Y"),
                "amount": round(row["Сумма операции"], 2),
                "category": row["Категория"].strip(),
                "description": row["Описание"] if pd.notna(row["Описание"]) else "",
            }
        )
    return transactions


# === 4. Функция: Курсы валют ===
def get_currency_rates() -> List[Dict[str, Any]]:
    """
    Получает актуальные курсы валют к рублю от ЦБ РФ.
    Источник: https://www.cbr.ru/scripts/XML_daily.asp
    """
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    try:
        params = {"date_req": datetime.now().strftime("%d/%m/%Y")}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)

        rates = []
        for valute in root.findall("Valute"):
            charcode_elem = valute.find("CharCode")
            if charcode_elem is not None and charcode_elem.text in ["USD", "EUR"]:
                value_elem = valute.find("Value")
                if value_elem is not None and value_elem.text is not None:
                    value_str = value_elem.text.replace(",", ".")
                    try:
                        rate = round(float(value_str), 2)
                        rates.append({"currency": charcode_elem.text, "rate": rate})
                    except ValueError as e:
                        logger.warning("Некорректный формат курса для %s: %s", charcode_elem.text, e)

        return rates
    except Exception as e:
        logger.error("Ошибка получения курсов валют: %s", e)
        print(f"Ошибка получения курсов валют: {e}")
        return [{"currency": "USD", "rate": 73.21}, {"currency": "EUR", "rate": 87.08}]


# === 5. Функция: Цены акций (заглушка) ===
def get_stock_prices(stock_list: List[str]) -> List[Dict]:
    prices = []
    for stock in stock_list:
        try:
            ticker = yf.Ticker(stock)
            price = ticker.history(period="1d")["Close"].iloc[-1]
            prices.append({"stock": stock, "price": round(price, 2)})
        except Exception as e:
            print(f"Ошибка для {stock}: {e}")
            prices.append({"stock": stock, "price": 0.0})
    return prices


# === Главная функция ===#
#def main(date_input: str = None) -> str:
def main(date_input: str | None = None) -> str:
    try:
        if date_input:
            input_dt = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
        else:
            # Автоматически текущее время
            input_dt = datetime.now()
            print(f"Используется текущее время: {input_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        hour = input_dt.hour
        get_greeting(hour)

        # Читаем данные из operations.xlsx
        try:
            df = pd.read_excel("C:/Users/User/PycharmProjects/KR_1/data/operations.xlsx", sheet_name=0)
        except FileNotFoundError:
            raise FileNotFoundError("Файл operations.xlsx не найден")
        except Exception as e:
            raise Exception(f"Ошибка чтения Excel-файла: {str(e)}")

        # Проверка обязательных столбцов
        required_columns = ["Дата операции", "Номер карты", "Сумма операции", "Категория", "Описание"]
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Отсутствуют обязательные столбцы: {missing}")

        # Преобразуем 'Дата операции' в datetime с учётом времени
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
        # Удаляем строки с некорректной датой
        df = df.dropna(subset=["Дата операции"])

        # Читаем настройки пользователя (заглушка)
        user_settings_str = """{
          "user_currencies": ["USD", "EUR"],
          "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        }"""
        import ast

        settings = ast.literal_eval(user_settings_str)
        user_stocks = settings["user_stocks"]

        # Формируем ответ
        result = {
            "greeting": get_greeting(hour),
            "current_time": input_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "cards": process_cards(df),
            "top_transactions": get_top_transactions(df),
            "currency_rates": get_currency_rates(),
            "stock_prices": get_stock_prices(user_stocks),
        }

        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        error = {"error": f"Ошибка обработки: {str(e)}"}
        return json.dumps(error, ensure_ascii=False, indent=4)


# === Пример вызова ===
if __name__ == "__main__":
    print("=== Текущее время ===")
    print(main())
