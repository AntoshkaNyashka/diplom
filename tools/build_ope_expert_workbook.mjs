import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "outputs/ope_expert_workbook";
const outputPath = `${outputDir}/expert_ope_tourism_routes.xlsx`;

await fs.mkdir(outputDir, { recursive: true });

const workbook = Workbook.create();

const criteria = [
  ["K1", "Соответствие интересам", "max"],
  ["K2", "Стоимость маршрута, руб.", "min"],
  ["K3", "Соответствие направлению", "max"],
  ["K4", "Сезонность", "max"],
  ["K5", "Длительность", "max"],
  ["K6", "Активность", "max"],
  ["K7", "Транспорт", "max"],
  ["K8", "Климат", "max"],
  ["K9", "Доступность", "max"],
  ["K10", "Инфраструктура", "max"],
];

const expertRanks = [
  [1, 1, 2, 1, 1],
  [2, 2, 1, 3, 2],
  [3, 4, 3, 2, 3],
  [4, 3, 4, 4, 4],
  [5, 5, 5, 5, 6],
  [6, 6, 6, 6, 5],
  [7, 7, 8, 7, 7],
  [8, 9, 7, 8, 9],
  [9, 8, 9, 9, 8],
  [10, 10, 10, 10, 10],
];

const alternatives = [
  ["Кисловодск: культурная программа", 8.2, 21100, 8, 10, 10, 10, 6.5, 10, 7.8, 8],
  ["Пятигорск: семейный отдых", 7.6, 18900, 8, 10, 10, 6.5, 10, 10, 7.8, 7],
  ["Ставрополь: активный маршрут", 8.0, 25900, 8, 10, 10, 6.5, 10, 10, 8.9, 8],
  ["Ессентуки: семейный отдых", 7.7, 19100, 8, 10, 10, 6.5, 10, 10, 7.8, 7],
  ["Минеральные Воды: семейный отдых", 7.4, 17900, 8, 10, 10, 6.5, 10, 10, 7.0, 6],
  ["Железноводск: семейный отдых", 7.2, 16700, 8, 10, 10, 6.5, 10, 10, 6.5, 6],
];

function styleTitle(sheet, range) {
  sheet.getRange(range).format = {
    fill: "#0F5F8F",
    font: { bold: true, color: "#FFFFFF", size: 14 },
  };
}

