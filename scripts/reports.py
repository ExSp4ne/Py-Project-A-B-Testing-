# -*- coding: utf-8 -*-
"""Модуль построения отчётов приложения «Анализ A/B-тестирования».

Содержит функции формирования текстового отчёта (.txt) и графических
отчётов (.png): столбчатой диаграммы сравнения CTR и круговой диаграммы
распределения пользователей по группам. Построение графиков выполняется
средствами Matplotlib.

Все функции написаны в функциональном стиле (без классов).

Автор: Зарипов Мурат Равилевич (визуализация),
        Шапкин Семён Григорьевич (текстовый аналитический вывод).
"""

import os

import matplotlib

# Используем неинтерактивный backend, чтобы графики строились без окна
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (импорт после set backend)

from library import utils  # noqa: E402


def build_text_report(data_frame, alpha, continuity, output_path):
    """Сформировать текстовый отчёт по результатам A/B-теста.

    Отчёт содержит размер выборки и CTR каждой группы, результат
    Z-критерия значимости различий и текстовый вывод о наличии
    статистически значимого эффекта.

    Параметры:
        data_frame (pandas.DataFrame): очищенные данные.
        alpha (float): уровень значимости.
        continuity (bool): поправка на непрерывность для Z-критерия.
        output_path (str): абсолютный путь к сохраняемому .txt-файлу.

    Возвращает:
        str: текст сформированного отчёта.

    Автор: Шапкин Семён Григорьевич.
    """
    ctr = utils.compute_ctr(data_frame)
    control = ctr["control"]
    treatment = ctr["treatment"]

    z_stat, p_value = utils.z_test_proportions(
        control["conversions"], control["size"],
        treatment["conversions"], treatment["size"],
        continuity=continuity,
    )

    significant = p_value < alpha
    if significant:
        if treatment["ctr"] > control["ctr"]:
            verdict = ("Различия статистически значимы: тестовая группа "
                       "показывает более высокую конверсию.")
        else:
            verdict = ("Различия статистически значимы: контрольная группа "
                       "показывает более высокую конверсию.")
    else:
        verdict = ("Статистически значимых различий между группами "
                   "не обнаружено.")

    lines = []
    lines.append("=" * 60)
    lines.append("ОТЧЁТ ОБ АНАЛИЗЕ РЕЗУЛЬТАТОВ A/B-ТЕСТИРОВАНИЯ (CTR)")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Размеры выборок:")
    lines.append("    Контрольная группа (control):  "
                 + str(control["size"]) + " пользователей")
    lines.append("    Тестовая группа (treatment):   "
                 + str(treatment["size"]) + " пользователей")
    lines.append("")
    lines.append("Показатель конверсии (CTR):")
    lines.append("    control:    " + _fmt_pct(control["ctr"])
                 + "  (" + str(control["conversions"]) + " конверсий)")
    lines.append("    treatment:  " + _fmt_pct(treatment["ctr"])
                 + "  (" + str(treatment["conversions"]) + " конверсий)")
    lines.append("")
    abs_diff = treatment["ctr"] - control["ctr"]
    lines.append("    Абсолютная разница CTR: " + _fmt_pct(abs_diff))
    lines.append("")
    lines.append("Статистический тест (двусторонний Z-критерий долей):")
    lines.append("    Z-статистика:        " + ("%.4f" % z_stat))
    lines.append("    p-значение:          " + ("%.6f" % p_value))
    lines.append("    Уровень значимости:  " + ("%.3f" % alpha))
    lines.append("    Поправка на непрерывность: "
                 + ("да" if continuity else "нет"))
    lines.append("")
    lines.append("Вывод:")
    lines.append("    " + verdict)
    lines.append("")
    lines.append("=" * 60)

    report_text = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as file_obj:
        file_obj.write(report_text)

    return report_text


def _fmt_pct(value):
    """Отформатировать долю как процент с двумя знаками.

    Параметры:
        value (float): доля (например, 0.12).

    Возвращает:
        str: строка вида '12.00%'.

    Автор: Шапкин Семён Григорьевич.
    """
    return ("%.2f" % (value * 100.0)) + "%"


