# BJT Common-Emitter DC Bias Web App — Design

- **Course:** ENG29 2121 (short lab)
- **Date:** 2026-11-10
- **Repo:** `https://github.com/pleng4995-cloud/Gitlab`, branch `main`
- **Status:** approved by the students on 2026-11-10

## 1. Intent and why

Students need a real, runnable Flask application that computes the DC operating
point (Q-point) of a **voltage-divider-biased common-emitter BJT**. The app is a
teaching aid: the student enters seven component values, sees the Q-point with
units, is told whether the transistor is in cutoff, active, or saturation, and
sees that a second, independently formulated calculation agrees with the first.

The lab grades the *separation of concerns* as much as the physics: engineering
logic, Flask routes, HTML templates, CSS, and tests must each live in their own
place, and the answer must be trustworthy enough to check by hand.

## 2. Goals

- One page, server-rendered, works with JavaScript disabled.
- Seven inputs: `VCC` (V), `R1` (Ω), `R2` (Ω), `RC` (Ω), `RE` (Ω), `beta` (–),
  `VBE` (V).
- Outputs with units: `VB`, `VC`, `VE`, `IB`, `IC`, `IE`, `VCE`, plus the
  region classification and any warnings.
- Per-field validation with the student's values preserved on error.
- A visible cross-check: closed-form result vs. nodal-analysis result, with the
  difference and a pass/fail marker.
- Runs locally on `http://127.0.0.1:5000` and is committed to GitHub today.

## 3. Non-goals (explicitly out of scope)

- **No AC analysis, no frequency response, no Bode plot, no function generator,
  no transient/time-domain simulation, no oscilloscope view.**
- **No decorative UI.** One plain stylesheet, readable typography, no images,
  animations, icons, or colour themes.
- No circuit editor, schematic canvas, drag-and-drop, or component library.
- No FET/MOSFET, op-amps, or other bias topologies (fixed bias, collector
  feedback, emitter feedback). Only voltage-divider CE bias.
- No database, accounts, saved history, REST/JSON API, JS framework, or build
  step.
- No changes to `electrical.py` / `test_electrical.py`.

## 4. Anti-goals (this is a failure even if the app runs)

- Any feature from section 3 creeping in.
- The "independent" calculation not being independent (e.g. `nodal.py`
  importing or reusing `operating_point.py`).
- Comparison shown at a precision so coarse that agreement is meaningless.
- A result the student cannot reproduce with a calculator.

## 5. Constraints

- Python 3.10.11; Flask only (pinned in `requirements.txt`); otherwise stdlib
  (`math`, `dataclasses`, `unittest`). No NumPy.
- Tests use `unittest`, matching the existing repo style, and run with
  `python -m unittest discover -s tests`.
- Start with `python app.py` (and `flask --app app run` must also work).
- No secrets, no network calls at runtime.
- `.gitignore` already covers `__pycache__/`, `*.pyc`, `.venv/`, `.env`.

## 6. Approaches considered

| # | Approach | Trade-off | Verdict |
|---|----------|-----------|---------|
| A | One flat `bjt.py` (validation + formulas + check) + `app.py` + one template/test | Fastest, but collapses the required separation into one module | Rejected |
| **B** | **Thin package: five small modules under `bjt_bias/`, `app.py`, two templates, one stylesheet, five test files** | ~12 small files; matches the required separation literally; each method stays provably independent | **Chosen** |
| C | Blueprints + WTForms + service layer + config classes | Professional-looking, doubles file count and indirection for seven numbers, risks the demo | Rejected |

**Cross-check choice (C from the brainstorm):** the independent calculation is a
nodal-analysis module **and** hand-worked reference values in the tests. It is
the only option that puts the comparison in the demo rather than only in code.

## 7. Structure