function styleHeader(sheet, range) {
  sheet.getRange(range).format = {
    fill: "#D9EAF7",
    font: { bold: true, color: "#1F2933" },
    wrapText: true,
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
}

function styleInput(sheet, range) {
  sheet.getRange(range).format = {
    fill: "#FFF7D6",
  };
}

function setWidths(sheet, widths) {
  widths.forEach(([range, width]) => {
    sheet.getRange(range).format.columnWidth = width;
  });
}

const intro = workbook.worksheets.add("Инструкция");
intro.getRange("A1:F1").values = [["Excel-шаблон для экспертной оценки ОПЭ туристических маршрутов", "", "", "", "", ""]];
styleTitle(intro, "A1:F1");
intro.getRange("A3:F10").values = [
  ["Назначение", "Файл подготовлен для расчета обобщенного показателя эффективности (ОПЭ) и экспертных весов критериев.", "", "", "", ""],
  ["Как использовать в программе", "Лист «Ранги экспертов» начинается с A1: ячейка A1 пустая, в первой строке имена экспертов, в первом столбце характеристики. Его можно загрузить как матрицу рангов.", "", "", "", ""],
  ["Правило рангов", "Ранг 1 означает самый важный критерий. Чем меньше ранг, тем выше значимость.", "", "", "", ""],
  ["Альтернативы", "Лист «Альтернативы» содержит абсолютные или балльные значения маршрутов. Для стоимости используется направление min, для остальных критериев max.", "", "", "", ""],
  ["Расчет", "Листы «Веса критериев», «ОПЭ расчет» и «Результат» содержат формулы Excel. Можно менять оценки экспертов и значения альтернатив.", "", "", "", ""],
  ["Связь с дипломом", "Критерии соответствуют рекомендательной системе подбора туристических маршрутов.", "", "", "", ""],
  ["", "", "", "", "", ""],
  ["Файл", "expert_ope_tourism_routes.xlsx", "", "", "", ""],
];
styleHeader(intro, "A3:A8");
setWidths(intro, [["A:A", 24], ["B:B", 110], ["C:F", 12]]);

const ranks = workbook.worksheets.add("Ранги экспертов");
ranks.getRange("A1:F1").values = [["", "Эксперт 1", "Эксперт 2", "Эксперт 3", "Эксперт 4", "Эксперт 5"]];
ranks.getRange("A2:F11").values = criteria.map((item, index) => [item[1], ...expertRanks[index]]);
styleHeader(ranks, "A1:F1");
styleInput(ranks, "B2:F11");
setWidths(ranks, [["A:A", 34], ["B:F", 13]]);
ranks.getRange("A13:F16").values = [
  ["Пояснение", "Этот лист можно загружать в программу из инструкции как матрицу с названиями характеристик и именами экспертов.", "", "", "", ""],
  ["", "A1 оставлена пустой специально.", "", "", "", ""],
  ["", "Ранги должны быть натуральными числами: 1, 2, 3 ...", "", "", "", ""],
  ["", "Наиболее важный критерий получает ранг 1.", "", "", "", ""],
];
styleHeader(ranks, "A13:A16");

const weights = workbook.worksheets.add("Веса критериев");
weights.getRange("A1:H1").values = [["Код", "Критерий", "Сумма рангов", "Средний ранг", "Обратная оценка", "Вес", "Вес, %", "Направление"]];
weights.getRange("A2:B11").values = criteria.map((item) => [item[0], item[1]]);
weights.getRange("H2:H11").values = criteria.map((item) => [item[2]]);
weights.getRange("C2").formulas = [["=SUM('Ранги экспертов'!B2:F2)"]];
weights.getRange("C2:C11").fillDown();
weights.getRange("D2").formulas = [["=AVERAGE('Ранги экспертов'!B2:F2)"]];
weights.getRange("D2:D11").fillDown();
weights.getRange("E2").formulas = [["=1/D2"]];
weights.getRange("E2:E11").fillDown();
weights.getRange("F2").formulas = [["=E2/SUM($E$2:$E$11)"]];
weights.getRange("F2:F11").fillDown();
weights.getRange("G2").formulas = [["=F2"]];
weights.getRange("G2:G11").fillDown();
weights.getRange("F2:G11").format.numberFormat = "0.00%";
styleHeader(weights, "A1:H1");
setWidths(weights, [["A:A", 10], ["B:B", 34], ["C:H", 16]]);

weights.getRange("J1:K1").values = [["Показатель", "Значение"]];
weights.getRange("J2:K8").values = [
  ["Количество критериев m", 10],
  ["Количество экспертов d", 5],
  ["Средняя сумма рангов", ""],
  ["S = сумма квадратов отклонений", ""],
  ["Коэффициент конкордации W", ""],
  ["χ² расчетное", ""],
  ["Вывод", ""],
];
weights.getRange("K4").formulas = [["=K3*(K2+1)/2"]];
weights.getRange("K5").formulas = [["=SUMXMY2(C2:C11,$K$4)"]];
weights.getRange("K6").formulas = [["=12*K5/(K3^2*(K2^3-K2))"]];
weights.getRange("K7").formulas = [["=K3*(K2-1)*K6"]];
weights.getRange("K8").formulas = [["=IF(K6>=0.5,\"эксперты согласованы\",\"нужна повторная оценка\")"]];
weights.getRange("K6:K7").format.numberFormat = "0.000";
styleHeader(weights, "J1:K1");
setWidths(weights, [["J:J", 34], ["K:K", 24]]);

const alt = workbook.worksheets.add("Альтернативы");
alt.getRange("A1:K1").values = [["", ...criteria.map((item) => item[1])]];
alt.getRange("A2:K7").values = alternatives;
styleHeader(alt, "A1:K1");
styleInput(alt, "B2:K7");
setWidths(alt, [["A:A", 38], ["B:B", 22], ["C:C", 18], ["D:K", 17]]);
alt.getRange("A9:K12").values = [
  ["Пояснение", "Этот лист содержит значения альтернатив по критериям. Для загрузки в программу используйте диапазон A1:K7.", "", "", "", "", "", "", "", "", ""],
  ["", "Стоимость является минимизируемым критерием: чем меньше цена, тем лучше.", "", "", "", "", "", "", "", "", ""],
  ["", "Остальные показатели заданы в баллах, где большее значение лучше.", "", "", "", "", "", "", "", "", ""],
  ["", "При необходимости замените маршруты и значения на свои.", "", "", "", "", "", "", "", "", ""],
];
styleHeader(alt, "A9:A12");

const calc = workbook.worksheets.add("ОПЭ расчет");
calc.getRange("A1:K1").values = [["Маршрут", ...criteria.map((item) => item[1])]];
calc.getRange("A2:A7").formulas = alternatives.map((_, index) => [`='Альтернативы'!A${index + 2}`]);
calc.getRange("B2").formulas = [[
  "=IF(MAX('Альтернативы'!B$2:B$7)=MIN('Альтернативы'!B$2:B$7),1,IF('Веса критериев'!H2=\"min\",(MAX('Альтернативы'!B$2:B$7)-'Альтернативы'!B2)/(MAX('Альтернативы'!B$2:B$7)-MIN('Альтернативы'!B$2:B$7)),('Альтернативы'!B2-MIN('Альтернативы'!B$2:B$7))/(MAX('Альтернативы'!B$2:B$7)-MIN('Альтернативы'!B$2:B$7))))",
]];
calc.getRange("B2:K7").fillRight();
calc.getRange("B2:K7").fillDown();
calc.getRange("L1:N1").values = [["ОПЭ", "ОПЭ, %", "Место"]];
calc.getRange("L2").formulas = [[
  "=B2*'Веса критериев'!$F$2+C2*'Веса критериев'!$F$3+D2*'Веса критериев'!$F$4+E2*'Веса критериев'!$F$5+F2*'Веса критериев'!$F$6+G2*'Веса критериев'!$F$7+H2*'Веса критериев'!$F$8+I2*'Веса критериев'!$F$9+J2*'Веса критериев'!$F$10+K2*'Веса критериев'!$F$11",
]];
calc.getRange("L2:L7").fillDown();
calc.getRange("M2").formulas = [["=L2"]];
calc.getRange("M2:M7").fillDown();
calc.getRange("N2").formulas = [["=RANK.EQ(L2,$L$2:$L$7,0)"]];
calc.getRange("N2:N7").fillDown();
calc.getRange("B2:M7").format.numberFormat = "0.00%";
styleHeader(calc, "A1:N1");
setWidths(calc, [["A:A", 38], ["B:K", 17], ["L:N", 13]]);

const result = workbook.worksheets.add("Результат");
result.getRange("A1:E1").values = [["Маршрут", "ОПЭ", "ОПЭ, %", "Место", "Интерпретация"]];
result.getRange("A2:A7").formulas = alternatives.map((_, index) => [`='ОПЭ расчет'!A${index + 2}`]);
result.getRange("B2").formulas = [["='ОПЭ расчет'!L2"]];
result.getRange("B2:B7").fillDown();
result.getRange("C2").formulas = [["=B2"]];
result.getRange("C2:C7").fillDown();
result.getRange("D2").formulas = [["='ОПЭ расчет'!N2"]];
result.getRange("D2:D7").fillDown();
result.getRange("E2").formulas = [["=IF(B2>=0.75,\"высокая эффективность\",IF(B2>=0.6,\"средняя эффективность\",\"низкая эффективность\"))"]];
result.getRange("E2:E7").fillDown();
result.getRange("B2:C7").format.numberFormat = "0.00%";
styleHeader(result, "A1:E1");
setWidths(result, [["A:A", 40], ["B:D", 13], ["E:E", 28]]);

result.getRange("G1:H1").values = [["Маршрут", "ОПЭ"]];
result.getRange("G2:H7").values = [
  ["Кисловодск", ""],
  ["Пятигорск", ""],
  ["Ставрополь", ""],
  ["Ессентуки", ""],
  ["Мин. Воды", ""],
  ["Железноводск", ""],
];
result.getRange("H2").formulas = [["=B2"]];
result.getRange("H2:H7").fillDown();
styleHeader(result, "G1:H1");
setWidths(result, [["G:G", 16], ["H:H", 13]]);
try {
  const chart = result.charts.add("bar", result.getRange("G1:H7"));
  chart.title = "ОПЭ туристических маршрутов";
  chart.hasLegend = false;
  chart.xAxis = { axisType: "textAxis" };
  chart.yAxis = { numberFormatCode: "0%" };
  chart.setPosition("J1", "Q18");
} catch (error) {
  // Диаграмма является визуальным дополнением; расчетная часть книги от нее не зависит.
}

const sheets = [intro, ranks, weights, alt, calc, result];
for (const sheet of sheets) {
  sheet.getRange("A1:Z200").format.font = { name: "Arial", size: 10 };
}

const inspect = await workbook.inspect({
  kind: "table",
  range: "Результат!A1:E7",
  include: "values,formulas",
  tableMaxRows: 10,
  tableMaxCols: 6,
});
console.log(inspect.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula errors",
});
console.log(errors.ndjson);

try {
  const preview = await workbook.render({
    sheetName: "Результат",
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(`${outputDir}/result_preview.png`, new Uint8Array(await preview.arrayBuffer()));
} catch (error) {
  console.warn(`Render skipped: ${error.message}`);
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(outputPath);
