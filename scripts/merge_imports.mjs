import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [root, masterPath] = process.argv.slice(2);
if (!root || !masterPath) throw new Error("Usage: merge_imports.mjs <workspace-root> <master-path>");
const categoryMap = JSON.parse(await fs.readFile(path.join(root, "category_map.json"), "utf8").catch(() => "{}"));
const skuHeader = "\u5546\u5bb6 SKU";
const categoryHeader = "\u7c7b\u76ee";
const brandHeader = "\u54c1\u724c";
let header = null;
const rowsBySku = new Map();

function addRows(values) {
  if (!values?.length) return;
  const incomingHeader = values[0];
  const hasMasterColumns = incomingHeader[0] === categoryHeader && incomingHeader[1] === brandHeader;
  const baseHeader = hasMasterColumns ? incomingHeader.slice(2) : incomingHeader;
  if (!header) header = baseHeader;
  const skuIndex = header.indexOf(skuHeader);
  for (const sourceRow of values.slice(1)) {
    const row = hasMasterColumns ? sourceRow.slice(2) : sourceRow;
    if (!row?.some(value => value !== null && value !== "")) continue;
    const sku = String(row[skuIndex] ?? "");
    if (sku) rowsBySku.set(sku, row);
  }
}

try {
  await fs.access(masterPath);
  const master = await SpreadsheetFile.importXlsx(await FileBlob.load(masterPath));
  addRows(master.worksheets.getItemAt(0).getUsedRange(true).values);
} catch (error) {
  if (error?.code !== "ENOENT") throw error;
}

const entries = await fs.readdir(root, { withFileTypes: true });
for (const entry of entries) {
  if (!entry.isDirectory() || !entry.name.startsWith("processed_")) continue;
  const outputDir = path.join(root, entry.name, "output");
  let files;
  try { files = await fs.readdir(outputDir, { withFileTypes: true }); } catch { continue; }
  const candidates = await Promise.all(files.filter(file => file.isFile() && !file.name.startsWith("~$") && /_importacao.*\.xlsx$/i.test(file.name)).map(async file => {
    const fullPath = path.join(outputDir, file.name);
    return { fullPath, name: file.name, stat: await fs.stat(fullPath) };
  }));
  if (!candidates.length) continue;
  candidates.sort((a, b) => Number(b.name.includes("9_imagens")) - Number(a.name.includes("9_imagens")) || b.stat.mtimeMs - a.stat.mtimeMs);
  const product = await SpreadsheetFile.importXlsx(await FileBlob.load(candidates[0].fullPath));
  addRows(product.worksheets.getItemAt(0).getUsedRange(true).values);
}
if (!header) throw new Error("No product rows found in completed imports or master table");

const skuIndex = header.indexOf(skuHeader);
const rows = [...rowsBySku.values()].sort((a, b) => String(a[skuIndex]).localeCompare(String(b[skuIndex]))).map(row => [categoryMap[String(row[skuIndex])] ?? "\u5f85\u5339\u914d", "\u65e0\u54c1\u724c", ...row]);
const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Importacao");
sheet.showGridLines = false;
sheet.getRange("A1:AE1").values = [[categoryHeader, brandHeader, ...header]];
sheet.getRange(`A2:AE${rows.length + 1}`).values = rows;
sheet.getRange("A1:AE1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" }, wrapText: true, horizontalAlignment: "center", verticalAlignment: "center" };
sheet.getRange(`A1:AE${rows.length + 1}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
sheet.getRange(`A2:AE${rows.length + 1}`).format = { verticalAlignment: "top", wrapText: true };
sheet.getRange("A1").format.columnWidth = 36; sheet.getRange("B1").format.columnWidth = 16; sheet.getRange("C1").format.columnWidth = 42; sheet.getRange("D1").format.columnWidth = 68; sheet.getRange("E1:M1").format.columnWidth = 44;
sheet.getRange("N1:O1").format.columnWidth = 18; sheet.getRange("P1:T1").format.columnWidth = 28; sheet.getRange("U1:Y1").format.columnWidth = 18; sheet.getRange("Z1:AE1").format.columnWidth = 20;
sheet.getRange("A1:AE1").format.rowHeight = 38; sheet.getRange(`A2:AE${rows.length + 1}`).format.rowHeight = 72;
sheet.freezePanes.freezeRows(1);
const table = sheet.tables.add(`A1:AE${rows.length + 1}`, true, "MasterImport"); table.showBandedColumns = false; table.showFilterButton = true;
const preview = await workbook.render({ sheetName: "Importacao", range: `A1:AE${rows.length + 1}`, scale: 1, format: "png" });
await fs.writeFile(path.join(path.dirname(masterPath), "input.excel.preview.png"), new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(masterPath);
const check = await workbook.inspect({ kind: "table", range: `Importacao!A1:AE${rows.length + 1}`, include: "values", tableMaxRows: 20, tableMaxCols: 31 });
console.log(check.ndjson);
