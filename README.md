# Automated Pinterest Poster

Automates Pinterest posting for two content streams:

1. **eBay affiliate product Pins**
2. **Non-affiliate Pinterest content** such as tips, quotes, questions, and quizzes

Current supported verticals:

- `3d` — 3D printing
- `honda` — Vintage Honda motorcycles

Current Pinterest boards:

- `3D Printer Parts, Filament & Supplies`
- `Vintage Honda Motorcycles`

---

## Quick start

From PowerShell, first make sure you are inside the project folder.

Example:

```powershell
cd "C:\Users\benne\OneDrive\Documents\Automation Programs\ebay_pinterest_combined_agent\ebay_pinterest_combined_agent"
```

Pull the latest code from GitHub:

```powershell
git pull origin master
```

Install or refresh dependencies if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

# Environment setup

The local `.env` file contains secrets and runtime settings.

Example:

```env
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
EBAY_REFRESH_TOKEN=...
EBAY_EPN_CAMPAIGN_ID=...
EBAY_MARKETPLACE_ID=EBAY_US

OPENAI_API_KEY=...
OPENAI_CONTENT_MODEL=gpt-6-luna

PINTEREST_BOARD_NAME=...
PINTEREST_PROFILE_DIR=data/pinterest_profile
PINTEREST_HEADLESS=false
PINTEREST_DRY_RUN=true
PINTEREST_TIMEOUT_MS=30000
PINTEREST_CREATE_PIN_URL=https://www.pinterest.com/pin-creation-tool/

OUTPUT_DIR=output
```

Do not commit `.env` to GitHub.

---

# Pinterest login

Normally you only need to do this once because the project uses a persistent Chrome profile.

```powershell
.\.venv\Scripts\python.exe pinterest_login.py
```

Log in to Pinterest in the Chrome window, then return to PowerShell and press Enter.

---

# Dry run vs live posting

For safe testing:

```env
PINTEREST_DRY_RUN=true
```

This fills out the Pinterest form but does not click Publish.

For live posting:

```env
PINTEREST_DRY_RUN=false
```

Always use a dry run first after changing Pinterest automation code.

---

# eBay affiliate Pins

## List affiliate categories

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --list-categories
```

## Post one 3D-printing affiliate Pin

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --vertical 3d
```

## Post one Honda affiliate Pin

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --vertical honda
```

## Post from a specific affiliate category

Example:

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --category "Honda CB750 OEM Parts"
```

Another example:

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --category "3D Printing PLA Filament"
```

## Post one winner from multiple affiliate categories

Repeat `--category`:

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --category "3D Printing PLA Filament" --category "3D Printing PETG Filament"
```

The multi-category mode selects one fresh winner from each matched category.

---

# Non-affiliate Pinterest content

The non-affiliate poster supports:

- `tip`
- `quote`
- `question`
- `quiz`
- `all`

When `OPENAI_API_KEY` is configured, the program generates fresh content with AI first.

If AI generation fails or no API key is configured, the program falls back to the prewritten `tip_config.yaml` library.

---

## List non-affiliate categories

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --list-categories
```

## Post any available non-affiliate content

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py
```

## Post any Honda non-affiliate content

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --vertical honda
```

## Post any 3D-printing non-affiliate content

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --vertical 3d
```

---

# AI-generated tips

## Honda tip

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical honda
```

## 3D-printing tip

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical 3d
```

---

# AI-generated quotes / humor

## Honda humor

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quote --vertical honda
```

## 3D-printing humor

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quote --vertical 3d
```

---

# AI-generated community questions

## Honda question

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type question --vertical honda
```

## 3D-printing question

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type question --vertical 3d
```

---

# AI-generated quizzes

## Honda quiz

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quiz --vertical honda
```

## 3D-printing quiz

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quiz --vertical 3d
```

---

# Force the old static/prewritten content system

Add `--static` to a non-affiliate command.

Example:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical honda --static
```

Example:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type question --vertical 3d --static
```

This bypasses AI generation and uses `tip_config.yaml`.

---

# Post from a specific non-affiliate category

Use `--category`:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --category "Vintage Honda Motorcycle Tips"
```

Another example:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --category "3D Printing PLA Tips"
```

You can combine `--category` with `--content-type`, `--vertical`, or `--static`.

---

# Multiple non-affiliate categories in one run

Repeat `--category`:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --category "3D Printing PLA Tips" --category "3D Printing PETG Tips"
```

Explicit multiple-category filters intentionally process one Pin from each matched category.

---

# Content cooldown

Non-affiliate repeat cooldown is configured in `tip_config.yaml`:

```yaml
tip_settings:
  history_db_path: "data/tip_history.db"
  cooldown_days: 60
  output_dir: "output/tip_images"
