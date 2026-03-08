# Auto-Discovery and Deduplication Guide

## Feature Overview

The OpenWebUI Skills Manager Tool now automatically discovers and installs all skills from GitHub repositories, with built-in duplicate handling.

## Features Added

### 1. **Automatic Repo Root Detection** 🎯

When you provide a GitHub repository root URL (without `/tree/`), the system automatically converts it to discovery mode.

#### Examples

```
Input:  https://github.com/nicobailon/visual-explainer
        ↓
Auto-converted to: https://github.com/nicobailon/visual-explainer/tree/main
        ↓
Discovers all skill subdirectories
```

### 2. **Automatic Skill Discovery** 🔍

Once a tree URL is detected, the tool automatically:

- Queries the GitHub API to list all subdirectories
- Creates skill installation URLs for each subdirectory
- Attempts to fetch `SKILL.md` or `README.md` from each subdirectory
- Installs all discovered skills in batch mode

#### Supported URL Formats

```
✓ https://github.com/owner/repo                    → Auto-detected as repo root
✓ https://github.com/owner/repo/                   → With trailing slash
✓ https://github.com/owner/repo/tree/main          → Existing tree format
✓ https://github.com/owner/repo/tree/main/skills   → Nested skill directory
```

### 3. **Duplicate URL Removal** 🔄

When installing multiple skills, the system automatically:

- Detects duplicate URLs
- Removes duplicates while preserving order
- Notifies user how many duplicates were removed
- Skips processing duplicate URLs

#### Example

```
Input URLs (5 total):
- https://github.com/user/repo/tree/main/skill1
- https://github.com/user/repo/tree/main/skill1   ← Duplicate
- https://github.com/user/repo/tree/main/skill2
- https://github.com/user/repo/tree/main/skill2   ← Duplicate
- https://github.com/user/repo/tree/main/skill3

Processing:
- Unique URLs: 3
- Duplicates Removed: 2
- Status: "Removed 2 duplicate URL(s) from batch"
```

### 4. **Duplicate Skill Name Detection** ⚠️

If multiple URLs result in the same skill name during batch installation:

- System detects the duplicate installation
- Logs warning with details
- Notifies user of the conflict
- Shows which action was taken (installed/updated)

#### Example Scenario

```
Skill A: skill1.zip → creates skill "report-generator"
Skill B: skill2.zip → creates skill "report-generator"  ← Same name!

Warning: "Duplicate skill name 'report-generator' - installed multiple times"
Note: The latest install may have overwritten the earlier one
      (depending on ALLOW_OVERWRITE_ON_CREATE setting)
```

## Usage Examples

### Example 1: Simple Repo Root

```
User Input:
"Install skills from https://github.com/nicobailon/visual-explainer"

System Response:
"Detected GitHub repo root: https://github.com/nicobailon/visual-explainer. 
 Auto-converting to discovery mode..."

"Discovering skills in https://github.com/nicobailon/visual-explainer/tree/main..."

"Installing 5 skill(s)..."
```

### Example 2: With Nested Skills Directory

```
User Input:
"Install all skills from https://github.com/anthropics/skills"

System Response:
"Detected GitHub repo root: https://github.com/anthropics/skills. 
 Auto-converting to discovery mode..."

"Discovering skills in https://github.com/anthropics/skills/tree/main..."

"Installing 12 skill(s)..."
```

### Example 3: Duplicate Handling

```
User Input (batch):
[
  "https://github.com/user/repo/tree/main/skill-a",
  "https://github.com/user/repo/tree/main/skill-a",  ← Duplicate
  "https://github.com/user/repo/tree/main/skill-b"
]

System Response:
"Removed 1 duplicate URL(s) from batch."

"Installing 2 skill(s)..."

Result:
- Batch install completed: 2 succeeded, 0 failed
```

## Implementation Details

### Detection Logic

**Repo root detection** uses regex pattern:

```python
^https://github\.com/([^/]+)/([^/]+)/?$
# Matches:
#   https://github.com/owner/repo     ✓
#   https://github.com/owner/repo/    ✓
# Does NOT match:
#   https://github.com/owner/repo/tree/main          ✗
#   https://github.com/owner/repo/blob/main/file.md  ✗
```

