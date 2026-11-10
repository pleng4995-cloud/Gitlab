# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A small Flask app that computes the voltage-divider BJT DC operating point, validates seven inputs, warns about cutoff/saturation, and shows a second independent calculation that agrees.

**Architecture:** Five tiny modules under `bjt_bias/` (validation, closed-form solver, nodal solver, region rules), a single `app.py` with one GET/POST route, two templates, one stylesheet. `nodal.py` never imports `operating_point.py`, so the cross-check is genuinely independent.

**Tech Stack:** Python 3.10.11, Flask (pinned), stdlib only otherwise (`math`, `dataclasses`, `unittest`). No NumPy, no JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md`

## Global Constraints

- Python 3.10.11 (`python`), Flask pinned in `requirements.txt`; no NumPy, no JS, no build step.
- Tests are `unittest`, run with `python -m unittest discover -s tests` from the repo root.
- Server listens on `http://127.0.0.1:5000`; `python app.py` must work.
- `git` is not on PATH; use `C:\Users\B6811938\AppData\Local\Programs\Git\cmd\git.exe`.
- Work on branch `feature/bjt-dc-bias`; never modify `electrical.py` or `test_electrical.py`.
- UI copy in Thai; engineering symbols stay Latin (`VCC`, `IB`, `VCE`, `cutoff`/`active`/`saturation`).
- Scope is DC bias only: no AC, Bode, transient, function generator, circuit editor, or decorative UI.
- Field names, everywhere (form, dataclass, errors): `vcc, r1, r2, rc, re, beta, vbe`.
- Reference values for the default inputs, used by every task: `VBB=2.105263158 V`, `RB=8245.614035 Ω`, `IB=8.8245e-06 A`, `IC=1.32368e-03 A`, `IE=1.33250e-03 A`, `VE=1.33250 V`, `VC=5.77871 V`, `VCE=4.44621 V`, `VB=2.03250 V`, region `active`.

## Review Focus

These are inputs the spec implies but does not test explicitly. Each has a test in the task that owns the code.

1. A POST that omits a field entirely (truncated form) — must produce a per-field error, not `KeyError` → Task 1.
2. Numbers with surrounding whitespace (`" 12 "`) — must be accepted → Task 1.
3. `VBE` exactly equal to `VBB` — must give cutoff with `IB = 0`, no division by zero → Task 2.
4. A very small `RE` (0.01 Ω) — must give a saturation warning, not a crash or negative-current display → Tasks 2 and 4.
5. `beta` between 0 and 1 — the spec only requires `beta > 0`, so it must be accepted and computed → Task 1.

---

### Task 1: Environment, package scaffold, and validation

**Files:**
- Create: `requirements.txt`, `bjt_bias/__init__.py`, `bjt_bias/params.py`, `tests/__init__.py`, `tests/test_params.py`

**Interfaces:**
- Produces: `BiasInputs(vcc, r1, r2, rc, re, beta, vbe)` frozen dataclass of floats; `validate(raw: Mapping[str, str]) -> tuple[BiasInputs | None, dict[str, str]]` returning `(inputs, {})` or `(None, errors)` keyed by field name.

- [ ] **Step 1: Create the virtual environment and install Flask**

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install flask
.venv\Scripts\python -c "import flask; print(flask.__version__)"
```

Then write `requirements.txt` with exactly `Flask==<the printed version>`.

- [ ] **Step 2: Write the failing tests**

`tests/test_params.py`:

```python
import unittest
from bjt_bias.params import BiasInputs, validate

VALID = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
         "re": "1000", "beta": "150", "vbe": "0.7"}


