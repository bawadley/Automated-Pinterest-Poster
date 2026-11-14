# Combined eBay + Pinterest Automation Project

This folder combines the two working systems:

1. eBay API product search + automatic OAuth refresh
2. Pinterest browser automation using Playwright + Chrome

## IMPORTANT: preserve your existing setup

You do NOT need to reinstall everything or sign into Pinterest again.

### Reuse your existing Python environment

In PyCharm, you can set the interpreter for this project to the existing working interpreter from your Pinterest project:

`C:\Users\benne\Downloads\pinterest_browser_agent_windows\.venv\Scripts\python.exe`

PyCharm:
Settings -> Project -> Python Interpreter -> Add Interpreter -> Add Local Interpreter -> Existing -> select that python.exe

That lets this combined project use the packages you already installed.

### Copy your existing `.env`

Copy the `.env` from your working project into this folder.

Make sure it includes the eBay values:

```env
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
EBAY_REFRESH_TOKEN=...
EBAY_EPN_CAMPAIGN_ID=...
EBAY_MARKETPLACE_ID=EBAY_US
```

and Pinterest values:

```env
PINTEREST_BOARD_NAME=3D Printer Parts
PINTEREST_PROFILE_DIR=data/pinterest_profile
PINTEREST_HEADLESS=false
PINTEREST_DRY_RUN=true
```

### Preserve your Pinterest login

Copy this folder from the working Pinterest project:

`data\pinterest_profile`

into this combined project's:

`data\pinterest_profile`

That preserves the Chrome/Pinterest login session.

Do NOT delete that folder unless you intentionally want to log in again.

## Test 1 - eBay refresh token

```powershell
python test_refresh_token.py
```

Expected:

```text
SUCCESS: eBay refresh token worked.
```

## Test 2 - eBay search

```powershell
python search_products.py
```

Expected:

```text
Refreshing eBay user OAuth token...
OAuth token refreshed successfully.

=== Honda CB750 Exhaust ===
...
```

## Test 3 - Pinterest login status

You generally do not need to run this again if you copied the working profile:

```powershell
python pinterest_login.py
```

## Test 4 - Pinterest posting

Put a JPG named `test_pin.jpg` in the project root.

Keep this for a safe first test:

```env
PINTEREST_DRY_RUN=true
```

Then:

```powershell
python test_post.py
```

The known-good Pinterest selectors carried into this project are:

- Title: `get_by_role("textbox", name="Title")`
- Description: visible Description section -> first contenteditable
- Link: `get_by_placeholder("Add a link")`
- Board selector logic from the working version
- Publish button logic from the working version
- Chrome persistent profile
- `channel="chrome"`
- `chromium_sandbox=True`

## What is NOT connected yet

The eBay search does not automatically send a selected product to Pinterest yet.

That is the next development step after both sides test successfully inside this combined project.