### Normalization

Detected repo root URLs are converted with:

```python
https://github.com/{owner}/{repo} → https://github.com/{owner}/{repo}/tree/main
```

The `main` branch is attempted first; the GitHub API handles fallback to `master` if needed.

### Discovery Process

1. Parse tree URL with regex to extract owner, repo, branch, and path
2. Query GitHub API: `/repos/{owner}/{repo}/contents{path}?ref={branch}`
3. Filter for directories (skip hidden directories starting with `.`)
4. For each subdirectory, create a tree URL pointing to it
5. Return list of discovered tree URLs for batch installation

### Deduplication Strategy

```python
seen_urls = set()
unique_urls = []
duplicates_removed = 0

for url in input_urls:
    if url not in seen_urls:
        unique_urls.append(url)
        seen_urls.add(url)
    else:
        duplicates_removed += 1
```

- Preserves URL order
- O(n) time complexity
- Low memory overhead

### Duplicate Name Tracking

During batch installation:

```python
installed_names = {}  # {lowercase_name: url}

for skill in results:
    if success:
        name_lower = skill["name"].lower()
        if name_lower in installed_names:
            # Duplicate detected
            warn_user(name_lower, installed_names[name_lower])
        else:
            installed_names[name_lower] = current_url
```

## Configuration

No new Valve parameters are required. Existing settings continue to work:

| Parameter | Impact |
|-----------|--------|
| `ALLOW_OVERWRITE_ON_CREATE` | Controls whether duplicate skill names result in updates or errors |
| `TRUSTED_DOMAINS` | Still enforced for all discovered URLs |
| `INSTALL_FETCH_TIMEOUT` | Applies to each GitHub API discovery call |
| `SHOW_STATUS` | Shows all discovery and deduplication messages |

## API Changes

### install_skill() Method

**New Behavior:**

- Automatically converts repo root URLs to tree format
- Auto-discovers all skill subdirectories for tree URLs
- Deduplicates URL list before batch processing
- Tracks duplicate skill names during installation

**Parameters:** (unchanged)

- `url`: Can now be repo root (e.g., `https://github.com/owner/repo`)
- `name`: Ignored in batch/auto-discovery mode
- `overwrite`: Controls behavior on skill name conflicts
- Other parameters remain the same

**Return Value:** (unchanged)

- Single skill: Returns installation metadata
- Batch install: Returns batch summary with success/failure counts

## Error Handling

### Discovery Failures

- If repo root normalization fails → treated as normal URL
- If tree discovery API fails → logs warning, continues single-file install attempt
- If no SKILL.md or README.md found → specific error for that URL

### Batch Failures

- Duplicate URL removal → notifies user but continues
- Individual skill failures → logs error, continues with next skill
- Final summary shows succeeded/failed counts

## Telemetry & Logging

All operations emit status updates:

- ✓ "Detected GitHub repo root: ..."
- ✓ "Removed {count} duplicate URL(s) from batch"
- ⚠️ "Warning: Duplicate skill name '{name}'"
- ✗ "Installation failed for {url}: {reason}"

Check OpenWebUI logs for detailed error traces.

## Testing

Run the included test suite:

```bash
python3 docs/test_auto_discovery.py
```

Tests coverage:

- ✓ Repo root URL detection (6 cases)
- ✓ URL normalization for discovery (4 cases)
- ✓ Duplicate removal logic (3 scenarios)
- ✓ Total: 13/13 test cases passing

## Backward Compatibility

✅ **Fully backward compatible.**

- Existing tree URLs work as before
- Existing blob/raw URLs function unchanged
- Existing batch installations unaffected
- New features are automatic (no user action required)
- No breaking changes to API

## Future Enhancements

Possible future improvements:

1. Support for GitLab, Gitea, and other Git platforms
2. Smart branch detection (master → main fallback)
3. Skill filtering by name pattern during auto-discovery
4. Batch installation with conflict resolution strategies
5. Caching of discovery results to reduce API calls