class TestValidate(unittest.TestCase):
    def test_valid_input_returns_dataclass(self):
        inputs, errors = validate(VALID)
        self.assertEqual(errors, {})
        self.assertIsInstance(inputs, BiasInputs)
        self.assertEqual((inputs.vcc, inputs.beta), (12.0, 150.0))

    def test_blank_field_is_rejected(self):
        inputs, errors = validate({**VALID, "r1": ""})
        self.assertIsNone(inputs)
        self.assertIn("r1", errors)

    def test_non_numeric_is_rejected(self):
        _, errors = validate({**VALID, "rc": "abc"})
        self.assertIn("rc", errors)

    def test_zero_and_negative_resistance_rejected(self):
        for field in ("r1", "r2", "rc", "re"):
            self.assertIn(field, validate({**VALID, field: "0"})[1])
            self.assertIn(field, validate({**VALID, field: "-1"})[1])

    def test_beta_must_be_positive(self):
        self.assertIn("beta", validate({**VALID, "beta": "0"})[1])

    def test_vbe_must_be_below_vcc(self):
        self.assertIn("vbe", validate({**VALID, "vbe": "12"})[1])

    def test_nan_and_inf_rejected(self):
        for value in ("nan", "inf"):
            self.assertIn("vcc", validate({**VALID, "vcc": value})[1])

    def test_missing_key_is_treated_as_blank(self):
        raw = dict(VALID)
        del raw["re"]
        inputs, errors = validate(raw)
        self.assertIsNone(inputs)
        self.assertIn("re", errors)

    def test_whitespace_is_stripped(self):
        inputs, errors = validate({**VALID, "vcc": " 12 "})
        self.assertEqual(errors, {})
        self.assertEqual(inputs.vcc, 12.0)

    def test_beta_between_zero_and_one_is_accepted(self):
        inputs, errors = validate({**VALID, "beta": "0.5"})
        self.assertEqual(errors, {})
        self.assertEqual(inputs.beta, 0.5)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv\Scripts\python -m unittest tests.test_params -v`
Expected: `ModuleNotFoundError: No module named 'bjt_bias'`.

(`tests/__init__.py` is empty; it makes `tests.test_params` importable and keeps `discover -t .` module names stable.)

- [ ] **Step 4: Implement `bjt_bias/params.py`**

`BiasInputs` is a `@dataclass(frozen=True)` with the seven float fields in the order listed above. `validate` loops over `FIELD_ORDER = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`, reads `raw.get(field, "")`, strips whitespace, parses with `float()`, and rejects non-finite values with `math.isfinite`. Rules: `vcc > 0`; `r1, r2, rc, re > 0`; `beta > 0`; `0 <= vbe < vcc`. Collect every error before returning; do not stop at the first. Thai messages: `"กรุณากรอกตัวเลข"` for blank/non-numeric, `"ต้องมากกว่า 0"` for non-positive, `"ต้องอยู่ระหว่าง 0 ถึง VCC"` for `vbe`. Create an empty `bjt_bias/__init__.py`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python -m unittest tests.test_params -v`
Expected: 10 tests, `OK`.

- [ ] **Step 6: Commit**

```powershell
$git = "C:\Users\B6811938\AppData\Local\Programs\Git\cmd\git.exe"
& $git checkout -b feature/bjt-dc-bias
& $git add requirements.txt bjt_bias tests
& $git commit -m "feat: add bias input validation"
& $git add docs
& $git commit -m "docs: add design and implementation plan"
```

---

### Task 2: Closed-form operating point

**Files:**
- Create: `bjt_bias/operating_point.py`, `tests/test_operating_point.py`

**Interfaces:**
- Consumes: `BiasInputs` from `bjt_bias.params`.
- Produces: `operating_point(inputs: BiasInputs) -> dict[str, float]` with keys `vbb, rb, ib, ic, ie, vb, vc, ve, vce`.

- [ ] **Step 1: Write the failing tests**

`tests/test_operating_point.py`:

```python
import math
import unittest
from bjt_bias.operating_point import operating_point
from bjt_bias.params import BiasInputs

DEFAULTS = BiasInputs(vcc=12, r1=47000, r2=10000, rc=4700,
                      re=1000, beta=150, vbe=0.7)


class TestOperatingPoint(unittest.TestCase):
    def test_matches_hand_worked_reference(self):
        op = operating_point(DEFAULTS)
        expected = {"vbb": 2.105263158, "rb": 8245.614035, "ib": 8.8245e-06,
                    "ic": 1.32368e-03, "ie": 1.33250e-03, "ve": 1.33250,
                    "vc": 5.77871, "vce": 4.44621, "vb": 2.03250}
        for key, value in expected.items():
            self.assertTrue(math.isclose(op[key], value, rel_tol=1e-6),
                            f"{key}: {op[key]} != {value}")

    def test_vbe_zero_is_valid_and_active(self):
        op = operating_point(BiasInputs(12, 47000, 10000, 4700, 1000, 150, 0.0))
        self.assertGreater(op["ic"], 0)
        self.assertGreater(op["vce"], 0.3)

    def test_cutoff_when_vbe_equals_vbb(self):
        vbb = 12 * 10000 / 57000
        op = operating_point(BiasInputs(12, 47000, 10000, 4700, 1000, 150, vbb))
        self.assertEqual(op["ib"], 0)
        self.assertEqual(op["ic"], 0)
        self.assertEqual(op["ie"], 0)
        self.assertEqual(op["ve"], 0)
        self.assertAlmostEqual(op["vb"], vbb, places=9)
        self.assertEqual(op["vce"], 12)

    def test_tiny_re_goes_into_saturation(self):
        op = operating_point(BiasInputs(12, 47000, 10000, 4700, 0.01, 150, 0.7))
        self.assertLess(op["vce"], 0.3)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m unittest tests.test_operating_point -v`
Expected: `ModuleNotFoundError` for `bjt_bias.operating_point`.

- [ ] **Step 3: Implement `bjt_bias/operating_point.py`**

Use the formulas in spec §8.1 verbatim. Compute `vbb` and `rb` first and return them. If `ib <= 0`, return `ib = ic = ie = 0`, `ve = 0`, `vc = vcc`, `vce = vcc`, `vb = vbb` (spec §8.1). No clamping anywhere else — saturation is reported, not simulated.

- [ ] **Step 4: Run to verify pass**

Run: `.venv\Scripts\python -m unittest tests.test_operating_point -v`
Expected: 4 tests, `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add bjt_bias/operating_point.py tests/test_operating_point.py
& $git commit -m "feat: add closed-form DC operating point"
```

---

### Task 3: Independent nodal solver

**Files:**
- Create: `bjt_bias/nodal.py`, `tests/test_nodal.py`

**Interfaces:**
- Consumes: `BiasInputs`.
- Produces: `nodal_operating_point(inputs: BiasInputs) -> dict[str, float]` with keys `ib, ic, ie, vb, vc, ve, vce`; helper `_solve(matrix: list[list[float]], rhs: list[float]) -> list[float]`.

- [ ] **Step 1: Write the failing tests**

`tests/test_nodal.py`:

