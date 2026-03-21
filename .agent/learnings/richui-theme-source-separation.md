# RichUI Theme Source Separation

> Discovered: 2026-03-20

## Context
Applies to the RichUI bridge in `plugins/pipes/github-copilot-sdk/github_copilot_sdk.py` when syncing iframe or standalone HTML theme with OpenWebUI.

## Finding
Theme detection must not read back bridge-applied local theme markers as if they were the upstream source of truth.

If the bridge writes `html[data-theme]` or `html.dark` in standalone/current-document mode and then also reads those same markers during detection, the theme can self-latch and stop following real source changes such as `meta[name="theme-color"]` updates or `prefers-color-scheme` changes.

## Solution / Pattern
Keep theme **detection** and theme **application** separate.

When embedded in OpenWebUI, follow the same stable detection order used by `smart-mind-map`:

1. `parent document` `meta[name="theme-color"]`
2. `parent document` `html/body` class or `html[data-theme]`
3. `prefers-color-scheme`

Only if there is no accessible parent document should the bridge fall back to the current document's `meta[name="theme-color"]` and `html/body` theme signals.

- Always write the resolved theme to a dedicated bridge marker such as `data-openwebui-applied-theme`.
- Only mirror generic `html[data-theme]` / `html.dark` markers when a real parent document exists, so standalone fallback does not pollute its own detection source.
- If internal widget CSS needs dark-mode styling in standalone mode, target the dedicated marker too (for example `html[data-openwebui-applied-theme="dark"]`).

## Gotchas
- Watching `style` mutations is unnecessary once detection no longer reads computed style or inline color-scheme.
- If standalone mode needs to honor page-owned `html.dark` or `html[data-theme]`, do not overwrite those markers just to style the bridge itself; use the dedicated bridge marker instead.
