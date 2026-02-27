# 📤 `publish_file_from_workspace` Tool Guide

This document explains the recommended usage contract of the built-in `publish_file_from_workspace` tool in the GitHub Copilot SDK Pipe.

## Tool Purpose

Use this tool when the agent has generated a file in the current workspace and needs to:

- Save the file into OpenWebUI file storage.
- Return stable links for preview and download.
- Keep rendering behavior consistent across local disk and object storage backends.

## Required Input

- `filename`: Relative filename under current workspace.
  - ✅ Example: `report.xlsx`
  - ✅ Example: `output/summary.html`
  - ❌ Avoid temporary paths outside workspace (e.g. `/tmp/...`).

## Output Contract

The tool typically returns structured fields used by the pipe to build user-facing links:

- `filename`
- `download_url`
- `preview_url` (if preview is available)
- metadata used by renderer (including optional `html_embed` for HTML previews)

## Embed Modes

### 1) `artifacts` (default)

- Message should include `[Preview]` + `[Download]` links.
- For HTML-capable content, `html_embed` may be rendered in a ```html block.
- Best for inline interactive previews in chat.

### 2) `richui`

- Message should include `[Preview]` + `[Download]` links.
- Integrated preview is emitted by Rich UI renderer automatically.
- Do not output iframe/html preview block in chat body.

## PDF Safety Rule (Mandatory)

For PDF files, always output markdown links only:

- `[Preview](...)`
- `[Download](...)` (if available)

Do NOT embed PDFs with iframe or raw HTML blocks.

## Recommended Workflow

1. Generate file in workspace.
2. Call `publish_file_from_workspace(filename=...)`.
3. Return links according to selected embed mode.
4. Follow PDF safety rule for any `.pdf` output.

## Practical Example

### Example A: HTML report (artifacts)

- Publish `analysis.html`.
- Return links.
- Allow `html_embed` block rendering for direct preview.

### Example B: PDF report

- Publish `audit.pdf`.
- Return links only.
- Skip iframe/html embedding entirely.

## Related Docs

- [Skills Manager Guide](./SKILLS_MANAGER.md)
- [Skills Best Practices](./SKILLS_BEST_PRACTICES.md)