```python
import inspect
import math
import unittest
from bjt_bias import nodal
from bjt_bias.nodal import nodal_operating_point
from bjt_bias.operating_point import operating_point
from bjt_bias.params import BiasInputs

CASES = [
    BiasInputs(12, 47000, 10000, 4700, 1000, 150, 0.7),
    BiasInputs(24, 47000, 10000, 4700, 1000, 150, 0.7),
    BiasInputs(12, 10000, 47000, 2200, 470, 100, 0.65),
]


class TestNodal(unittest.TestCase):
    def test_matches_hand_worked_reference(self):
        op = nodal_operating_point(CASES[0])
        expected = {"ib": 8.8245e-06, "ic": 1.32368e-03, "ie": 1.33250e-03,
                    "vb": 2.03250, "vc": 5.77871, "ve": 1.33250, "vce": 4.44621}
        for key, value in expected.items():
            self.assertTrue(math.isclose(op[key], value, rel_tol=1e-6),
                            f"{key}: {op[key]} != {value}")

    def test_agrees_with_closed_form(self):
        for case in CASES:
            nodal_op = nodal_operating_point(case)
            closed_op = operating_point(case)
            for key in ("ib", "ic", "ie", "vb", "vc", "ve", "vce"):
                self.assertTrue(math.isclose(nodal_op[key], closed_op[key], rel_tol=1e-9),
                                f"{key} differs on {case}")

    def test_solver_swaps_rows_when_pivot_is_zero(self):
        self.assertEqual(nodal._solve([[0, 1], [1, 0]], [2, 3]), [3, 2])

    def test_does_not_import_closed_form_module(self):
        source = inspect.getsource(nodal)
        self.assertNotIn("from .operating_point", source)
        self.assertNotIn("from bjt_bias.operating_point", source)
        self.assertNotIn("import operating_point", source)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m unittest tests.test_nodal -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `bjt_bias/nodal.py`**

Build the 4×4 system from spec §8.2 with unknowns `[VB, VC, VE, IB]`, solve with Gaussian elimination and partial pivoting in `_solve`, then derive `ic = beta * ib`, `ie = (1 + beta) * ib`, `vce = vc - ve`. Raise `ValueError("singular system")` if a pivot stays zero. Do not import `operating_point` and do not use the `vbb`/`rb` substitution.

- [ ] **Step 4: Run to verify pass**

Run: `.venv\Scripts\python -m unittest tests.test_nodal -v`
Expected: 4 tests, `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add bjt_bias/nodal.py tests/test_nodal.py
& $git commit -m "feat: add independent nodal cross-check"
```

---

### Task 4: Region classification and warnings

**Files:**
- Create: `bjt_bias/regions.py`, `tests/test_regions.py`

**Interfaces:**
- Consumes: the `operating_point` result dict.
- Produces: `classify(op: Mapping[str, float]) -> tuple[str, list[str]]` returning `("cutoff" | "saturation" | "active", warnings)`; constant `SATURATION_VCE_V = 0.3`.

- [ ] **Step 1: Write the failing tests**

`tests/test_regions.py`:

```python
import unittest
from bjt_bias.regions import classify

ACTIVE = {"ib": 1e-5, "vce": 4.4}
SATURATED = {"ib": 1e-5, "vce": 0.2}
BOUNDARY = {"ib": 1e-5, "vce": 0.3}
OFF = {"ib": 0.0, "vce": 12.0}


class TestClassify(unittest.TestCase):
    def test_active_has_no_warning(self):
        region, warnings = classify(ACTIVE)
        self.assertEqual(region, "active")
        self.assertEqual(warnings, [])

    def test_saturation_below_threshold(self):
        region, warnings = classify(SATURATED)
        self.assertEqual(region, "saturation")
        self.assertEqual(len(warnings), 1)

    def test_exactly_0_3_v_is_active(self):
        self.assertEqual(classify(BOUNDARY)[0], "active")

    def test_zero_base_current_is_cutoff(self):
        region, warnings = classify(OFF)
        self.assertEqual(region, "cutoff")
        self.assertEqual(len(warnings), 1)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m unittest tests.test_regions -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `bjt_bias/regions.py`**

Order matters: `ib <= 0` → cutoff; else `vce < SATURATION_VCE_V` → saturation; else active. Warnings use the Thai strings from spec §8.4.

- [ ] **Step 4: Run to verify pass**

Run: `.venv\Scripts\python -m unittest tests.test_regions -v`
Expected: 4 tests, `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add bjt_bias/regions.py tests/test_regions.py
& $git commit -m "feat: add region classification and warnings"
```

---

### Task 5: Flask skeleton, form, templates, stylesheet

**Files:**
- Create: `app.py`, `templates/base.html`, `templates/index.html`, `static/style.css`, `tests/test_routes.py`

**Interfaces:**
- Produces: `app` (Flask instance), `DEFAULTS: dict[str, str]` with the seven default strings, `GET /` returning 200.

- [ ] **Step 1: Write the failing tests**

`tests/test_routes.py` (this file grows in Tasks 6 and 7):

