---
name: tk-up
description: Process local TikTok Shop product folders with TK-UP MCP tools. Use when a user asks to prepare product materials, generate nine localized listing images with Codex image generation, check image readiness, or create a TikTok upload workbook in the corresponding category template.
---

# TK-UP workflow

1. Call `tk_up_prepare` with product folder and workspace root.
2. Use Codex's built-in `image_gen` exactly nine times. Save nine local 800×800 PNG paths.
3. Call `tk_up_status`.
4. Call `tk_up_finalize` with the job ID, nine paths, category, and listing fields.

Never create a generic workbook or combine categories. If image generation is unavailable, stop: `tk_up_finalize` rejects fewer than nine images or any non-800×800 PNG and creates no TikTok template.
