"""Prepare one ecommerce product folder for the Brazil Product Batch workflow."""
from __future__ import annotations

import argparse, csv, json, re, shutil, sys
from pathlib import Path
from urllib.request import Request, urlopen

URL_RE = re.compile(r'https?://[^"\'\s>]+')

def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "gb18030", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            pass
    return path.read_text(errors="replace")

def tokenize(value: str) -> set[str]:
    return set(re.findall(r"[A-Za-zÀ-ÿ0-9]+", value.lower()))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sku")
    args = parser.parse_args()
    text_files = sorted(args.folder.glob("*.txt"))
    if not text_files:
        raise SystemExit("No .txt file found in product folder")
    source_text = read_text(text_files[0])
    title = source_text.splitlines()[0].strip()
    urls = list(dict.fromkeys(URL_RE.findall(source_text)))[:9]
    if not urls:
        raise SystemExit("No image URLs found")
    args.output.mkdir(parents=True, exist_ok=True)
    source_dir = args.output / "source_images"
    source_dir.mkdir(exist_ok=True)
    downloaded = []
    for index, url in enumerate(urls, 1):
        target = source_dir / f"{index:02d}.jpg"
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response, target.open("wb") as file:
            shutil.copyfileobj(response, file)
        downloaded.append(str(target))
    rows = list(csv.DictReader(args.inventory.open(encoding="utf-8-sig", newline="")))
    selected = [row for row in rows if row.get("SKU") == args.sku] if args.sku else []
    title_words = tokenize(title)
    scored = []
    for row in rows:
        score = len(title_words & tokenize(row.get("标题", "")))
        if score:
            scored.append({"sku": row.get("SKU"), "title": row.get("标题"), "score": score,
                           "available_stock": row.get("可用库存"), "cost": row.get("平均成本")})
    manifest = {
        "source_folder": str(args.folder), "product_title": title, "source_urls": urls,
        "downloaded_images": downloaded, "selected_inventory": selected,
        "inventory_candidates": sorted(scored, key=lambda item: item["score"], reverse=True)[:10],
        "next_step": "Confirm selected SKU before generating or publishing images."
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
