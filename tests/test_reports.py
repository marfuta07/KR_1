from io import StringIO
import sys
import os
import pytest
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.reports import load_operations_data, preprocess_data, spending_by_category


def test_load_csv_success():
    """Тест успешной загрузки CSV‑файла."""
    csv_data = """Дата операции,Дата платежа,Сумма операции,Категория
01.01.2020 12:00:00,01.01.2020,1000.00,Супермаркеты
02.01.2020 13:00:00,02.01.2020,-500.00,Кафе"""
    csv_file = StringIO(csv_data)

    df = load_operations_data(csv_file, 'csv')
    assert len(df) == 2
    assert 'Дата операции' in df.columns
    assert 'Сумма операции' in df.columns


def test_load_excel_success(tmp_path):
    """Тест успешной загрузки Excel‑файла."""
    df_test = pd.DataFrame({
        'Дата операции': ['01.01.2020 12:00:00', '02.01.2020 13:00:00'],
        'Дата платежа': ['01.01.2020', '02.01.2020'],
        'Сумма операции': [1000.00, -500.00],
        'Категория': ['Супермаркеты', 'Кафе']
    })
    excel_path = tmp_path / "test_operations.xlsx"
    df_test.to_excel(excel_path, index=False)

    df = load_operations_data(excel_path, 'excel')
    assert len(df) == 2
    assert df['Сумма операции'].iloc[0] == 1000.00


def test_invalid_format_raises_value_error():
    """Тест на ошибку при неверном формате файла."""
    with pytest.raises(ValueError, match="Формат файла должен быть 'csv' или 'excel'"):
        load_operations_data('file.txt', 'txt')

def test_file_not_found_raises_exception():
    """Тест на ошибку при отсутствии файла."""
    with pytest.raises(Exception):
        load_operations_data('nonexistent_file.xlsx', 'excel')


def test_nan_values_handled_correctly():
    """Тест обработки NaN значений."""
    df = pd.DataFrame({
        'Дата операции': [None, '01.01.2020 12:00:00'],
        'Дата платежа': [None, '01.01.2020'],
        'Сумма операции': [None, '500.00'],
        'Категория': [None, 'Супермаркеты']
    })

    processed_df = preprocess_data(df)
    assert len(processed_df) == 1
    assert not processed_df['Дата операции'].isna().any()


@pytest.fixture
def sample_transactions():
    """Фикстура с тестовыми транзакциями."""
    return pd.DataFrame({
        'Дата операции': [
            datetime(2023, 10, 1, 12, 0, 0),
            datetime(2023, 9, 15, 13, 0, 0),
            datetime(2023, 8, 1, 14, 0, 0),  # вне 3‑месячного периода
            datetime(2023, 7, 1, 15, 0, 0)   # вне 3‑месячного периода
        ],
        'Дата платежа': [datetime(2023, 10, 1)] * 4,
        'Сумма операции': [-1000.00, -500.00, -200.00, -300.00],
        'Категория': ['Супермаркеты', 'Супермаркеты', 'Супермаркеты', 'Кафе'],
        'Номер карты': ['1234'] * 4
    })


def test_filtering_by_category_and_date(sample_transactions):
    """Тест фильтрации по категории и дате."""
    reference_date = datetime(2023, 10, 31)
    result = spending_by_category(sample_transactions, 'Супермаркеты', reference_date)

    assert len(result) == 2  # Должны остаться только 2 транзакции за последние 3 месяца
    assert all(result['Сумма операции'] < 0)
    assert all(result['Категория'] == 'Супермаркеты')

def test_empty_result_when_no_matching_transactions(sample_transactions):
    """Тест пустого результата при отсутствии подходящих транзакций."""
    result = spending_by_category(sample_transactions, 'Неизвестная категория', datetime(2023, 10, 31))
    assert result.empty


def test_case_insensitive_category_matching(sample_transactions):
    """Тест нечувствительного к регистру сравнения категорий."""
    result_upper = spending_by_category(sample_transactions, 'СУПЕРМАРКЕТЫ', datetime(2023, 10, 31))
    result_lower = spending_by_category(sample_transactions, 'супермаркеты', datetime(2023, 10, 31))

    assert len(result_upper) == len(result_lower) == 2


def test_excludes_positive_amounts(sample_transactions):
    """Тест исключения транзакций с положительными суммами."""
    sample_transactions.loc[0, 'Сумма операции'] = 1000.00  # Положительная сумма
    result = spending_by_category(sample_transactions, 'Супермаркеты', datetime(2023, 10, 31))
    assert len(result) == 1  # Только одна отрицательная транзакция

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
