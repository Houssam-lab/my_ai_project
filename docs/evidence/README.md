# `docs/evidence/`

Visual evidence attached to pull requests, committed so a reviewer can see it
from the diff and so the link in a PR body does not rot.

D-270 L1 asks for the command and its output; `validate_pr_description.py`
additionally requires a screenshot on any change that touches `frontend/`,
because what a student sees should be visible in review. Files here are that
screenshot — captured from a real run, never a mock-up, and named for the change
they belong to.

| file | what it shows |
|---|---|
| `react19-frontend-2026-08-24.png` | the login screen served by `next start` after the React 18.3.1 → 19.2.8 / Next 16.3.0 → 16.3.1 / katex 0.16 → 0.18 uplift (#2291, #2292): Arabic RTL layout, theme tokens and form controls all intact. |
| `d305-hard-currency-frontier-2026-10-01.png` | the admin-only Hard-Currency Center (D-305) on the built bundle, logged in as the owner: the frontier map with the real funnel on top (1 contact · 0 replies · 0 settled payments · `GATE_C = ABSENT`), the five derived classifications for the 25 paths, and one path's eight-link chain with its next link and actor. |
| `d305-hard-currency-cbam-2026-10-01.png` | the CBAM decision tool on pinned code `2523100090`: Algerian default values, path toll, crossover threshold, the 73-of-90 banner, a plant figure of 0.6 tCO₂e/t giving 2026 as the first cheaper year, and the threshold-by-year chart with its hover tooltip. |
| `d305-hard-currency-einvoicing-2026-10-01.png` | the FR e-invoicing workbench after uploading `docs/commercial/outreach/demo/DEMO_20_FICHES.csv`: summary tiles equal to `audit_french_csv`, the anomaly table and the two downloads; the file is not stored. |
| `d305-student-menu-no-center-2026-10-01.png` | the same build logged in as a student: the header menu has no Hard-Currency Center entry. |
