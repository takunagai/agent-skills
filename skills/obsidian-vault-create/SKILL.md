---
name: obsidian-vault-create
description: Create new Obsidian vaults under ~/Documents using YYYY-MM-DD-Project naming, a minimal default folder layout, and optional default settings copied from a baseline vault. Use when a user asks to initialize a new Obsidian vault, set up initial folders/templates, or clone standard Obsidian settings.
---

# Obsidian Vault Create

## Overview

Create a new Obsidian vault folder on disk with a standard layout, README/Home notes, and optional settings copy. Use `scripts/create_vault.py` for repeatable creation, then hand off to Obsidian to open the vault.

## Workflow

### 1. Collect Inputs

- Ask for a project name (required).
- Ask for a date if the user wants to override today (default to today).
- Ask whether to skip the Daily folder and daily template.
- Ask whether to copy default settings from an existing vault or `.obsidian` directory.

### 2. Decide Settings Strategy

- Prefer copying `.obsidian` from a vanilla vault created with the user's current Obsidian version when "orthodox/default settings" are requested.
- If no baseline exists, skip `.obsidian` and let Obsidian generate defaults on first open.
- Do not add community plugins unless explicitly requested. Keep to core plugins only.

### 3. Create the Vault (Script)

Default layout (ordered with numeric prefixes for consistent sorting):

- `00-Inbox`
- `01-Notes`
- `02-Projects`
- `03-Resources`
- `04-Templates`
- `05-Assets`
- `06-Daily`
- `99-Archive`

Create a vault using the script:

```bash
python3 scripts/create_vault.py \
  --project "Project Name" \
  --date 2026-02-03 \
  --base-dir ~/Documents \
  --config-source "/path/to/vanilla-vault-or-.obsidian"
```

Notes:

- `--date` is optional; the script defaults to today.
- `--config-source` can be either a vault root containing `.obsidian` or a direct `.obsidian` path.
- Use `--dry-run` to preview actions.
- Use `--skip-daily` if you do not want the Daily folder or Daily template.
- The script creates `README.md` (required) and `Home.md` (landing note) by default.

### 4. Post-Checks

- Confirm the vault folder exists at `~/Documents/YYYY-MM-DD-Project`.
- Avoid nesting the vault inside another vault.
- If settings were copied, confirm `.obsidian` exists under the new vault.
- Verify `README.md` and `Home.md` exist at the vault root.

## Core Plugins (Optional)

If the user wants Daily Notes templating, remind them to enable the core plugins "Daily notes" and "Templates", then:

- Set template folder location to `04-Templates`.
- Set Daily notes folder to `06-Daily` (only if you created it).

## Resources

### scripts/

- `scripts/create_vault.py`: Create the vault with the standard layout and optional settings copy.

### references/

- `references/obsidian-basics.md`: Official-docs summary for vault storage, settings, and core plugins.
