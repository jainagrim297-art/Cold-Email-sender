# Integration of Lead Enrichment and Pipeline Start

The goal is to enable the autonomous outreach engine by integrating the Hunter.io and Apollo APIs to find real contact emails for discovered startups, fixing existing bugs in `main.py`, and starting the engine.

## User Review Required

> [!IMPORTANT]
> The engine will now attempt to find real contact emails using your Hunter.io API key. For testing safety, I will keep a configuration flag to allow you to send emails to yourself first before blasting real prospects.

## Proposed Changes

### Lead Enrichment Module

#### [NEW] [enrichment.py](file:///d:/1styearproject/src/scrapers/enrichment.py)
*   Implement `get_contact_email(domain)` function.
*   First attempts Hunter.io API.
*   Falls back to Apollo API if necessary.

### Main Pipeline Modification

#### [MODIFY] [main.py](file:///d:/1styearproject/src/main.py)
*   **Fix**: Define `MY_EMAIL` using `GMAIL_ADDRESS` from `.env`.
*   **Fix**: Correct file paths for `target_leads.csv` and the LoRA adapter.
*   **Feature**: Integrate the new `enrichment.py` to replace placeholder emails with real ones.
*   **Robustness**: Add domain extraction logic from URLs.

### Searcher/Discovery Update

#### [MODIFY] [startup_hunter.py](file:///d:/1styearproject/src/scrapers/startup_hunter.py)
*   Ensure CSV saving is robust and handles the directory structure correctly.

---

## Open Questions

1.  **Test Mode**: Should I set the engine to "Test Mode" by default? In this mode, even if a real email is found, it will send the pitch to *your* Gmail address so you can see how it looks before real use.
2.  **Apollo Usage**: Your Apollo key is available. Do you want it to be the primary source, or just a fallback if Hunter fails?

## Verification Plan

### Automated Tests
1.  Run a small test script to verify Hunter.io API connectivity using your key.
2.  Run the discovery phase and verify `target_leads.csv` is populated.

### Manual Verification
1.  Execute `python src/main.py` (in test mode) and verify an email arrives in your inbox with a startup's pitch.
