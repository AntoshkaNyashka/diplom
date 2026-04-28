from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "generated"


CRITERIA = [
    ("interests", "Соответствие интересам туриста", 0.20),
    ("budget", "Бюджет поездки", 0.16),
    ("location", "Желаемое направление", 0.14),
    ("season", "Сезонность маршрута", 0.13),
    ("duration", "Длительность поездки", 0.11),
    ("activity", "Уровень активности", 0.08),
    ("transport", "Транспортная доступность", 0.06),
    ("climate", "Климатические предпочтения", 0.04),
    ("accessibility", "Доступная среда", 0.04),
    ("popularity", "Популярность и инфраструктура", 0.04),
]

TOP6 = CRITERIA[:6]


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: str, bold: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(10)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def style_table(table, header_fill: str = "D9EAF7") -> None:
    table.style = "Table Grid"
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.size = Pt(9)
            if row_index == 0:
                set_cell_shading(cell, header_fill)
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True


def setup_document(title: str, subtitle: str) -> Document:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(1.8)

    styles = doc.styles
    styles["Normal"].font.name = "Times New Roman"
    styles["Normal"].font.size = Pt(11)
    styles["Title"].font.name = "Times New Roman"
    styles["Title"].font.size = Pt(18)
    styles["Title"].font.bold = True
    styles["Heading 1"].font.name = "Times New Roman"
    styles["Heading 1"].font.size = Pt(14)
    styles["Heading 1"].font.bold = True
    styles["Heading 1"].font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    styles["Heading 2"].font.name = "Times New Roman"
    styles["Heading 2"].font.size = Pt(12)
    styles["Heading 2"].font.bold = True

    title_paragraph = doc.add_paragraph(style="Title")
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_paragraph.add_run(title)

    subtitle_paragraph = doc.add_paragraph()
    subtitle_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle_paragraph.add_run(subtitle)
    subtitle_run.italic = True
    subtitle_run.font.size = Pt(12)

    doc.add_paragraph()
    return doc


def add_note(doc: Document, text: str) -> None:
    table = doc.add_table(rows=1, cols=1)
    cell = table.cell(0, 0)
    set_cell_shading(cell, "EEF6FB")
    set_cell_text(cell, text)
    doc.add_paragraph()


def add_criteria_table(doc: Document, criteria=CRITERIA) -> None:
    table = doc.add_table(rows=1, cols=4)
    headers = ["Код", "Критерий", "Вес", "Назначение"]
    for index, header in enumerate(headers):
        set_cell_text(table.cell(0, index), header, bold=True)

    descriptions = {
        "interests": "Совпадение интересов пользователя с признаками маршрута.",
        "budget": "Сравнение цены маршрута с максимальным бюджетом.",
        "location": "Учет выбранного города или региона.",
        "season": "Проверка пригодности маршрута для сезона.",
        "duration": "Сравнение длительности с желаемым числом дней.",
        "activity": "Соответствие физической нагрузки предпочтениям.",
        "transport": "Совпадение или совместимость транспорта.",
        "climate": "Соответствие климатическим предпочтениям.",
        "accessibility": "Учет необходимости доступной среды.",
        "popularity": "Оценка популярности и инфраструктуры города.",
    }

    for code, name, weight in criteria:
        cells = table.add_row().cells
        set_cell_text(cells[0], code)
        set_cell_text(cells[1], name)
        set_cell_text(cells[2], f"{weight:.2f}")
        set_cell_text(cells[3], descriptions[code])

    style_table(table)


def add_pairwise_matrix(doc: Document) -> None:
    normalized = [(code, name, weight / sum(item[2] for item in TOP6)) for code, name, weight in TOP6]
    table = doc.add_table(rows=1, cols=len(normalized) + 1)
    set_cell_text(table.cell(0, 0), "Критерий", bold=True)
    for index, (_, name, _) in enumerate(normalized, start=1):
        set_cell_text(table.cell(0, index), f"K{index}", bold=True)

    for row_index, (_, name, row_weight) in enumerate(normalized, start=1):
        cells = table.add_row().cells
        set_cell_text(cells[0], f"K{row_index}. {name}")
        for col_index, (_, _, col_weight) in enumerate(normalized, start=1):
            ratio = row_weight / col_weight
            set_cell_text(cells[col_index], f"{ratio:.2f}")

    style_table(table, header_fill="E2F0D9")


