# -*- coding: utf-8 -*-
"""Модуль универсальных функций приложения «Анализ A/B-тестирования».

Содержит функции для работы с конфигурацией, загрузки и очистки данных
средствами Pandas, сохранения/загрузки данных в двоичном формате (pickle),
работы со справочниками и расчёта статистических показателей.

Все функции написаны в функциональном стиле (без использования классов).

Автор: Шапкин Семён Григорьевич (логика обработки данных и статистика),
        Власенков Максим Максимович (файловый ввод/вывод).
"""

import os
import configparser

import numpy as np
import pandas as pd


# Ожидаемые столбцы исходного набора данных
EXPECTED_COLUMNS = ["user_id", "timestamp", "group",
                    "landing_page", "converted"]

# Корректные сочетания группы и показанной страницы
VALID_PAIRS = {"control": "old_page", "treatment": "new_page"}


def get_root_dir():
    """Вернуть абсолютный путь к корневому каталогу work.

    Путь вычисляется относительно расположения этого модуля
    (work/library/utils.py -> work), что гарантирует корректную
    работу независимо от текущего рабочего каталога.

    Параметры:
        Нет.

    Возвращает:
        str: абсолютный путь к каталогу work.

    Автор: Власенков Максим Максимович.
    """
    # Каталог library -> подняться на один уровень вверх до work
    library_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(library_dir)