```

Examples:

```yaml
cooldown_days: 30
```

or:

```yaml
cooldown_days: 90
```

Recent content inside the cooldown window is excluded from reuse and is supplied to the AI as content to avoid duplicating.

Older content becomes eligible again after the cooldown window.

---

# Affiliate listing cooldown

Affiliate product cooldown is configured in `config.yaml`.

Current behavior uses the posted-history database:

```text
data/posted_history.db
```

Recently posted eBay items are excluded for the configured cooldown period.

---

# Non-affiliate history

Generated and static non-affiliate posts are stored in:

```text
data/tip_history.db
```

After a confirmed publish, the program stores the generated content so future AI generations can avoid recently used ideas.

Dry runs are not added to posting history.

---

# Affiliate history

Affiliate Pins are stored in:

```text
data/posted_history.db
```

An item is added only after Pinterest confirms the publish.

---

# AI behavior

Normally one generated Pin uses **one OpenAI API request**.

If the generated idea is too similar to recent content, the local duplicate checker rejects it and the generator tries again.

Current maximum:

```text
3 OpenAI generation attempts per Pin
```

The similarity check itself runs locally and does not make an API request.

---

# Useful Git commands

Pull the newest version:

```powershell
git pull origin master
```

Check local status:

```powershell
git status
```

See recent commits:

```powershell
git log --oneline -10
```

See your current branch:

```powershell
git branch
```

---

# Python / dependency commands

Check Python version:

```powershell
.\.venv\Scripts\python.exe --version
```

Install project requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

See installed packages:

```powershell
.\.venv\Scripts\python.exe -m pip list
```

---

# Useful test commands

## Safe Honda AI tip test

Set:

```env
PINTEREST_DRY_RUN=true
```

Then:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical honda
```

## Safe 3D AI question test

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type question --vertical 3d
```

## Safe Honda affiliate test

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --category "Honda CB750 OEM Parts"
```

## Test Pinterest login/profile

```powershell
.\.venv\Scripts\python.exe pinterest_login.py
```

---

# Typical daily workflow

Pull updates:

```powershell
git pull origin master
```

Post an affiliate product:

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --vertical 3d
```

Post an AI-generated tip:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical 3d
```

Post a community question:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type question --vertical honda
```

Post a quiz:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quiz --vertical honda
```

Post humor:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quote --vertical 3d
```

---

# Main files

```text
run_best_pin.py          Affiliate eBay -> Pinterest workflow
run_tip_pin.py           Non-affiliate / AI content workflow
ai_content_generator.py  AI generation + similarity checking
pinterest_browser.py     Pinterest browser automation
tip_builder.py           Non-affiliate image rendering
pin_builder.py           Affiliate Pin construction
tip_config.yaml          Non-affiliate categories + cooldown settings
config.yaml              Affiliate search/ranking configuration
tip_history.py           Non-affiliate posting history
history_db.py            Affiliate posting history
.env                     Local secrets/settings (never commit)
```

---

# Important safety checks

- Keep `PINTEREST_DRY_RUN=true` while testing changes.
- Never commit API keys or eBay credentials.
- Confirm the Pinterest board name is correct before live testing.
- The browser automation stops if the required board cannot be selected.
- Generated content is saved to history only after a confirmed Pinterest publish.
- Affiliate items are saved to history only after a confirmed Pinterest publish.

---

# Quick command cheat sheet

```powershell
# Pull latest code
git pull origin master

# Install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Pinterest login
.\.venv\Scripts\python.exe pinterest_login.py

# List affiliate categories
.\.venv\Scripts\python.exe run_best_pin.py --list-categories

# Honda affiliate Pin
.\.venv\Scripts\python.exe run_best_pin.py --vertical honda

# 3D affiliate Pin
.\.venv\Scripts\python.exe run_best_pin.py --vertical 3d

# List non-affiliate categories
.\.venv\Scripts\python.exe run_tip_pin.py --list-categories

# Honda AI tip
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical honda

# 3D AI tip
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical 3d

# Honda question
.\.venv\Scripts\python.exe run_tip_pin.py --content-type question --vertical honda

# 3D question
.\.venv\Scripts\python.exe run_tip_pin.py --content-type question --vertical 3d

# Honda quiz
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quiz --vertical honda

# 3D quiz
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quiz --vertical 3d

# Honda humor
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quote --vertical honda

# 3D humor
.\.venv\Scripts\python.exe run_tip_pin.py --content-type quote --vertical 3d

# Force static content
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical honda --static
```