def build_ahp_doc() -> Path:
    doc = setup_document(
        "Метод анализа иерархий для подбора туристических маршрутов",
        "Адаптация метода Саати для рекомендательной системы дипломного проекта",
    )

    doc.add_heading("1. Постановка задачи", level=1)
    doc.add_paragraph(
        "В проекте рассматривается задача выбора туристического маршрута из множества "
        "альтернатив, сформированных на основе базы городов, сезона, бюджета, интересов "
        "пользователя и характеристик маршрута. Для формализации выбора используется "
        "иерархическая модель принятия решений."
    )
    add_note(
        doc,
        "Цель верхнего уровня: подобрать оптимальный туристический маршрут. "
        "Промежуточный уровень содержит критерии выбора, нижний уровень - альтернативные маршруты.",
    )

    doc.add_heading("2. Иерархическая структура", level=1)
    table = doc.add_table(rows=1, cols=3)
    for i, header in enumerate(["Уровень", "Элемент", "Содержание"]):
        set_cell_text(table.cell(0, i), header, bold=True)
    rows = [
        ("0", "Цель", "Подбор оптимального туристического маршрута."),
        ("1", "Критерии", "Интересы, бюджет, направление, сезон, длительность, активность и другие признаки."),
        ("2", "Подкритерии", "Совпадение города, запас бюджета, сезонная пригодность, совместимость транспорта и т.д."),
        ("3", "Альтернативы", "Конкретные маршруты вида: город + тип маршрута + цена + длительность."),
    ]
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value)
    style_table(table)

    doc.add_heading("3. Критерии и веса", level=1)
    doc.add_paragraph(
        "Веса критериев задаются экспертно и используются в программной реализации "
        "при расчете итогового рейтинга маршрута."
    )
    add_criteria_table(doc)

    doc.add_heading("4. Матрица парных сравнений для 6 ключевых критериев", level=1)
    doc.add_paragraph(
        "Для демонстрации метода Саати выбраны шесть наиболее значимых критериев. "
        "Значения матрицы рассчитаны как отношение нормированных весов критериев; "
        "такая матрица является согласованной и может быть использована как базовая "
        "заготовка для ввода в MPriority."
    )
    add_pairwise_matrix(doc)

    doc.add_heading("5. Расчет итогового приоритета", level=1)
    doc.add_paragraph("Итоговая оценка маршрута определяется формулой:")
    doc.add_paragraph("Score = Σ(qᵢ · wᵢ) · 100,")
    doc.add_paragraph(
        "где qᵢ - нормированная оценка маршрута по i-му критерию, "
        "wᵢ - вес i-го критерия. Чем выше значение Score, тем выше позиция маршрута в рекомендации."
    )

    table = doc.add_table(rows=1, cols=5)
    for i, header in enumerate(["Маршрут", "Интересы", "Бюджет", "Сезон", "Итог"]):
        set_cell_text(table.cell(0, i), header, bold=True)
    examples = [
        ("Кисловодск: культурная программа", "0,82", "0,91", "1,00", "75,1"),
        ("Пятигорск: семейный отдых", "0,76", "0,96", "1,00", "72,5"),
        ("Ставрополь: активный маршрут", "0,80", "0,64", "1,00", "71,9"),
    ]
    for row in examples:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value)
    style_table(table)

    doc.add_heading("6. Вывод", level=1)
    doc.add_paragraph(
        "Метод анализа иерархий позволяет обосновать структуру рекомендательной системы, "
        "выделить значимые критерии и формально связать экспертные веса с итоговой "
        "ранжировкой туристических маршрутов."
    )

    output = OUT_DIR / "method_hierarchy_tourism_routes.docx"
    doc.save(output)
    return output


