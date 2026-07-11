from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
ET.register_namespace("", NS["x"])

def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name

def read_values(xlsx: Path) -> list[list[object]]:
    def normalize_text(value: str) -> str:
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    with zipfile.ZipFile(xlsx) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.itertext()) for node in root.findall("x:si", NS)]
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in root.findall(".//x:sheetData/x:row", NS):
        values = []
        for cell in row.findall("x:c", NS):
            ref = cell.attrib.get("r", "A1")
            col = re.match(r"[A-Z]+", ref).group(0)
            index = 0
            for char in col: index = index * 26 + ord(char) - 64
            while len(values) < index: values.append(None)
            kind = cell.attrib.get("t")
            value_node = cell.find("x:v", NS)
            if kind == "inlineStr": value = normalize_text("".join(cell.itertext()))
            elif value_node is None: value = None
            elif kind == "s": value = normalize_text(shared[int(value_node.text)])
            elif kind in ("str", "inlineStr"): value = normalize_text(value_node.text or "")
            else:
                raw = value_node.text
                try: value = float(raw) if raw and "." in raw else int(raw) if raw else None
                except ValueError: value = normalize_text(raw or "")
            values[index - 1] = value
        rows.append(values)
    return rows

def write_row(template: Path, row_number: int, values: list[object]) -> None:
    with zipfile.ZipFile(template) as source:
        files = {name: source.read(name) for name in source.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find("x:sheetData", NS)
    existing = {int(row.attrib["r"]): row for row in sheet_data.findall("x:row", NS)}
    style_source = existing.get(7) or existing.get(6)
    styles = {re.match(r"[A-Z]+", cell.attrib.get("r", "A1")).group(0): cell.attrib.get("s") for cell in style_source.findall("x:c", NS)} if style_source is not None else {}
    if row_number in existing: sheet_data.remove(existing[row_number])
    new_row = ET.Element(f"{{{NS['x']}}}row", {"r": str(row_number), "spans": f"1:{len(values)}"})
    for index, value in enumerate(values, 1):
        if value is None or value == "": continue
        col = column_name(index)
        attrs = {"r": f"{col}{row_number}"}
        if styles.get(col): attrs["s"] = styles[col]
        cell = ET.SubElement(new_row, f"{{{NS['x']}}}c", attrs)
        if isinstance(value, (int, float)):
            ET.SubElement(cell, f"{{{NS['x']}}}v").text = str(value)
        else:
            cell.attrib["t"] = "inlineStr"
            inline = ET.SubElement(cell, f"{{{NS['x']}}}is")
            ET.SubElement(inline, f"{{{NS['x']}}}t").text = str(value)
    inserted = False
    for position, row in enumerate(sheet_data.findall("x:row", NS)):
        if int(row.attrib["r"]) > row_number:
            sheet_data.insert(position, new_row); inserted = True; break
    if not inserted: sheet_data.append(new_row)
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", dir=template.parent) as tmp:
        temp_path = Path(tmp.name)
    with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as output:
        for name, content in files.items(): output.writestr(name, content)
    temp_path.replace(template)

root = Path(sys.argv[1])
master_rows = read_values(root / "input.excel")
headers = master_rows[0]
category_index = headers.index("类目")
sku_index = headers.index("商家 SKU")
category_map = json.loads((root / "category_map.json").read_text(encoding="utf-8"))
template_by_category = {}
for line in (root / "muban" / "类目.md").read_text(encoding="utf-8").splitlines():
    match = re.match(r"\s*\d+\.\s+(.+?)\s+<!--\s*(.+?\.xlsx)\s*-->", line)
    if match: template_by_category[match.group(1).strip()] = match.group(2).strip()
registry_path = root / "template_rows.json"
registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {}
for row in master_rows[1:]:
    if len(row) <= sku_index or not row[sku_index]: continue
    category, sku = str(row[category_index]), str(row[sku_index])
    template_name = template_by_category[category]
    folder = root / "类目模板输出" / Path(template_name).stem
    folder.mkdir(parents=True, exist_ok=True)
    template = folder / template_name
    if not template.exists(): shutil.copy2(root / "muban" / "leimu" / template_name, template)
    registry.setdefault(template_name, {})
    row_number = registry[template_name].get(sku, max([8, *registry[template_name].values()]) + 1)
    registry[template_name][sku] = row_number
    write_row(template, row_number, row[:31] + [None] * 4)
    for extra in folder.glob("*_importacao*.xlsx"):
        extra.unlink()
    print(f"{sku} -> {template} row {row_number}")
registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
