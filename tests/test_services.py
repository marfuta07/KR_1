import pytest
import pandas as pd
import json
#import logging
import src.services as services

#logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
def setup_transactions():
    """Заменяет глобальную переменную df_transactions в модуле services"""
    df = pd.DataFrame({
        "Дата операции": ["01.01.2025 10:00:00", "02.01.2025 12:00:00", "03.01.2025 14:00:00"],
        "Сумма операции": [-200.0, -450.0, -150.0],
        "Категория": ["Еда", "Транспорт", "Еда"],
        "Описание": ["Оплата в кофейне", "Проездной", "Кофе с собой"],
        "Номер карты": ["*1234", None, "*5678"]
    })
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

    services.df_transactions = df
    #logger.info("Тестовые данные загружены в src.services.df_transactions")

def test_search_by_description():
    result = services.search_transactions("кофе")
    assert "кофе" in result.lower()
    data = json.loads(result)
    assert len(data["transactions"]) == 2

    descriptions = [t["description"] for t in data["transactions"]]
    assert any("кофейне" in d.lower() for d in descriptions)
    assert any("кофе с собой" in d.lower() for d in descriptions)

def test_search_by_category():
    result = services.search_transactions("еда")
    data = json.loads(result)
    assert len(data["transactions"]) == 2
    categories = [t["category"] for t in data["transactions"]]
    assert all(cat == "Еда" for cat in categories)

def test_search_case_insensitive():
    result = services.search_transactions("КОФЕ")
    data = json.loads(result)
    assert len(data["transactions"]) == 2

def test_empty_query():
    result = services.search_transactions("   ")
    data = json.loads(result)
    assert data["transactions"] == []

def test_no_matches():
    result = services.search_transactions("путешествие")
    data = json.loads(result)
    assert len(data["transactions"]) == 0

def test_partial_match():
    result = services.search_transactions("коф")
    data = json.loads(result)
    assert len(data["transactions"]) == 2
    descriptions = [t["description"] for t in data["transactions"]]
    assert any("кофейне" in d.lower() for d in descriptions)
    assert any("кофе с собой" in d.lower() for d in descriptions)
