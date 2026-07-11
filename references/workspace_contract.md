# Required workspace inputs

- `填写要求.txt`: product-image and listing rules, plus the target GitHub image repository configuration.
- Inventory CSV: SKU, title, available stock, and average cost. Pass its path to `prepare_product.py`.
- One folder per product: a `.txt` file with its title and image URLs.

The skill creates `processed_<SKU>`, `input.excel`, `category_map.json`, `template_rows.json`, and `类目模板输出` in the workspace.
