# Account ABC — Portfolio Rebalancing Test Package

This entire folder contains the manual and automated test deliverables for the
Account ABC rebalancing calculation (the "number of shares to buy/sell" for
each security). Start here if you're opening this folder for the first time.

## What's in this folder

| File | What it is |
|---|---|
| `North American Technical Assessment.ipynb` | The full automated test suite —> `pytest` tests covering the calculation engine, input validation, and the vesting rule. Self-contained: run it in Google Colab (or any Jupyter environment) with no setup beyond the steps below. |
| `test_cases_for_northamerican_assessment.xlsx` | manual test cases (calculation logic, validation, vesting, UI, and API layers), including which ones are automated and a pointer to the exact automated test function for each. |
| `ASSUMPTIONS.md` | The assumptions both suites are built on —> rounding rules, validation rules, scope decisions (like vesting), and what's intentionally out of scope. Kindly read this if an expected result looks surprising. |
| `rebalancer.py` | Standalone copy of the reference implementation (the System Under Test) that the notebook also writes out and imports. Handy for reading the calculation logic on its own, outside the notebook. |

## How to run the automated test suite (`.ipynb`)

1. Go to [colab.research.google.com](https://colab.research.google.com) and choose **Upload** (or **File → Upload notebook**), then select `North American Technical Assessment.ipynb`. (Any Jupyter environment works the same way — Colab is just the easiest with zero local setup.)
2. Run the cells from top to bottom (**Runtime → Run all**, or step through with Shift+Enter):
   - The first code cell installs `pytest` and `ipytest` into the Colab runtime.
   - A `%%writefile rebalancer.py` cell writes the reference implementation to disk in that runtime (this is what's being tested — see the notebook's own explanation of this step if you're curious why).
   - A second `%%writefile` cell writes out the test file.
   - The final `ipytest.run('-vv')` cell actually executes all tests and prints a pass/fail result for each.
3. You should see `28 passed` at the bottom with no failures. If anything fails, it means the reference implementation was changed without updating the tests (or vice versa) . Kindly check `ASSUMPTIONS.md` first, since most expected values trace back to an assumption listed there.

No API keys, external services, or local installs are needed , everything the notebook needs, it installs or writes for itself in the first few cells.

## How the three test documents relate

- **`ASSUMPTIONS.md`** is the source of truth. Every expected value in both the spreadsheet and the notebook is derived from an assumption listed there (e.g., the rounding rule, or how vesting reduces the investable base).
- **`test_cases_for_northamerican_assessment.xlsx`** is the complete test plan — all 25 cases, including the ones that can't be automated yet (the UI and API layers, marked `Automated = N` / `Status = Blocked`, with a note explaining why). Each automated row's **"Automated Test Ref"** column names the exact `pytest` function in the notebook that covers it — that's the traceability mapping between the two documents.
- **`North American Technical Assessment.ipynb`** is the executable proof for the 19 of 25 cases that can be automated today. It embeds its own copy of the reference implementation and the test file, so it runs standalone without needing this whole folder.

If you're reviewing this package end to end, a natural order is: `ASSUMPTIONS.md` → `manual_test_cases.xlsx` (for the full picture of what's tested and how) → the notebook (to see the automated subset actually pass).
