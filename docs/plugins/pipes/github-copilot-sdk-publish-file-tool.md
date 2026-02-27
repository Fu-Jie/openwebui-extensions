# GitHub Copilot SDK Pipe - `publish_file_from_workspace` Tool Guide

## Summary

`publish_file_from_workspace` is the file delivery tool used by the GitHub Copilot SDK Pipe to publish workspace-generated files into OpenWebUI storage and return stable preview/download links.

## Input

- `filename` (required): Relative file path under current workspace.

## Delivery Modes

- `artifacts` (default): Return `[Preview]` + `[Download]`, with optional `html_embed` rendering in HTML block.
- `richui`: Return `[Preview]` + `[Download]`; integrated preview is rendered by Rich UI emitter.

## PDF Rule

For PDF outputs, always return markdown links only (`[Preview]`, `[Download]` when available). Do not embed PDF using iframe or HTML.

## Recommended Steps

1. Generate file in workspace.
2. Publish via `publish_file_from_workspace(filename=...)`.
3. Return links according to embed mode.
4. Apply PDF link-only rule for `.pdf` files.

## Reference

- Plugin local guide: `plugins/pipes/github-copilot-sdk/PUBLISH_FILE_FROM_WORKSPACE.md`
