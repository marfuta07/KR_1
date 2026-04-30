import pandas as pd
import json
from src.views import (
    get_greeting,
    process_cards,
    get_top_transactions,
    get_currency_rates,
    get_stock_prices,
    main,
)


def test_get_greeting():
    assert get_greeting(7) == "Доброе утро", "Утро не работает"
    assert get_greeting(11) == "Доброе утро", "Утро до 12 не работает"

    assert get_greeting(12) == "Добрый день", "Полдень не работает"
    assert get_greeting(17) == "Добрый день", "День до 18 не работает"

    assert get_greeting(18) == "Добрый вечер", "Вечер не работает"
    assert get_greeting(23) == "Добрый вечер", "Вечер до 24 не работает"

    assert get_greeting(0) == "Доброй ночи", "Полночь не работает"
    assert get_greeting(5) == "Доброй ночи", "Ночь до 6 не работает"

    # Проверка ошибки на некорректный час
    try:
        get_greeting(24)
        assert False, "Ожидалась ошибка при hour=24"
    except ValueError:
        pass  # OK

    try:
        get_greeting(-1)
        assert False, "Ожидалась ошибка при hour=-1"
    except ValueError:
        pass  # OK


def test_process_cards():
    df = pd.DataFrame(
        {
            "Номер карты": ["*1234", "*5678", "*1234", "*5678", None, "*9999"],
            "Сумма операции": [-1000.0, -2000.0, -500.0, -300.0, -400.0, 100.0],
            "Категория": ["Еда", "Транспорт", "Еда", "Онлайн", "Еда", "Бонусы"],
            "Описание": ["Кафе", "Метро", "Ресторан", "Amazon", "Кафе", "Cashback"],
        }
    )

    result = process_cards(df)

    # Проверяем, что карты 1234 и 5678 обработаны
    cards = {item["last_digits"]: item for item in result}
    assert "1234" in cards
    assert "5678" in cards
    assert "9999" not in cards  # потому что доход (положительная сумма)
    assert None not in [item["last_digits"] for item in result]  # пустые номера не попали

    assert cards["1234"]["total_spent"] == 1500.0
    assert cards["1234"]["cashback"] == 15.0

    assert cards["5678"]["total_spent"] == 2300.0
    assert cards["5678"]["cashback"] == 23.0


def test_get_top_transactions():
    df = pd.DataFrame(
        {
            "Дата операции": [
                "01.01.2023 10:00:00",  # ← Самая большая сумма — должна быть первой
                "02.01.2023 11:00:00",
                "03.01.2023 12:00:00",
                "04.01.2023 13:00:00",
                "05.01.2023 14:00:00",
                "06.01.2023 15:00:00",
            ],
            "Сумма операции": [-5000.0, -2000.0, 1000.0, -1500.0, -800.0, -3000.0],
            "Категория": ["Еда", "Еда", "Бонусы", "Транспорт", "Развлечения", "Еда"],  # ← "Переводы" убрано!
            "Описание": ["Ресторан", "Ресторан", "Cashback", "Такси", "Кино", "Доставка"],
        }
    )
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    result = get_top_transactions(df)

    categories = [t["category"] for t in result]
    assert "Бонусы" not in categories, "Категория 'Бонусы' не должна быть в топе"
    assert len(result) == 5, "Должно быть 5 транзакций"

    amounts = [t["amount"] for t in result]
    assert amounts == [-5000.0, -3000.0, -2000.0, -1500.0, -800.0], "Сортировка по сумме неверна"

    assert result[0]["date"] == "01.01.2023", "Формат даты должен быть ДД.ММ.ГГГГ"


# 🔁 Заглушка для get_currency_rates (не тестируем API, но проверим fallback)
def test_get_currency_rates_fallback():
    # Просто проверим, что возвращается список с USD и EUR
    result = get_currency_rates()
    currencies = {item["currency"] for item in result}
    assert "USD" in currencies
    assert "EUR" in currencies
    assert isinstance(result[0]["rate"], (int, float))


# 🔁 Заглушка для get_stock_prices — мок через monkeypatch не делаем, просто проверим структуру
def test_get_stock_prices_structure():
    # Это не полноценный тест, но проверим, что функция возвращает правильную структуру
    result = get_stock_prices(["AAPL", "MSFT"])
    assert len(result) == 2
    assert result[0]["stock"] == "AAPL"
    assert isinstance(result[0]["price"], (int, float))
    assert result[1]["stock"] == "MSFT"
    assert isinstance(result[1]["price"], (int, float))


def test_main_output_structure():
    # Проверим, что main возвращает валидный JSON с нужными полями
    result_str = main("2023-01-01 12:00:00")
    try:
        result = json.loads(result_str)
    except json.JSONDecodeError:
        assert False, "main вернул невалидный JSON"

    expected_keys = ["greeting", "current_time", "cards", "top_transactions", "currency_rates", "stock_prices"]
    for key in expected_keys:
        assert key in result, f"Нет ключа {key} в результате main"

    assert isinstance(result["cards"], list)
    assert isinstance(result["top_transactions"], list)
    assert isinstance(result["currency_rates"], list)
    assert isinstance(result["stock_prices"], list)
