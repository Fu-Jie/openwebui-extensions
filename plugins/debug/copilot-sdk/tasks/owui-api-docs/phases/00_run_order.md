# OpenWebUI API Documentation — Phase Run Order

## Overview

This task set reads the OpenWebUI backend source code and generates a complete
API reference in `api_docs/` inside the open-webui repository.

**Source repo:** `/Users/fujie/app/python/oui/open-webui`  
**Output directory:** `/Users/fujie/app/python/oui/open-webui/api_docs/`  
**Task files dir:** `plugins/debug/copilot-sdk/tasks/owui-api-docs/phases/`

---

## Phase Execution Order

Run phases sequentially. Each phase depends on the previous.

| Order | Task File | Coverage | ~Lines Read |
|-------|-----------|----------|-------------|
| 1 | `01_route_index.txt` | main.py + all 26 router files → master route table | ~15,000 |
| 2 | `02_auth_users_groups_models.txt` | auths, users, groups, models | ~4,600 |
| 3 | `03_chats_channels_memories_notes.txt` | chats, channels, memories, notes | ~5,500 |
| 4 | `04_files_folders_knowledge_retrieval.txt` | files, folders, knowledge, retrieval | ~5,200 |
| 5 | `05_ollama_openai_audio_images.txt` | ollama, openai, audio, images | ~6,900 |
| 6 | `06_tools_functions_pipelines_skills_tasks.txt` | tools, functions, pipelines, skills, tasks | ~3,200 |
| 7 | `07_configs_prompts_evaluations_analytics_scim_utils.txt` | configs, prompts, evaluations, analytics, scim, utils | ~3,400 |
| 8 | `08_consolidation_index.txt` | Consolidates all outputs → README.md + JSON | (reads generated files) |

---

## Output Files (after all phases complete)

```
open-webui/api_docs/
├── README.md               ← Master index + quick reference
├── 00_route_index.md       ← Complete route table (200+ endpoints)
├── 02_auths.md
├── 02_users.md
├── 02_groups.md
├── 02_models.md
├── 03_chats.md
├── 03_channels.md
├── 03_memories.md
├── 03_notes.md
├── 04_files.md
├── 04_folders.md
├── 04_knowledge.md
├── 04_retrieval.md
├── 05_ollama.md
├── 05_openai.md
├── 05_audio.md
├── 05_images.md
├── 06_tools.md
├── 06_functions.md
├── 06_pipelines.md
├── 06_skills.md
├── 06_tasks.md
├── 07_configs.md
├── 07_prompts.md
├── 07_evaluations.md
├── 07_analytics.md
├── 07_scim.md
├── 07_utils.md
└── openwebui_api.json      ← Machine-readable summary (all routes)
```

---

## Notes

- Each phase uses `--no-plan-first` (detailed instructions already provided).
- Working directory for all phases: `/Users/fujie/app/python/oui/open-webui`
- The one-click runner: `run_owui_api_docs_phases.sh`
- If a phase fails, fix the issue and re-run that single phase before continuing.