def build_bar_chart(data_frame, output_path, dpi):
    """Построить столбчатую диаграмму сравнения CTR групп.

    Параметры:
        data_frame (pandas.DataFrame): очищенные данные.
        output_path (str): абсолютный путь к сохраняемому .png-файлу.
        dpi (int): разрешение изображения.

    Возвращает:
        str: путь сохранённого файла.

    Автор: Зарипов Мурат Равилевич.
    """
    ctr = utils.compute_ctr(data_frame)
    groups = ["control", "treatment"]
    values = [ctr["control"]["ctr"] * 100.0,
              ctr["treatment"]["ctr"] * 100.0]
    colors = ["#4C72B0", "#DD8452"]

    figure, axes = plt.subplots(figsize=(7, 5))
    bars = axes.bar(groups, values, color=colors, width=0.55)

    # Подписи значений над столбцами
    for bar_obj, val in zip(bars, values):
        axes.text(bar_obj.get_x() + bar_obj.get_width() / 2.0,
                  val, ("%.2f%%" % val),
                  ha="center", va="bottom", fontsize=11)

    axes.set_title("Сравнение конверсии (CTR) по группам")
    axes.set_ylabel("Конверсия, %")
    axes.set_xlabel("Группа")
    axes.set_ylim(0, max(values) * 1.25 if max(values) > 0 else 1)
    axes.grid(axis="y", linestyle="--", alpha=0.4)

    figure.tight_layout()
    figure.savefig(output_path, dpi=dpi)
    plt.close(figure)
    return output_path


def build_pie_chart(data_frame, output_path, dpi):
    """Построить круговую диаграмму распределения пользователей по группам.

    Параметры:
        data_frame (pandas.DataFrame): очищенные данные.
        output_path (str): абсолютный путь к сохраняемому .png-файлу.
        dpi (int): разрешение изображения.

    Возвращает:
        str: путь сохранённого файла.

    Автор: Зарипов Мурат Равилевич.
    """
    ctr = utils.compute_ctr(data_frame)
    sizes = [ctr["control"]["size"], ctr["treatment"]["size"]]
    labels = ["control", "treatment"]
    colors = ["#4C72B0", "#DD8452"]

    figure, axes = plt.subplots(figsize=(6, 6))
    axes.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
             startangle=90, counterclock=False,
             wedgeprops={"edgecolor": "white"})
    axes.set_title("Распределение пользователей по группам")
    axes.axis("equal")  # круг, а не эллипс

    figure.tight_layout()
    figure.savefig(output_path, dpi=dpi)
    plt.close(figure)
    return output_path


def generate_all_reports(data_frame, config):
    """Сформировать все отчёты (текстовый и графические) разом.

    Параметры:
        data_frame (pandas.DataFrame): очищенные данные.
        config (configparser.ConfigParser): настройки приложения.

    Возвращает:
        dict: пути к сформированным файлам отчётов.

    Автор: Зарипов Мурат Равилевич.
    """
    alpha = config.getfloat("analysis", "alpha")
    continuity = config.getboolean("analysis", "continuity_correction")
    dpi = config.getint("reports", "chart_dpi")

    output_dir = utils.ensure_dir(config.get("paths", "output_dir"))
    graphics_dir = utils.ensure_dir(config.get("paths", "graphics_dir"))

    text_path = os.path.join(output_dir,
                             config.get("reports", "text_report"))
    bar_path = os.path.join(graphics_dir,
                            config.get("reports", "bar_chart"))
    pie_path = os.path.join(graphics_dir,
                            config.get("reports", "pie_chart"))

    build_text_report(data_frame, alpha, continuity, text_path)
    build_bar_chart(data_frame, bar_path, dpi)
    build_pie_chart(data_frame, pie_path, dpi)

    return {"text": text_path, "bar": bar_path, "pie": pie_path}
