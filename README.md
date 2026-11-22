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

## macOS desktop version

The same GUI now has a macOS launcher. It is a Python/Tkinter application, **not yet a packaged standalone .app**.

**One-time setup on a Mac:**

1. Install Python 3 for macOS (with Tkinter) and Google Chrome.
2. Clone this repository to the Mac (or pull the latest updates).
3. In Finder, open `Setup Pinterest Automation Mac.command`. This creates a Mac-specific `.venv` and installs `requirements.txt`.
4. Copy your own `.env` configuration into the project root; never commit credentials.
5. Double-click `Pinterest Automation Mac.command` to launch the GUI.
6. Click **Pinterest Login** inside the GUI to sign in on the Mac, then test with **Dry run** enabled.

If Finder refuses to open a `.command` file due to permissions, run the following once from Terminal in the project directory:

```bash
chmod +x "Setup Pinterest Automation Mac.command" "Pinterest Automation Mac.command"
```

Or launch directly:

```bash
./.venv/bin/python gui_app.py
```

**Important:** The Mac needs its own virtual environment and its own browser login profile. Do not copy the Windows `.venv` or assume the Windows Pinterest browser profile is portable. The actual Pinterest browser automation has been developed/tested on Windows; macOS needs a dry-run validation before live posting. The GUI still uses the same content generation, categorization, Pin-count, affiliate, and publishing scripts.

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

# Desktop GUI

You can run the automation as a normal Windows app instead of typing commands.

After pulling the latest code, double-click:

```text
Pinterest Automation App.bat
```

The GUI includes:

- Affiliate Pins tab
- Non-Affiliate / AI Content tab
- 3D-printing or Honda vertical selection
- Specific category selection
- Affiliate Pin count control
- Non-affiliate Pin count control
- Per-Pin Tip / Quote / Question / Quiz / Random selectors
- AI/static content selection
- Dry-run checkbox
- Live output console
- Pinterest login button
- Stop Current Run button
- Continue / Close Dry-Run Browser button
- Open Output Folder button
- Open README button

The GUI runs the same tested Python scripts underneath, so the command-line workflow still works exactly as before.

For safety, the GUI starts with **Dry run enabled** each time you open it.

During a dry run, inspect the Pinterest browser and then click:

```text
Continue / Close Dry-Run Browser
```

That replaces pressing Enter in the PowerShell terminal.

You can also launch the GUI manually:

```powershell
.\.venv\Scripts\python.exe gui_app.py
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


## Post multiple Pins from one vertical

Use `--count` (or `--pins`) to choose how many fresh affiliate Pins to publish in one run.

Three 3D-printing Pins:

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --vertical 3d --count 3
```

Three Honda Pins:

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --vertical honda --count 3
```

The selector keeps the batch diverse by taking strong products from different search categories first when possible. Each confirmed Pin is saved to posted history immediately.

You can also use the alias:

```powershell
.\.venv\Scripts\python.exe run_best_pin.py --vertical 3d --pins 3
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

# Non-affiliate image design variation

Non-affiliate cards now rotate through **four visual layouts** per content type, with independently chosen color palettes. This includes editorial cards, bold hero designs, split-section posters, and floating-card layouts.

The rendering engine adjusts font sizes to help longer generated content fit inside the image. Visual selection is deterministic based on each content ID, and the existing 1000 x 1500 pixel output is preserved.

The same variation is available for AI-generated content and static/prewritten content. Affiliate product images are unchanged.

---

# Non-affiliate Pinterest content

The non-affiliate poster supports:

- `tip`
- `quote`
- `question`
- `quiz`
- `random` for individual batch slots
- `all` as the general CLI mode

The GUI can create a multi-Pin non-affiliate batch where every Pin has its own type selector.

Example GUI plan:

```text
Number of Pins: 3

Pin 1: Quiz
Pin 2: Question
Pin 3: Random
```

The program prefers different matching categories inside the same batch when possible and prevents the exact same card from being reused in that run. AI-generated cards from earlier in the current batch are also included in duplicate checking even during dry runs.

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


## Post multiple non-affiliate Pins

Use `--count` and repeat `--pin-type` once for each Pin.

Example: Quiz, Question, Random:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --vertical 3d --count 3 --pin-type quiz --pin-type question --pin-type random
```

Example: three randomly selected content types:

```powershell
.\.venv\Scripts\python.exe run_tip_pin.py --vertical honda --count 3 --pin-type random --pin-type random --pin-type random
```

If you omit `--pin-type`, the existing `--content-type` value is used for every requested Pin. If `--content-type all` is used, each slot behaves as Random.

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
gui_app.py               Windows desktop GUI
Pinterest Automation App.bat  Double-click GUI launcher
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

# Three 3D affiliate Pins in one run
.\.venv\Scripts\python.exe run_best_pin.py --vertical 3d --count 3

# List non-affiliate categories
.\.venv\Scripts\python.exe run_tip_pin.py --list-categories

# Honda AI tip
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical honda

# 3D AI tip
.\.venv\Scripts\python.exe run_tip_pin.py --content-type tip --vertical 3d


# Three non-affiliate Pins: quiz, question, random
.\.venv\Scripts\python.exe run_tip_pin.py --vertical 3d --count 3 --pin-type quiz --pin-type question --pin-type random

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
