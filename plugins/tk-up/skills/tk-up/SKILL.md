---
name: tk-up
description: Process local TikTok Shop product folders with TK-UP MCP tools. Use when a user asks to prepare product materials, generate nine localized listing images with Codex image generation, check image readiness, or create a TikTok upload workbook in the corresponding category template.
---

# TK-UP workflow

Read `<workspace-root>/填写要求.txt` as UTF-8 before doing anything. The following rules are non-negotiable and override generic ecommerce-image habits.

1. Call `tk_up_prepare` with product folder and workspace root. Inspect every supplied image and select the clearest white-background photo as the structural reference.
2. Build exactly nine final 800×800 PNGs. Do **not** generate a trial image, do **not** stop after one image, and do **not** ask whether to continue. For source images without text, retain the image and make it 800×800; for source images with text, use `image_gen` to replace text with natural pt-BR. Generate only the missing image slots from real product-use scenarios.
3. Generate image 1 (main image) from the white-background reference using this fixed layout: product on the right at 60–65% of the frame; four vertical feature panels on the left; a bottom 18–22% text area with bold main title and subtitle. All visible text is correct, complete Brazilian Portuguese only—never Chinese, English, garbled text, watermark, or tiny text. Use a commercial ecommerce photograph style with natural light and high contrast.
4. Derive the four feature panels, top tag, main title, subtitle, and product description from the product name and actual visible features. Do not invent specifications, accessories, medical/therapeutic claims, or change supplied Portuguese copy.
5. Preserve the exact product structure, color, material, number of parts, and appearance in every image. Never add/remove products or parts, deform it, duplicate zippers/pockets/handles/buttons/accessories, or show unnatural hands/fingers.
6. Call `tk_up_status`, then `tk_up_finalize` with the job ID, all nine paths, exact category, and listing fields.

Never create a generic workbook or combine categories. `tk_up_finalize` rejects fewer than nine images or any non-800×800 PNG and creates no TikTok template. Write only the copied matched category template; image columns must use the GitHub raw URLs at `https://raw.githubusercontent.com/video-text/photo/main/products/<SKU>/`.