```
bjt_bias/
  __init__.py
  params.py           # BiasInputs dataclass; validate(raw_form) -> (inputs, errors)
  operating_point.py  # closed-form Q-point from textbook formulas
  nodal.py            # independent 4x4 node-voltage solve (Gaussian elimination)
  regions.py          # cutoff / active / saturation classification + warnings
app.py                # Flask: GET+POST on "/"
templates/
  base.html
  index.html
static/
  style.css
tests/
  test_params.py
  test_operating_point.py
  test_nodal.py
  test_regions.py
  test_routes.py
requirements.txt
README.md             # add "How to run" and "How to test"
```

Dependency direction: `app.py` → `bjt_bias.{params,operating_point,nodal,regions}`.
`nodal.py` imports nothing from `operating_point.py`. `operating_point.py` imports
nothing from `nodal.py`.

## 8. Engineering behaviour

### 8.1 Closed-form method (`operating_point.py`)

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VC  = VCC - IC * RC
VCE = VC - VE
VB  = VBE + VE
```

If `IB <= 0` the transistor is off: report `IB = IC = IE = 0`, `VCE = VCC`,
`VE = 0`, and `VB = VBB` (the base floats to the divider's open-circuit
voltage, which is below `VBE` in cutoff), and flag cutoff. Do not present
negative currents as physical results.

### 8.2 Independent method (`nodal.py`)

Treat the BJT as a fixed `VBE` source plus a current-controlled current source
`IC = beta * IB`. Solve the linear system with unknowns `[VB, VC, VE, IB]`:

```
[ 1/R1 + 1/R2    0        0          1      ] [VB]   [ VCC/R1 ]
[ 0              1/RC     0          beta   ] [VC] = [ VCC/RC ]
[ 0              0        1/RE    -(1+beta)] [VE]   [   0    ]
[ 1              0       -1          0      ] [IB]   [  VBE   ]
```

Solve by Gaussian elimination with partial pivoting. No NumPy.

### 8.3 Comparison

- Compare `VB, VC, VE, IB, IC, IE, VCE` pairwise.
- Tolerance: `1e-9` absolute for currents (A) and `1e-6` absolute for voltages
  (V); exact constants are the builder's call.
- Show both values and the delta; mark "OK" or "MISMATCH".
- The comparison panel uses its own formatter: **6 significant figures** for
  each method's value and the delta in scientific notation with 2 significant
  figures (e.g. `Δ = 1.4e-16 V`). This is separate from the 4-significant-figure
  results formatter, so agreement is not hidden by rounding.
- In cutoff, the linear model is invalid, so show the comparison as
  "n/a — transistor off" instead of a mismatch.

### 8.4 Region rules (`regions.py`)

| Condition | Region | Warning text (Thai UI) |
|-----------|--------|------------------------|
| `IB <= 0` (i.e. `VBE >= VBB`) | cutoff | "ทรานซิสเตอร์อยู่ในช่วง cutoff (IB ≈ 0)" |
| `IB > 0` and `VCE < 0.3 V` | saturation | "ทรานซิสเตอร์อยู่ในช่วง saturation (VCE < 0.3 V) ค่า Q-point ใช้เป็นแอมพลิฟายเออร์ไม่ได้" |
| `IB` or `VCE` not finite (overflow) | invalid | "ค่าผิดปกติ: ผลลัพธ์ไม่ใช่จำนวนจริง (ตรวจสอบค่าอินพุต)" |
| otherwise | active | none |

`VCE > VCC` is unreachable for valid inputs (`VCE < VCC` whenever `IB > 0`, and
`VCE = VCC` in cutoff), so no anomaly rule is implemented for it.

Region names in the UI stay in English (cutoff / active / saturation) with Thai
explanations.

### 8.5 Validation (`params.py`)

- All seven fields required; blank, non-numeric, `NaN`, and `inf` are rejected
  per field with a Thai message.
- `VCC > 0`; `R1, R2, RC, RE > 0`; `beta > 0`; `0 <= VBE < VCC`.
- Errors are returned as `{field_name: message}` so the template can place each
  message next to its input and re-fill the previous values.
- No cross-field constraint such as `R1 > R2` — a reversed divider is legal
  input, it just biases differently.

### 8.6 Web behaviour

- `GET /` renders the form with defaults:
  `VCC=12, R1=47000, R2=10000, RC=4700, RE=1000, beta=150, VBE=0.7`.
- `POST /` validates:
  - invalid → re-render form, HTTP 200, field errors, previous values kept;
  - valid → render results, HTTP 200.
- Results are formatted to 4 significant figures; currents shown in mA, voltages
  in V, resistances in Ω/kΩ.
- All labels are tied to inputs; error text sits beside the field. No JavaScript.

## 9. Testing

- **Hand-worked reference** (derived by hand algebra, independent of both code
  paths), defaults `VCC=12, R1=47000, R2=10000, RC=4700, RE=1000, beta=150,
  VBE=0.7`, stored to full precision so the tolerance is not fighting rounding:

  ```
  VBB = 2.1052631578947367 V   RB  = 8245.61403508772 Ω
  IB  = 8.824501487275531e-06 A
  IC  = 1.3236752230913298e-03 A
  IE  = 1.3324997245786052e-03 A
  VE  = 1.3324997245786052 V   VB  = 2.032499724578605 V
  VC  = 5.77872645147075 V     VCE = 4.446226726892145 V
  region = active
  ```

  Derived with exact rational arithmetic (`fractions.Fraction`), independently of
  both code paths, so the oracle is not a copy of the implementation's output.

  Test tolerance is `1e-6` absolute for every quantity, which the published
  precision satisfies with margin.
- `test_operating_point.py`: reference values within `1e-6`; `VBE = 0` case
  (valid, active); high-`RC` saturation case.
- `test_nodal.py`: nodal result matches the same hand-worked reference within
  `1e-6`; the module does not import `operating_point`.
- `test_regions.py`: cutoff when `VBE >= VBB`; saturation when `VCE < 0.3 V`;
  active otherwise; boundary at exactly `0.3 V`.
- `test_params.py`: blank, text, zero, negative, `NaN`/`inf`, `beta <= 0`,
  `VBE >= VCC` all rejected with the right field key; valid input accepted.
- `test_routes.py`: `GET /` is 200 and contains all seven input names;
  valid `POST /` is 200 and shows mA values and the region; invalid `POST /` is
  200 with an error message and the typed value still present.
- Target ≈ 20 tests, all green before commit.

## 10. Delivery

- Branch `feature/bjt-dc-bias`, commits in reviewable steps, push to GitHub,
  then merge to `main` after review (finishing-a-development-branch skill).
- `README.md` gains: what the app does, install, run, test.
- Demo checklist: active case, saturation case, cutoff case, invalid input,
  cross-check panel.

## 11. Acceptance criteria (agreed with the students)

| # | Criterion | How it is checked |
|---|-----------|-------------------|
| 1 | `python -m unittest discover -s tests` passes, ≥ 20 tests | real run, raw output shown |
| 2 | At least one test compares the two methods | `tests/test_nodal.py` |
| 3 | Changing `VCC` 12 → 24 changes the result proportionally | two browser runs |
| 4 | Defaults give `VCE ≈ 4.446 V`, `IC ≈ 1.324 mA`, region active | `http://127.0.0.1:5000` |
| 5 | `R1=0`, `beta=-5`, `VBE=15`, blank → Thai per-field error, values kept | typed by hand |
| 6 | Saturation and cutoff cases show the right warning | typed by hand |
| 7 | Cross-check panel shows both columns, Δ, and OK | on screen |
| 8 | `python app.py` serves `127.0.0.1:5000` | real run |
| 9 | Commit exists on GitHub | `git log` + repo page |
| 10 | No AC/Bode/transient/function generator/decorative UI | file list + grep for forbidden terms |
| 11 | `electrical.py` and its tests still pass | run the old test file |

## 12. Left to the builder

- Exact CSS rules, Thai wording of labels/messages, error phrasing, route
  function names, tolerance constants, and how many commits to split the work
  into.
