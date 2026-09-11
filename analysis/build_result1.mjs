import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [solutionPath, outputPath] = process.argv.slice(2);
if (!solutionPath || !outputPath) {
  throw new Error("usage: node analysis/build_result1.mjs <solution.json> <result.xlsx>");
}

const solution = JSON.parse(await fs.readFile(solutionPath, "utf8"));
const workbook = await SpreadsheetFile.importXlsx(
  await FileBlob.load("附件/附件3/result1.xlsx"),
);

const letters = [];
for (let i = 0; i < 26; i += 1) letters.push(String.fromCharCode(65 + i));

function columnName(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

function roundedMatrix(matrix) {
  return matrix.map((row) => row.map((value) => Number(value.toFixed(4))));
}

const time = solution.time_s;
const distanceCm = solution.radius_m.map((value) => Number((value * 100).toFixed(1)));
const nRows = time.length;
const nColumns = distanceCm.length;
const lastColumn = columnName(nColumns);
const header = [["时间\\到药材中心的距离", ...distanceCm]];
const timeValues = time.map((value) => [value]);

for (const [sheetName, matrix] of [
  ["温度", solution.temperature_c],
  ["水分浓度", solution.moisture_dry_basis],
]) {
  const sheet = workbook.worksheets.getItem(sheetName);
  sheet.getRange(`A1:${lastColumn}1`).values = header;
  sheet.getRange(`A2:A${nRows + 1}`).values = timeValues;
  sheet.getRange(`B2:${lastColumn}${nRows + 1}`).values = roundedMatrix(matrix);

  const headerRange = sheet.getRange(`A1:${lastColumn}1`);
  headerRange.format = {
    font: { name: "宋体", size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: false,
  };
  const timeRange = sheet.getRange(`A2:A${nRows + 1}`);
  timeRange.format = {
    font: { name: "宋体", size: 11 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    numberFormat: "0",
  };
  const dataRange = sheet.getRange(`B2:${lastColumn}${nRows + 1}`);
  dataRange.format = {
    font: { name: "宋体", size: 11 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    numberFormat: "0.0000",
  };
  sheet.getRange(`A1:A${nRows + 1}`).format.columnWidth = 19.625;
  sheet.getRange(`B1:${lastColumn}1`).format.columnWidth = 9.625;
  const usedRange = sheet.getUsedRange().address;
  const expectedRange = `A1:${lastColumn}${nRows + 1}`;
  if (usedRange !== expectedRange) {
    throw new Error(`${sheetName}: expected used range ${expectedRange}, got ${usedRange}`);
  }
}

workbook.recalculate();

const preview = await workbook.render({
  sheetName: "温度",
  range: "A1:F20",
  scale: 1,
  format: "png",
});
await fs.writeFile(
  "/private/tmp/result1_temperature_preview.png",
  new Uint8Array(await preview.arrayBuffer()),
);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
console.log(`wrote ${outputPath}`);