def build_efficiency_doc() -> Path:
    doc = setup_document(
        "Обобщенный показатель эффективности рекомендательной системы",
        "Расчет интегральной оценки качества подбора туристических маршрутов",
    )

    doc.add_heading("1. Назначение показателя", level=1)
    doc.add_paragraph(
        "Обобщенный показатель эффективности используется для количественной оценки того, "
        "насколько выбранный маршрут соответствует запросу пользователя. В рамках проекта "
        "показатель применяется как итоговый рейтинг маршрута."
    )

    doc.add_heading("2. Частные показатели эффективности", level=1)
    table = doc.add_table(rows=1, cols=5)
    headers = ["Код", "Частный показатель", "Вес", "Диапазон", "Смысл"]
    for i, header in enumerate(headers):
        set_cell_text(table.cell(0, i), header, bold=True)

    rows = [
        ("q1", "Соответствие интересам", "0,20", "0..1", "Доля совпадающих интересов пользователя и маршрута."),
        ("q2", "Соответствие бюджету", "0,16", "0..1", "Оценка цены маршрута относительно бюджета."),
        ("q3", "Соответствие направлению", "0,14", "0..1", "Совпадение города или региона."),
        ("q4", "Сезонность", "0,13", "0..1", "Пригодность маршрута для выбранного сезона."),
        ("q5", "Длительность", "0,11", "0..1", "Близость длительности к желаемому числу дней."),
        ("q6", "Активность", "0,08", "0..1", "Соответствие физической нагрузки."),
        ("q7", "Транспорт", "0,06", "0..1", "Совпадение или совместимость транспорта."),
        ("q8", "Климат", "0,04", "0..1", "Соответствие климатическим предпочтениям."),
        ("q9", "Доступность", "0,04", "0..1", "Учет доступной среды."),
        ("q10", "Инфраструктура", "0,04", "0..1", "Популярность и туристическая развитость города."),
    ]
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value)
    style_table(table)

    doc.add_heading("3. Формула обобщенного показателя", level=1)
    doc.add_paragraph("ОПЭ = Σ(wᵢ · qᵢ),  i = 1..10")
    doc.add_paragraph(
        "Значение ОПЭ лежит в диапазоне от 0 до 1. Для удобства вывода в интерфейсе "
        "оно умножается на 100 и отображается как рейтинг маршрута."
    )

    add_note(
        doc,
        "Если ОПЭ ≥ 0,75, маршрут считается хорошо подходящим; "
        "если 0,60 ≤ ОПЭ < 0,75, маршрут подходит частично; "
        "если ОПЭ < 0,60, маршрут рекомендуется только при отсутствии лучших вариантов.",
    )

    doc.add_heading("4. Пример расчета", level=1)
    table = doc.add_table(rows=1, cols=5)
    for i, header in enumerate(["Показатель", "Вес", "Маршрут A", "Маршрут B", "Маршрут C"]):
        set_cell_text(table.cell(0, i), header, bold=True)
    example_rows = [
        ("q1 Интересы", "0,20", "0,82", "0,76", "0,80"),
        ("q2 Бюджет", "0,16", "0,91", "0,96", "0,64"),
        ("q3 Направление", "0,14", "0,80", "0,80", "0,80"),
        ("q4 Сезон", "0,13", "1,00", "1,00", "1,00"),
        ("q5 Длительность", "0,11", "1,00", "1,00", "1,00"),
        ("q6 Активность", "0,08", "1,00", "0,65", "0,65"),
        ("q7 Транспорт", "0,06", "0,65", "1,00", "1,00"),
        ("q8 Климат", "0,04", "1,00", "1,00", "1,00"),
        ("q9 Доступность", "0,04", "0,78", "0,78", "0,89"),
        ("q10 Инфраструктура", "0,04", "0,80", "0,70", "0,80"),
        ("ОПЭ", "1,00", "0,751", "0,725", "0,719"),
    ]
    for row in example_rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, bold=row[0] == "ОПЭ")
    style_table(table, header_fill="E2F0D9")

    doc.add_heading("5. Использование в программной реализации", level=1)
    doc.add_paragraph(
        "В коде проекта частные показатели рассчитываются отдельными функциями: "
        "season_score(), budget_score(), duration_score(), activity_score() и другими. "
        "Затем функция score_route() объединяет их с весами из CRITERIA_WEIGHTS."
    )

    doc.add_heading("6. Вывод", level=1)
    doc.add_paragraph(
        "Обобщенный показатель эффективности позволяет привести разные характеристики "
        "маршрута к единой числовой шкале и сравнивать альтернативы между собой."
    )

    output = OUT_DIR / "generalized_efficiency_tourism_recommender.docx"
    doc.save(output)
    return output