```python
import unittest
from app import app


class TestFormPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_returns_form_with_all_fields(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertEqual(self.client.get("/").status_code, 200)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)

    def test_get_prefills_defaults(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="12"', body)
        self.assertIn('value="47000"', body)

    def test_no_out_of_scope_features_on_page(self):
        body = self.client.get("/").get_data(as_text=True).lower()
        for word in ("bode", "function generator", "transient", "oscilloscope"):
            self.assertNotIn(word, body)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m unittest tests.test_routes -v`
Expected: `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement the skeleton**

`app.py`: `app = Flask(__name__)`, `DEFAULTS` with `{"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700", "re": "1000", "beta": "150", "vbe": "0.7"}`, `@app.route("/", methods=["GET", "POST"])` returning `render_template("index.html", values=DEFAULTS, errors={})` for now, and `if __name__ == "__main__": app.run(debug=False)` (no reloader, one process, predictable demo).

`templates/base.html`: `<!doctype html>`, `<meta charset="utf-8">`, Thai `<title>`, link to `static/style.css`, `{% block content %}{% endblock %}`.

`templates/index.html`: extends base; one `<form method="post">`; seven `<label for>` + `<input type="text" name="..." value="{{ values[...] }}">` pairs; a submit button. No results section yet.

`static/style.css`: system font stack, max-width 40rem, plain table borders, red error text class. No colours beyond neutral greys.

- [ ] **Step 4: Run to verify pass**

Run: `.venv\Scripts\python -m unittest tests.test_routes -v`
Expected: 3 tests, `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add app.py templates static tests/test_routes.py
& $git commit -m "feat: add Flask form skeleton"
```

---

### Task 6: POST handling, validation errors, and results table

**Files:**
- Modify: `app.py`, `templates/index.html`, `tests/test_routes.py`

**Interfaces:**
- Consumes: `validate`, `operating_point`, `classify`.
- Produces: `_format_current(amps: float) -> str` (mA, 4 significant figures), `_format_voltage(volts: float) -> str` (V, 4 significant figures); `POST /` renders `results`, `region`, `warnings`.

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_routes.py`:

```python
VALID = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
         "re": "1000", "beta": "150", "vbe": "0.7"}


class TestCompute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_valid_post_shows_operating_point(self):
        response = self.client.post("/", data=VALID)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("4.446", body)
        self.assertIn("1.324", body)
        self.assertIn("mA", body)
        self.assertIn("active", body)

    def test_invalid_post_keeps_values_and_shows_error(self):
        response = self.client.post("/", data={**VALID, "r1": "0"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", body)
        self.assertIn('value="0"', body)

    def test_cutoff_case_warns(self):
        body = self.client.post("/", data={**VALID, "vbe": "5"}).get_data(as_text=True)
        self.assertIn("cutoff", body)

    def test_saturation_case_warns(self):
        body = self.client.post("/", data={**VALID, "rc": "47000"}).get_data(as_text=True)
        self.assertIn("saturation", body)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m unittest tests.test_routes -v`
Expected: the four new tests fail (no `4.446` in the page, no Thai error).

- [ ] **Step 3: Implement POST handling**

In `app.py`: on POST call `validate(request.form)`; on errors re-render with `values=request.form` and `errors`; on success compute `op = operating_point(inputs)`, `region, warnings = classify(op)`, and render `index.html` with `values`, `results` (list of `(label, formatted_value)` for `VB, VC, VE, IB, IC, IE, VCE`), `region`, `warnings`.

Formatting: `_format_current` multiplies by 1000 and formats `f"{value * 1000:.4g} mA"`; `_format_voltage` formats `f"{value:.4g} V"`.

In `index.html`: render `errors[field]` in `<span class="error">` next to each input; below the form, when `results` is set, a `<table>` of results, a `<p class="region">` with the region, and a `<ul>` of warnings.

- [ ] **Step 4: Run to verify pass**

Run: `.venv\Scripts\python -m unittest tests.test_routes -v`
Expected: 7 tests, `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add app.py templates/index.html tests/test_routes.py
& $git commit -m "feat: compute and display DC operating point"
```

---

### Task 7: Cross-check panel

**Files:**
- Modify: `app.py`, `templates/index.html`, `tests/test_routes.py`

