# Flash Card

Generate polished learning flashcards from any text—title, summary, key points, tags, and category—ready for review and sharing.

![Flash Card Example](flash_card.png)

## Highlights

- **One-click generation**: Drop in text, get a structured card.
- **Concise extraction**: 3–5 key points and 2–4 tags automatically surfaced.
- **Multi-language**: Choose target language (default English).
- **Progressive merge**: Multiple runs append cards into the same HTML container; enable clearing to reset.
- **Status updates**: Live notifications for generating/done/error.

## Parameters

| Param               | Description                                                  | Default |
| ------------------- | ------------------------------------------------------------ | ------- |
| MODEL_ID            | Model to use; empty falls back to current session model      | empty   |
| MIN_TEXT_LENGTH     | Minimum text length; below this prompts for more text        | 50      |
| LANGUAGE            | Output language (e.g., en, zh)                               | en      |
| SHOW_STATUS         | Whether to show status updates                               | true    |
| CLEAR_PREVIOUS_HTML | Whether to clear previous card HTML (otherwise append/merge) | false   |
| MESSAGE_COUNT       | Use the latest N messages to build the card                  | 1       |

## How to Use

1. Install and enable “Flash Card”.
2. Send the text to the chat (multi-turn supported; governed by MESSAGE_COUNT).
3. Watch status updates; the card HTML is embedded into the latest message.
4. To regenerate from scratch, toggle CLEAR_PREVIOUS_HTML or resend text.

## Output Format

- JSON fields: `title`, `summary`, `key_points` (3–5), `tags` (2–4), `category`.
- UI: gradient-styled card with tags, key-point list; supports stacking multiple cards.

## Tips

- Very short text triggers a prompt to add more; consider summarizing first.
- Long text is accepted; for deep analysis, pre-condense with other tools before card creation.

## Author

Fu-Jie
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## License

MIT License

## Changelog

### v0.2.4

- Removed debug messages from output