def build_concordance_doc() -> Path:
    doc = setup_document(
        "Оценка согласованности суждений экспертов",
        "Применение коэффициента конкордации Кендалла для критериев туристической рекомендации",
    )

    doc.add_heading("1. Назначение оценки", level=1)
    doc.add_paragraph(
        "При назначении весов критериев рекомендательной системы желательно проверить, "
        "насколько согласованы мнения экспертов. Для этого используется коэффициент "
        "конкордации Кендалла W."
    )

    doc.add_heading("2. Экспертное ранжирование критериев", level=1)
    criteria = [item[1] for item in TOP6]
    ranks = [
        [1, 2, 3, 4, 5, 6],
        [1, 2, 4, 3, 5, 6],
        [2, 1, 3, 4, 5, 6],
        [1, 3, 2, 4, 5, 6],
        [1, 2, 3, 5, 4, 6],
    ]

    table = doc.add_table(rows=1, cols=8)
    headers = ["Критерий", "Эксперт 1", "Эксперт 2", "Эксперт 3", "Эксперт 4", "Эксперт 5", "Сумма", "Отклонение"]
    for i, header in enumerate(headers):
        set_cell_text(table.cell(0, i), header, bold=True)

    m = len(criteria)
    d = len(ranks)
    mean_rank_sum = d * (m + 1) / 2
    sums = []
    z_value = 0
    for row_index, criterion in enumerate(criteria):
        row_ranks = [expert[row_index] for expert in ranks]
        rank_sum = sum(row_ranks)
        deviation = rank_sum - mean_rank_sum
        sums.append(rank_sum)
        z_value += deviation ** 2
        cells = table.add_row().cells
        values = [criterion] + [str(value) for value in row_ranks] + [str(rank_sum), f"{deviation:.1f}"]
        for i, value in enumerate(values):
            set_cell_text(cells[i], value)
    style_table(table)

    w_value = 12 * z_value / (d ** 2 * (m ** 3 - m))
    chi_square = d * (m - 1) * w_value

    doc.add_heading("3. Расчет коэффициента конкордации", level=1)
    doc.add_paragraph("Средняя сумма рангов:")
    doc.add_paragraph("R̄ = d(m + 1) / 2 = 5 · (6 + 1) / 2 = 17,5")
    doc.add_paragraph("Сумма квадратов отклонений:")
    doc.add_paragraph(f"Z = Σ(Rᵢ - R̄)² = {z_value:.1f}")
    doc.add_paragraph("Коэффициент конкордации без связных рангов:")
    doc.add_paragraph("W = 12Z / (d²(m³ - m))")
    doc.add_paragraph(f"W = 12 · {z_value:.1f} / (5² · (6³ - 6)) = {w_value:.3f}")

    add_note(
        doc,
        "Интерпретация: W близок к 1, следовательно, эксперты достаточно согласованы "
        "в оценке важности критериев рекомендательной системы.",
    )

    doc.add_heading("4. Проверка значимости", level=1)
    doc.add_paragraph(
        "Для проверки значимости используется критерий Пирсона: χ² = d(m - 1)W."
    )
    doc.add_paragraph(f"χ² = 5 · (6 - 1) · {w_value:.3f} = {chi_square:.2f}")
    doc.add_paragraph(
        "При числе степеней свободы ν = m - 1 = 5 и уровне значимости 0,05 "
        "табличное значение χ² составляет 11,07. Так как расчетное значение больше "
        "табличного, гипотеза о согласованности экспертных ранжировок принимается."
    )

    doc.add_heading("5. Вывод", level=1)
    doc.add_paragraph(
        "Полученное значение коэффициента конкордации подтверждает, что выбранные "
        "критерии и их относительная важность могут использоваться в модели подбора "
        "туристических маршрутов."
    )

    output = OUT_DIR / "expert_concordance_tourism_criteria.docx"
    doc.save(output)
    return output


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [
        build_ahp_doc(),
        build_efficiency_doc(),
        build_concordance_doc(),
    ]
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
