import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
import yfinance as yf
from src.views import get_greeting,process_cards,get_top_transactions,get_currency_rates,get_stock_prices

# === 🟩 Главная функция ===
def main(date_input: str) -> str:
    try:
        # Парсим входную дату
        input_dt = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
        hour = input_dt.hour

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
        user_settings_str = '''{
          "user_currencies": ["USD", "EUR"],
          "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        }'''
        import ast
        settings = ast.literal_eval(user_settings_str)
        user_stocks = settings["user_stocks"]

        # Формируем ответ
        result = {
            "greeting": get_greeting(hour),
            "cards": process_cards(df),
            "top_transactions": get_top_transactions(df),
            "currency_rates": get_currency_rates(),
            "stock_prices": get_stock_prices(user_stocks)
        }

        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        error = {"error": f"Ошибка обработки: {str(e)}"}
        return json.dumps(error, ensure_ascii=False, indent=4)

# === Пример вызова ===
if __name__ == "__main__":
    input_time = "2026-04-29 01:43:00"
    print(main(input_time))