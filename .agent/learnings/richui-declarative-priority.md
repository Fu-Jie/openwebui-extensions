# RichUI Declarative Priority

> Discovered: 2026-03-16

## Context
This applies to the RichUI bridge embedded by `plugins/pipes/github-copilot-sdk/github_copilot_sdk.py` when HTML pages mix declarative `data-openwebui-prompt` / `data-prompt` actions with inline `onclick` handlers.

## Finding
Mixing declarative prompt/link attributes with inline click handlers can cause duplicate prompt submission paths, especially when both the page and the bridge react to the same click.

## Solution / Pattern
The bridge now treats inline `onclick` as the default owner of click behavior. Declarative prompt/link dispatch is skipped when an element already has inline click logic.

If a page intentionally wants declarative bridge handling even with inline handlers present, mark the element explicitly:

```html
<button
  onclick="trackClick()"
  data-openwebui-prompt="Explain this chart"
  data-openwebui-force-declarative="1"
>
```

## Gotchas
Without the explicit override, keyboard/click dispatch for declarative actions will yield to inline `onclick`.

The bridge also keeps a short same-prompt dedupe window in `sendPrompt()` as a safety net, but the preferred fix is still to avoid mixed ownership unless you opt in deliberately.
