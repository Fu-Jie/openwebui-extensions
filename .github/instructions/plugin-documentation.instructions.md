---
name: Plugin Documentation
description: Use when writing or updating plugin README files, mirrored docs pages, bilingual release notes, or other user-facing documentation for plugins.
applyTo: "plugins/**/README*.md"
---
# Plugin Documentation Standards

## Delivery Language

- Plugin directories must keep both `README.md` and `README_CN.md`
- When a task includes docs, guides, announcements, release notes, or development docs, prepare both English and Chinese versions for review unless the user explicitly asks for single-language delivery
- Even if only English is committed, provide a Chinese review draft in the conversation when documentation is part of the work

## README Structure

Use this order for plugin READMEs:

1. Title with icon
2. README header
3. One-sentence description
4. `What's New` with only the latest update
5. `Key Features`
6. `How to Use`
7. Configuration or Valves table
8. Support section
9. Other sections such as examples, template notes, troubleshooting, or changelog link

## README Header

Do not use the old pipe-separated metadata line.

Use a compact two-part header:

1. A full-width two-column line with author/version on the left and the star link on the right
2. A single-row live badge table with no visible text header

English example:

`| By [Fu-Jie](https://github.com/Fu-Jie) · vx.y.z | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |`

`| :--- | ---: |`

`| ![followers](...) | ![points](...) | ![top](...) | ![contributions](...) | ![downloads](...) | ![saves](...) | ![views](...) |`

`| :---: | :---: | :---: | :---: | :---: | :---: | :---: |`

Chinese example:

`| 作者：[Fu-Jie](https://github.com/Fu-Jie) · vx.y.z | [⭐ 点个 Star 支持项目](https://github.com/Fu-Jie/openwebui-extensions) |`

`| :--- | ---: |`

`| ![followers](...) | ![points](...) | ![top](...) | ![contributions](...) | ![downloads](...) | ![saves](...) | ![views](...) |`

`| :---: | :---: | :---: | :---: | :---: | :---: | :---: |`

Guidelines:

- Keep the author link pointing to `https://github.com/Fu-Jie`
- Keep the star link pointing to the repository root
- Put the version on the left-side author line as plain text (`vx.y.z`), not as a badge
- Use live badges for followers, points, plugin contribution count, total plugin downloads, total plugin saves, and total plugin views
- Keep the `Top` badge compact and use the project standard wording (`Top <1%`)
- Do not add a visible label header row above the badges

## Support Section

Use the repository-standard support wording.

English:
`If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.`

Chinese:
`如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。`

## Mirror and Sync Rules

When plugin documentation changes, keep these layers aligned as needed:

- Plugin-local README files under `plugins/`
- Mirrored docs pages under `docs/plugins/`
- Plugin index pages under `docs/plugins/<type>/index.md` and `index.zh.md`
- Root `README.md` and `README_CN.md` date badge when preparing a release

Use the `doc-mirror-sync` skill when the task includes mirroring plugin READMEs into `docs/`.

## Changelog Handling

- Keep detailed changelog history in GitHub release history or dedicated docs
- In README files, keep `What's New` focused on the latest version only
