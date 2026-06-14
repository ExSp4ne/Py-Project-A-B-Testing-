# -*- coding: utf-8 -*-
"""Главный исполняемый модуль приложения «Анализ A/B-тестирования (CTR)».

Реализует графический интерфейс пользователя на базе Tkinter: просмотр
данных в таблице, добавление, редактирование и удаление записей,
загрузку/сохранение данных в двоичном формате, очистку данных и
формирование текстовых и графических отчётов.

Приложение написано в функциональном стиле (без использования классов).
Запуск из корневого каталога work: python scripts/main.py

Автор: Власенков Максим Максимович (интерфейс и файловый ввод/вывод).
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Добавляем корневой каталог work в путь поиска модулей,
# чтобы импорты library и reports работали при запуске из любого места.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from library import utils  # noqa: E402
import reports  # noqa: E402


# Глобальное состояние приложения хранится в одном словаре,
# что позволяет обходиться без классов и передавать состояние
# во вложенные функции-обработчики.
STATE = {
    "config": None,      # объект конфигурации
    "data": None,        # текущий DataFrame
    "tree": None,        # виджет таблицы
    "status": None,      # переменная строки состояния
    "root": None,        # главное окно
}


def set_status(message):
    """Обновить текст в строке состояния приложения.

    Параметры:
        message (str): сообщение для пользователя.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    if STATE["status"] is not None:
        STATE["status"].set(message)


def refresh_table():
    """Перерисовать таблицу данных в интерфейсе по текущему DataFrame.

    Отображается ограниченное число строк (table_rows из конфигурации)
    для сохранения отзывчивости интерфейса на больших наборах.

    Параметры:
        Нет (использует глобальное состояние STATE).

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    tree = STATE["tree"]
    data_frame = STATE["data"]

    # Очистить текущее содержимое таблицы
    for item in tree.get_children():
        tree.delete(item)

    if data_frame is None:
        return

    limit = STATE["config"].getint("interface", "table_rows")
    shown = data_frame.head(limit)
    for position, (_, row) in enumerate(shown.iterrows()):
        tree.insert("", "end", iid=str(position),
                    values=(row["user_id"], row["timestamp"],
                            row["group"], row["landing_page"],
                            int(row["converted"])))

    set_status("Показано строк: " + str(len(shown))
               + " из " + str(len(data_frame)))


def action_load_csv():
    """Загрузить исходные данные из CSV и очистить их.

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    try:
        config = STATE["config"]
        raw = utils.load_csv(config.get("paths", "source_csv"))
        cleaned, stats = utils.clean_data(raw)
        STATE["data"] = cleaned
        refresh_table()
        messagebox.showinfo(
            "Загрузка CSV",
            "Данные загружены и очищены.\n"
            "Исходно строк: " + str(stats["initial"]) + "\n"
            "Удалено некорректных/дубликатов: " + str(stats["removed"]) + "\n"
            "Осталось строк: " + str(stats["after_mismatch"]))
    except (FileNotFoundError, ValueError) as error:
        messagebox.showerror("Ошибка загрузки CSV", str(error))


def action_save_binary():
    """Сохранить текущие данные в двоичный файл (.pkl).

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    if STATE["data"] is None:
        messagebox.showwarning("Сохранение", "Нет данных для сохранения.")
        return
    path = utils.save_binary(STATE["data"],
                             STATE["config"].get("paths", "binary_file"))
    set_status("Данные сохранены в двоичный файл: " + os.path.basename(path))
    messagebox.showinfo("Сохранение", "Данные сохранены в:\n" + path)


def action_load_binary():
    """Загрузить данные из двоичного файла (.pkl).

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    try:
        STATE["data"] = utils.load_binary(
            STATE["config"].get("paths", "binary_file"))
        refresh_table()
        set_status("Данные загружены из двоичного файла.")
    except FileNotFoundError as error:
        messagebox.showerror("Ошибка загрузки", str(error))


