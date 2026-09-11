import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [solutionPath, outputPath, templatePath, sheetNamesArg] = process.argv.slice(2);
if (!solutionPath || !outputPath || !templatePath || !sheetNamesArg) {
  throw new Error(
    "usage: node analysis/build_two_sheet_workbook.mjs "
      + "<solution.json> <result.xlsx> <template.xlsx> <sheet1,sheet2>",
  );
}

const solution = JSON.parse(await fs.readFile(solutionPath, "utf8"));
const sheetNames = sheetNamesArg.split(",").map((name) => name.trim());
if (sheetNames.length !== 2) {
  throw new Error("exactly two sheet names are required");
}
const workbook = await SpreadsheetFile.importXlsx(
  await FileBlob.load(templatePath),
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
const fullDistanceCm = solution.radius_m.map((value) => value * 100.0);
const outputStepCm = 0.1;
const outputMaxCm = Number((Math.max(...fullDistanceCm)).toFixed(10));
const outputCount = Math.round(outputMaxCm / outputStepCm) + 1;
const distanceCm = Array.from(
  { length: outputCount },
  (_, index) => Number((index * outputStepCm).toFixed(10)),
);
const outputIndices = distanceCm.map((target) => {
  let bestIndex = 0;
  let bestDistance = Math.abs(fullDistanceCm[0] - target);
  for (let index = 1; index < fullDistanceCm.length; index += 1) {
    const distance = Math.abs(fullDistanceCm[index] - target);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  }
  if (bestDistance > 1e-9) {
    throw new Error(`no grid node matches output distance ${target} cm`);
  }
  return bestIndex;
});
const nRows = time.length;
const nColumns = distanceCm.length;
const lastColumn = columnName(nColumns);
const header = [["时间\\到药材中心的距离", ...distanceCm]];
const timeValues = time.map((value) => [value]);

function sampleMatrix(matrix) {
  return matrix.map((row) => outputIndices.map((index) => row[index]));
}

for (const [sheetName, matrix] of [
  [sheetNames[0], solution.temperature_c],
  [sheetNames[1], solution.moisture_dry_basis],
]) {
  const sampledMatrix = sampleMatrix(matrix);
  const sheet = workbook.worksheets.getItem(sheetName);
  sheet.getRange(`A1:${lastColumn}1`).values = header;
  sheet.getRange(`A2:A${nRows + 1}`).values = timeValues;
  sheet.getRange(`B2:${lastColumn}${nRows + 1}`).values = roundedMatrix(sampledMatrix);

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
  sheetName: sheetNames[0],
  range: "A1:F20",
  scale: 1,
  format: "png",
});
await fs.writeFile(
  `/private/tmp/${path.basename(outputPath)}_${sheetNames[0]}_preview.png`,
  new Uint8Array(await preview.arrayBuffer()),
);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
console.log(`wrote ${outputPath}`);
