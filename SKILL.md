---
name: tk-up
description: Process local product folders into Brazilian TikTok Shop listings. Use when folders contain product-name text and image URLs and the task requires SKU matching, nine localized images, GitHub image links, a master import table, and records written into the correct TikTok category template.
---

# TK-UP

Use this workflow for one product folder at a time. Do not overwrite prior `processed_<SKU>` outputs. The required deliverable is exactly nine final images for every product.

## Workspace setup

Require the user workspace to contain `填写要求.txt`, an inventory CSV, and one or more product folders. Copy `assets/muban` into `<workspace-root>/muban` if that folder is absent; it contains `类目.md` and the category templates required for final TikTok imports. Never package or request another user's inventory CSV, product source files, GitHub credentials, or generated outputs.

## Prepare

1. Read `填写要求.txt` in the workspace and the product folder's `.txt` file.
2. Run `scripts/prepare_product.py <folder> --inventory <csv> --output <output-dir> [--sku <SKU>]`.
   It extracts up to nine source URLs, downloads them, and writes `manifest.json`.
3. Confirm the candidate SKU against product type, variant, stock, and cost. If candidates are ambiguous, ask the user. Use the selected SKU for the output directory and GitHub path; do not reuse a hard-coded path from a prior product.

## Generate images

Use the `imagegen` skill. Inspect all source images first. Select the clearest white-background product photo as the structural reference.

### Mandatory image-tool gate

Before downloading-only processing, creating any spreadsheet, publishing to GitHub, or reporting completion, verify that the active Codex session exposes the built-in `image_gen` tool.

- If `image_gen` is unavailable, stop and tell the user: `图片生成功能在当前 Codex 会话不可用，因此不能完成 TK-UP；未生成图片时不得输出导入表。` Do not substitute source images, copied images, placeholders, or only downloaded assets.
- If it is available, make real `image_gen` tool calls. A prompt, a script, an image URL list, or a downloaded source image does not count as generation.
- Record the nine final local output paths in `manifest.json`. Do not create a product workbook, update `input.excel`, or write a category template until the manifest contains all nine files and each is verified at 800×800.

- Run exactly nine image-generation/editing jobs: one new main image plus eight support images. Do not stop at the number of downloaded source images.
- Localize each usable source image first. Preserve product structure, colors, and material; replace Chinese text with pt-BR only. Exclude source images that show a different SKU/variant unless the workbook declares that variant.
- When fewer than eight usable source images exist, use the white-background structural reference to generate the missing distinct support images. Fill the next numbered slots with product-only, feature close-up, controls/operation, LED/color mode, lifestyle use, packaging/contents, dimensions (only if verified), and care/detail views. Do not invent specifications, accessories, or medical claims.
- Call `image_gen` once for every missing numbered slot. Treat a prompt list or an output plan as incomplete work: save an actual generated file for `main.png` and every `image-2.png` through `image-9.png`.
- Before publishing, count the files and validate exactly nine final PNGs, each 800×800. If the count is not nine, continue generation rather than delivering an incomplete workbook.

## Publish and build the import file

1. Publish to `products/<SKU>/` in the configured GitHub image repository. Verify the raw main-image URL returns HTTP 200 before building the workbook.
2. Price rule: cost below 50 × 5; cost 50 or above × 3. Use available stock as quantity. Estimate package size/weight only when no source data exists, and mark these estimates in the manifest.
3. Create a one-row `.xlsx` import workbook using the `spreadsheets` skill and the manifest. Include product name/description, all image links, SKU variant, package details, price, quantity, and merchant SKU.
4. Read `<workspace-root>/类目.md` using UTF-8 and select the most specific listed category for the product. Before merging, update `<workspace-root>/category_map.json` with `{ "<SKU>": "<exact category from 类目.md>" }`. Set brand to `无品牌` for every product.
5. Update the workspace master table at `input.excel`. Run `scripts/merge_imports.mjs <workspace-root> <workspace-root>/input.excel` from a writable working copy that has access to `@oai/artifact-tool`. It selects the newest completed workbook for each `processed_<SKU>` folder, replaces any existing master rows with the same merchant SKU, and preserves one row per SKU. The first two master columns must be `类目` and `品牌`.
6. Read `<workspace-root>/muban/类目.md` to map the selected exact category to its `.xlsx` template under `<workspace-root>/muban/leimu`. Run `scripts/write_records_to_templates.py <workspace-root>`. For each category, copy the mapped template once into `类目模板输出/<模板名>/<模板名>.xlsx`, then add or update product records only inside that copied template. Do not create separate product workbooks and never edit the source files in `muban/leimu`.
7. Verify that only the copied category template `.xlsx` files are delivered from `类目模板输出`.

## Guardrails

- Before a batch image run, state that it contains exactly nine image jobs. Execute them in the active task after the user authorizes generation; do not merely describe the steps.
- Never claim health, therapeutic, hair-loss, medical, or light-treatment outcomes without approved compliance copy. Use neutral feature wording for personal-care devices.
- Never push if the repository/path is unclear or credentials are unavailable.
- Preserve source images and generation prompts in the product output folder for audit and reruns.