def action_add_record():
    """Открыть диалог добавления новой записи о пользователе.

    Для минимизации ручного ввода группа и страница выбираются
    из выпадающих списков, а признак конверсии — переключателем.

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    if STATE["data"] is None:
        messagebox.showwarning("Добавление", "Сначала загрузите данные.")
        return

    dialog = tk.Toplevel(STATE["root"])
    dialog.title("Добавить запись")
    dialog.transient(STATE["root"])
    dialog.resizable(False, False)

    # Поля ввода
    tk.Label(dialog, text="user_id:").grid(row=0, column=0, sticky="e",
                                           padx=6, pady=4)
    uid_var = tk.StringVar()
    tk.Entry(dialog, textvariable=uid_var).grid(row=0, column=1,
                                                padx=6, pady=4)

    tk.Label(dialog, text="timestamp:").grid(row=1, column=0, sticky="e",
                                             padx=6, pady=4)
    ts_var = tk.StringVar(value="2017-01-01 00:00:00")
    tk.Entry(dialog, textvariable=ts_var).grid(row=1, column=1,
                                               padx=6, pady=4)

    tk.Label(dialog, text="group:").grid(row=2, column=0, sticky="e",
                                         padx=6, pady=4)
    group_var = tk.StringVar(value="control")
    ttk.Combobox(dialog, textvariable=group_var,
                 values=["control", "treatment"],
                 state="readonly").grid(row=2, column=1, padx=6, pady=4)

    tk.Label(dialog, text="landing_page:").grid(row=3, column=0, sticky="e",
                                                padx=6, pady=4)
    page_var = tk.StringVar(value="old_page")
    ttk.Combobox(dialog, textvariable=page_var,
                 values=["old_page", "new_page"],
                 state="readonly").grid(row=3, column=1, padx=6, pady=4)

    tk.Label(dialog, text="converted:").grid(row=4, column=0, sticky="e",
                                             padx=6, pady=4)
    conv_var = tk.IntVar(value=0)
    tk.Checkbutton(dialog, text="конверсия совершена",
                   variable=conv_var).grid(row=4, column=1, sticky="w",
                                           padx=6, pady=4)

    def confirm():
        """Подтвердить добавление записи и закрыть диалог.

        Возвращает:
            None.

        Автор: Власенков Максим Максимович.
        """
        try:
            user_id = int(uid_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "user_id должен быть целым числом.",
                                 parent=dialog)
            return
        STATE["data"] = utils.add_record(
            STATE["data"], user_id, ts_var.get(), group_var.get(),
            page_var.get(), conv_var.get())
        refresh_table()
        set_status("Добавлена запись user_id=" + str(user_id))
        dialog.destroy()

    tk.Button(dialog, text="Добавить", command=confirm).grid(
        row=5, column=0, columnspan=2, pady=10)


def get_selected_index():
    """Получить позиционный индекс выбранной в таблице строки.

    Параметры:
        Нет.

    Возвращает:
        int или None: индекс выбранной строки либо None, если ничего
        не выбрано.

    Автор: Власенков Максим Максимович.
    """
    selection = STATE["tree"].selection()
    if not selection:
        return None
    return int(selection[0])


def action_delete_record():
    """Удалить выбранную в таблице запись.

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    if STATE["data"] is None:
        return
    index = get_selected_index()
    if index is None:
        messagebox.showwarning("Удаление", "Выберите строку в таблице.")
        return
    if messagebox.askyesno("Удаление", "Удалить выбранную запись?"):
        STATE["data"] = utils.delete_record(STATE["data"], index)
        refresh_table()
        set_status("Запись удалена.")


def action_edit_record():
    """Изменить значение в выбранной записи через диалог.

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    if STATE["data"] is None:
        return
    index = get_selected_index()
    if index is None:
        messagebox.showwarning("Редактирование", "Выберите строку в таблице.")
        return

    column = simpledialog.askstring(
        "Редактирование",
        "Какой столбец изменить?\n"
        "(user_id, timestamp, group, landing_page, converted)",
        parent=STATE["root"])
    if not column:
        return
    column = column.strip()
    if column not in utils.EXPECTED_COLUMNS:
        messagebox.showerror("Ошибка", "Неизвестный столбец: " + column)
        return

    value = simpledialog.askstring(
        "Редактирование", "Новое значение для столбца '" + column + "':",
        parent=STATE["root"])
    if value is None:
        return
    try:
        STATE["data"] = utils.update_record(STATE["data"], index,
                                            column, value)
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректное значение для " + column)
        return
    refresh_table()
    set_status("Запись изменена.")


def action_clean_data():
    """Повторно очистить текущие данные от дубликатов и ошибок.

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Шапкин Семён Григорьевич.
    """
    if STATE["data"] is None:
        messagebox.showwarning("Очистка", "Сначала загрузите данные.")
        return
    cleaned, stats = utils.clean_data(STATE["data"])
    STATE["data"] = cleaned
    refresh_table()
    messagebox.showinfo(
        "Очистка данных",
        "Очистка выполнена.\nУдалено строк: " + str(stats["removed"])
        + "\nОсталось: " + str(stats["after_mismatch"]))


def action_generate_reports():
    """Сформировать все отчёты (текстовый и графические).

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Зарипов Мурат Равилевич.
    """
    if STATE["data"] is None:
        messagebox.showwarning("Отчёты", "Сначала загрузите данные.")
        return
    try:
        paths = reports.generate_all_reports(STATE["data"], STATE["config"])
        set_status("Отчёты сформированы в каталогах output и graphics.")
        messagebox.showinfo(
            "Отчёты сформированы",
            "Текстовый отчёт:\n" + paths["text"] + "\n\n"
            "Столбчатая диаграмма:\n" + paths["bar"] + "\n\n"
            "Круговая диаграмма:\n" + paths["pie"])
    except Exception as error:  # показать пользователю любую ошибку
        messagebox.showerror("Ошибка формирования отчётов", str(error))


def action_show_text_report():
    """Показать текстовый отчёт в отдельном окне.

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    if STATE["data"] is None:
        messagebox.showwarning("Отчёт", "Сначала загрузите данные.")
        return
    config = STATE["config"]
    alpha = config.getfloat("analysis", "alpha")
    continuity = config.getboolean("analysis", "continuity_correction")
    output_dir = utils.ensure_dir(config.get("paths", "output_dir"))
    text_path = os.path.join(output_dir, config.get("reports", "text_report"))
    text = reports.build_text_report(STATE["data"], alpha, continuity,
                                     text_path)

    window = tk.Toplevel(STATE["root"])
    window.title("Текстовый отчёт")
    text_widget = tk.Text(window, width=70, height=24, wrap="word")
    text_widget.insert("1.0", text)
    text_widget.configure(state="disabled")
    text_widget.pack(fill="both", expand=True, padx=8, pady=8)