**Interfaces:**
- Consumes: `operating_point`, `nodal_operating_point`.
- Produces: `_compare(closed: dict, nodal: dict | None) -> list[dict]` with keys `name, unit, primary, independent, delta, ok`; `nodal=None` means the linear model is invalid (cutoff).

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_routes.py`:

```python
class TestCrossCheck(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_valid_post_shows_two_methods_and_ok(self):
        body = self.client.post("/", data=VALID).get_data(as_text=True)
        self.assertIn("Nodal", body)
        self.assertIn("OK", body)
        self.assertIn("Δ", body)

    def test_cutoff_shows_not_applicable(self):
        body = self.client.post("/", data={**VALID, "vbe": "5"}).get_data(as_text=True)
        self.assertIn("n/a", body)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv\Scripts\python -m unittest tests.test_routes -v`
Expected: the two new tests fail.

- [ ] **Step 3: Implement `_compare` and the panel**

`_compare` pairs the seven quantities; tolerance `1e-9` for currents (`ib, ic, ie`) and `1e-6` for voltages (`vb, vc, ve, vce`); formats each side to 6 significant figures (`f"{value:.6g}"`) and the delta as `f"{abs(primary - independent):.1e}"`. In cutoff (`region == "cutoff"`), pass `nodal=None` and render a single row `"n/a — transistor off"` instead of the table. Add a `<h2>` "ตรวจสอบด้วยวิธีอิสระ (Nodal)" and the table to `index.html`, plus a caption: "การตรวจนี้ยืนยันว่าสองวิธีคำนวณได้คำตอบเดียวกัน ไม่ได้ยืนยันว่าทรานซิสเตอร์อยู่ในช่วงที่แบบจำลองใช้ได้" — the check proves the algebra agrees, not the device region.

- [ ] **Step 4: Run to verify pass**

Run: `.venv\Scripts\python -m unittest tests.test_routes -v`
Expected: 9 tests, `OK`.

- [ ] **Step 5: Run the whole suite**

Run: `.venv\Scripts\python -m unittest discover -s tests -t . -v`
Expected: all tests `OK` (≥ 30).

- [ ] **Step 6: Commit**

```powershell
& $git add app.py templates/index.html tests/test_routes.py
& $git commit -m "feat: add independent nodal cross-check panel"
```

---

### Task 8: README, full verification, and push

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md` (status only)

- [ ] **Step 1: Update `README.md`**

Add sections: what the app computes, `python -m venv .venv`, `.venv\Scripts\python -m pip install -r requirements.txt`, `.venv\Scripts\python app.py`, open `http://127.0.0.1:5000`, and `.venv\Scripts\python -m unittest discover -s tests -t .`. Keep the existing DC-calculator text.

- [ ] **Step 2: Verify the old tests still pass**

Run: `.venv\Scripts\python -m unittest test_electrical -v`
Expected: `OK`.

- [ ] **Step 3: Run the full suite one more time**

Run: `.venv\Scripts\python -m unittest discover -s tests -t . -v`
Expected: all `OK`.

- [ ] **Step 4: Start the app and walk the demo checklist**

Run: `.venv\Scripts\python app.py` in the background; open `http://127.0.0.1:5000`.
Check: defaults → `VCE 4.446 V`, `IC 1.324 mA`, active, cross-check OK; `VCC=24` → values change; `rc=47000` → saturation warning; `vbe=5` → cutoff warning and `n/a`; `r1=0` → Thai error with `0` kept. Stop the server.

- [ ] **Step 5: Confirm scope**

Run: `& $git ls-files` and confirm no AC/Bode/transient files exist; grep the templates for `bode|transient|function generator|oscilloscope` and expect no matches.

- [ ] **Step 6: Push**

```powershell
& $git add README.md
& $git commit -m "docs: document how to run and test the bias app"
& $git push -u origin feature/bjt-dc-bias
```

- [ ] **Step 7: Merge after review**

After the reviewer passes the branch, merge to `main` and push (see `finishing-a-development-branch`).