def load_config(filename="config.ini"):
    """Загрузить конфигурационный файл приложения.

    Параметры:
        filename (str): имя конфигурационного файла в корне work.

    Возвращает:
        configparser.ConfigParser: объект с прочитанными настройками.

    Автор: Власенков Максим Максимович.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(get_root_dir(), filename)
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            "Не найден конфигурационный файл: " + config_path
        )
    # encoding указывается явно для поддержки кириллицы в комментариях
    config.read(config_path, encoding="utf-8")
    return config


def resolve_path(relative_path):
    """Преобразовать относительный путь (из конфига) в абсолютный.

    Параметры:
        relative_path (str): путь относительно каталога work.

    Возвращает:
        str: абсолютный путь к файлу или каталогу.

    Автор: Власенков Максим Максимович.
    """
    return os.path.join(get_root_dir(), relative_path)


def load_csv(csv_relative_path):
    """Загрузить исходные данные из CSV-файла в DataFrame.

    Параметры:
        csv_relative_path (str): относительный путь к CSV-файлу.

    Возвращает:
        pandas.DataFrame: загруженные данные.

    Автор: Власенков Максим Максимович.
    """
    path = resolve_path(csv_relative_path)
    if not os.path.exists(path):
        raise FileNotFoundError("Не найден файл данных CSV: " + path)
    data_frame = pd.read_csv(path)
    # Проверяем наличие всех ожидаемых столбцов
    missing = [c for c in EXPECTED_COLUMNS if c not in data_frame.columns]
    if missing:
        raise ValueError("В CSV отсутствуют столбцы: " + ", ".join(missing))
    return data_frame


def clean_data(data_frame):
    """Очистить набор данных от дубликатов и некорректных строк.

    Выполняемые операции:
        1. Удаление полностью повторяющихся строк.
        2. Удаление повторов по user_id (оставляется первая запись).
        3. Удаление строк с пропусками в ключевых столбцах.
        4. Удаление строк с недопустимым сочетанием group/landing_page
           (например, control + new_page).
        5. Приведение столбца converted к целочисленным значениям 0/1.

    Параметры:
        data_frame (pandas.DataFrame): исходные «грязные» данные.

    Возвращает:
        tuple: (очищенный DataFrame, словарь со статистикой очистки).

    Автор: Шапкин Семён Григорьевич.
    """
    stats = {"initial": len(data_frame)}

    # 1. Полные дубликаты строк
    data_frame = data_frame.drop_duplicates()
    stats["after_full_dup"] = len(data_frame)

    # 2. Дубликаты по идентификатору пользователя
    data_frame = data_frame.drop_duplicates(subset="user_id", keep="first")
    stats["after_user_dup"] = len(data_frame)

    # 3. Пропуски в ключевых столбцах
    data_frame = data_frame.dropna(subset=EXPECTED_COLUMNS)
    stats["after_dropna"] = len(data_frame)

    # 4. Несоответствие группы и показанной страницы.
    #    Создаём булеву маску корректных строк через map по VALID_PAIRS.
    expected_page = data_frame["group"].map(VALID_PAIRS)
    valid_mask = data_frame["landing_page"] == expected_page
    data_frame = data_frame[valid_mask]
    stats["after_mismatch"] = len(data_frame)

    # 5. Приведение типа целевого показателя к int
    data_frame = data_frame.copy()
    data_frame["converted"] = data_frame["converted"].astype(int)

    stats["removed"] = stats["initial"] - stats["after_mismatch"]
    return data_frame, stats


def save_binary(data_frame, binary_relative_path):
    """Сохранить DataFrame в двоичный формат (pickle).

    Параметры:
        data_frame (pandas.DataFrame): данные для сохранения.
        binary_relative_path (str): относительный путь к .pkl-файлу.

    Возвращает:
        str: абсолютный путь сохранённого файла.

    Автор: Власенков Максим Максимович.
    """
    path = resolve_path(binary_relative_path)
    data_frame.to_pickle(path)
    return path


def load_binary(binary_relative_path):
    """Загрузить DataFrame из двоичного файла (pickle).

    Параметры:
        binary_relative_path (str): относительный путь к .pkl-файлу.

    Возвращает:
        pandas.DataFrame: загруженные данные.

    Автор: Власенков Максим Максимович.
    """
    path = resolve_path(binary_relative_path)
    if not os.path.exists(path):
        raise FileNotFoundError("Не найден двоичный файл данных: " + path)
    return pd.read_pickle(path)


def binary_exists(binary_relative_path):
    """Проверить существование двоичного файла данных.

    Параметры:
        binary_relative_path (str): относительный путь к .pkl-файлу.

    Возвращает:
        bool: True, если файл существует.

    Автор: Власенков Максим Максимович.
    """
    return os.path.exists(resolve_path(binary_relative_path))


def load_reference(ref_relative_path):
    """Загрузить справочник (groups или pages) из CSV в DataFrame.

    Параметры:
        ref_relative_path (str): относительный путь к файлу справочника.

    Возвращает:
        pandas.DataFrame: содержимое справочника.

    Автор: Шапкин Семён Григорьевич.
    """
    path = resolve_path(ref_relative_path)
    if not os.path.exists(path):
        raise FileNotFoundError("Не найден файл справочника: " + path)
    return pd.read_csv(path)


def compute_ctr(data_frame):
    """Рассчитать показатели конверсии (CTR) по группам.

    Параметры:
        data_frame (pandas.DataFrame): очищенные данные.

    Возвращает:
        dict: для каждой группы — словарь с размером выборки,
              числом конверсий и значением CTR (доля).

    Автор: Шапкин Семён Григорьевич.
    """
    result = {}
    for group_name in ("control", "treatment"):
        subset = data_frame[data_frame["group"] == group_name]
        size = int(len(subset))
        conversions = int(subset["converted"].sum())
        ctr = conversions / size if size > 0 else 0.0
        result[group_name] = {
            "size": size,
            "conversions": conversions,
            "ctr": ctr,
        }
    return result


def z_test_proportions(conv_a, size_a, conv_b, size_b,
                       continuity=False):
    """Выполнить Z-критерий сравнения двух долей (конверсий).

    Реализация на NumPy без сторонних статистических библиотек.
    Используется двусторонний тест на равенство долей двух групп.

    Параметры:
        conv_a (int): число конверсий в группе A.
        size_a (int): размер группы A.
        conv_b (int): число конверсий в группе B.
        size_b (int): размер группы B.
        continuity (bool): применять ли поправку на непрерывность.

    Возвращает:
        tuple: (z-статистика, двустороннее p-значение).

    Автор: Шапкин Семён Григорьевич.
    """
    p_a = conv_a / size_a
    p_b = conv_b / size_b
    # Объединённая доля при справедливости нулевой гипотезы
    p_pool = (conv_a + conv_b) / (size_a + size_b)
    # Стандартная ошибка разности долей
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / size_a + 1 / size_b))
    if se == 0:
        return 0.0, 1.0
    diff = abs(p_a - p_b)
    # Поправка на непрерывность уменьшает абсолютную разность
    if continuity:
        diff = max(0.0, diff - (1 / (2 * size_a) + 1 / (2 * size_b)))
    z_stat = diff / se
    # Двустороннее p-значение через функцию ошибок (erf), без SciPy
    p_value = 2 * (1 - _normal_cdf(z_stat))
    return float(z_stat), float(p_value)


def _normal_cdf(x):
    """Функция распределения стандартного нормального закона.

    Вычисляется через функцию ошибок math.erf, что исключает
    необходимость в библиотеке SciPy.

    Параметры:
        x (float): значение аргумента.

    Возвращает:
        float: значение CDF N(0, 1) в точке x.

    Автор: Шапкин Семён Григорьевич.
    """
    import math
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def add_record(data_frame, user_id, timestamp, group, landing_page,
               converted):
    """Добавить новую запись о пользователе в DataFrame.

    Параметры:
        data_frame (pandas.DataFrame): текущие данные.
        user_id (int): идентификатор пользователя.
        timestamp (str): время действия.
        group (str): группа (control/treatment).
        landing_page (str): показанная страница (old_page/new_page).
        converted (int): признак конверсии (0/1).

    Возвращает:
        pandas.DataFrame: данные с добавленной строкой.

    Автор: Власенков Максим Максимович.
    """
    new_row = {
        "user_id": int(user_id),
        "timestamp": str(timestamp),
        "group": str(group),
        "landing_page": str(landing_page),
        "converted": int(converted),
    }
    new_df = pd.DataFrame([new_row])
    return pd.concat([data_frame, new_df], ignore_index=True)


def delete_record(data_frame, row_index):
    """Удалить запись по позиционному индексу строки.

    Параметры:
        data_frame (pandas.DataFrame): текущие данные.
        row_index (int): позиционный номер строки (0..N-1).

    Возвращает:
        pandas.DataFrame: данные без удалённой строки.

    Автор: Власенков Максим Максимович.
    """
    data_frame = data_frame.reset_index(drop=True)
    if 0 <= row_index < len(data_frame):
        data_frame = data_frame.drop(index=row_index).reset_index(drop=True)
    return data_frame


def update_record(data_frame, row_index, column, value):
    """Изменить значение в указанной ячейке DataFrame.

    Параметры:
        data_frame (pandas.DataFrame): текущие данные.
        row_index (int): позиционный номер строки.
        column (str): имя изменяемого столбца.
        value: новое значение.

    Возвращает:
        pandas.DataFrame: данные с применённым изменением.

    Автор: Власенков Максим Максимович.
    """
    data_frame = data_frame.reset_index(drop=True)
    if 0 <= row_index < len(data_frame) and column in data_frame.columns:
        if column in ("user_id", "converted"):
            value = int(value)
        data_frame.at[row_index, column] = value
    return data_frame


def ensure_dir(relative_path):
    """Создать каталог (если он отсутствует) и вернуть абсолютный путь.

    Параметры:
        relative_path (str): относительный путь к каталогу.

    Возвращает:
        str: абсолютный путь к каталогу.

    Автор: Власенков Максим Максимович.
    """
    path = resolve_path(relative_path)
    os.makedirs(path, exist_ok=True)
    return path