def build_toolbar(parent):
    """Создать панель кнопок управления приложением.

    Параметры:
        parent (tk.Widget): родительский контейнер.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    bar = tk.Frame(parent)
    bar.pack(side="top", fill="x", padx=6, pady=6)

    buttons = [
        ("Загрузить CSV", action_load_csv),
        ("Сохранить (PKL)", action_save_binary),
        ("Загрузить (PKL)", action_load_binary),
        ("Добавить", action_add_record),
        ("Редактировать", action_edit_record),
        ("Удалить", action_delete_record),
        ("Очистить данные", action_clean_data),
        ("Текстовый отчёт", action_show_text_report),
        ("Сформировать отчёты", action_generate_reports),
    ]
    for text, command in buttons:
        tk.Button(bar, text=text, command=command).pack(
            side="left", padx=3)


def build_table(parent):
    """Создать виджет таблицы (Treeview) для отображения данных.

    Параметры:
        parent (tk.Widget): родительский контейнер.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    frame = tk.Frame(parent)
    frame.pack(side="top", fill="both", expand=True, padx=6, pady=6)

    columns = ("user_id", "timestamp", "group", "landing_page", "converted")
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    widths = {"user_id": 90, "timestamp": 220, "group": 110,
              "landing_page": 120, "converted": 100}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=widths[col], anchor="center")

    scrollbar = ttk.Scrollbar(frame, orient="vertical",
                              command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    STATE["tree"] = tree


def build_statusbar(parent):
    """Создать строку состояния внизу окна.

    Параметры:
        parent (tk.Widget): родительский контейнер.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    status = tk.StringVar(value="Готово. Загрузите данные для начала работы.")
    STATE["status"] = status
    label = tk.Label(parent, textvariable=status, anchor="w",
                     relief="sunken")
    label.pack(side="bottom", fill="x")


def main():
    """Точка входа приложения: инициализация и запуск интерфейса.

    Загружает конфигурацию, создаёт главное окно и его элементы,
    при наличии готовит данные (двоичный файл либо исходный CSV).

    Параметры:
        Нет.

    Возвращает:
        None.

    Автор: Власенков Максим Максимович.
    """
    config = utils.load_config()
    STATE["config"] = config

    root = tk.Tk()
    STATE["root"] = root
    root.title(config.get("interface", "window_title"))
    width = config.getint("interface", "window_width")
    height = config.getint("interface", "window_height")
    root.geometry(str(width) + "x" + str(height))

    # Применяем настраиваемый через конфиг шрифт интерфейса
    font_family = config.get("interface", "font_family")
    font_size = config.getint("interface", "font_size")
    root.option_add("*Font", (font_family, font_size))

    build_toolbar(root)
    build_table(root)
    build_statusbar(root)

    # Стартовая загрузка данных: предпочитаем двоичный файл, иначе CSV.
    try:
        if utils.binary_exists(config.get("paths", "binary_file")):
            STATE["data"] = utils.load_binary(
                config.get("paths", "binary_file"))
            set_status("Данные загружены из двоичного файла.")
        else:
            raw = utils.load_csv(config.get("paths", "source_csv"))
            STATE["data"], _ = utils.clean_data(raw)
            set_status("Данные загружены из CSV и очищены.")
        refresh_table()
    except (FileNotFoundError, ValueError) as error:
        set_status("Данные не загружены: " + str(error))

    root.mainloop()


if __name__ == "__main__":
    main()
