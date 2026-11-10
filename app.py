from flask import Flask, render_template, request

from bjt_bias.nodal import nodal_operating_point
from bjt_bias.operating_point import operating_point
from bjt_bias.params import validate
from bjt_bias.regions import classify

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}

RESULT_LABELS = (
    ("vb", "VB", "voltage"),
    ("vc", "VC", "voltage"),
    ("ve", "VE", "voltage"),
    ("ib", "IB", "current"),
    ("ic", "IC", "current"),
    ("ie", "IE", "current"),
    ("vce", "VCE", "voltage"),
)


def _format_current(amps: float) -> str:
    milliamps = amps * 1000
    if abs(milliamps) < 1:
        return f"{amps * 1_000_000:.4g} µA"
    return f"{milliamps:.4g} mA"


def _format_voltage(volts: float) -> str:
    return f"{volts:.4g} V"


def _format_resistance(ohms: float) -> str:
    if abs(ohms) >= 1000:
        return f"{ohms / 1000:.4g} kΩ"
    return f"{ohms:.4g} Ω"


def _schematic(values) -> dict[str, str]:
    """Labels for the circuit diagram; falls back to defaults on bad input."""

    def number(key: str, fallback: float) -> float:
        try:
            return float(str(values.get(key, fallback)).strip())
        except (TypeError, ValueError):
            return fallback

    return {
        "vcc": f"{number('vcc', 12):.4g} V",
        "r1": _format_resistance(number("r1", 100000)),
        "r2": _format_resistance(number("r2", 22000)),
        "rc": _format_resistance(number("rc", 2200)),
        "re": _format_resistance(number("re", 1000)),
        "beta": f"{number('beta', 100):.4g}",
    }


COMPARISON = (
    ("vb", "VB", "V", 1e-6),
    ("vc", "VC", "V", 1e-6),
    ("ve", "VE", "V", 1e-6),
    ("ib", "IB", "A", 1e-9),
    ("ic", "IC", "A", 1e-9),
    ("ie", "IE", "A", 1e-9),
    ("vce", "VCE", "V", 1e-6),
)


def _compare(closed: dict, nodal: dict | None) -> list[dict] | None:
    """Pair the two methods quantity by quantity, or None when off."""
    if nodal is None:
        return None
    rows = []
    for key, label, unit, tolerance in COMPARISON:
        primary = closed[key]
        independent = nodal[key]
        difference = abs(primary - independent)
        rows.append({
            "name": label,
            "unit": unit,
            "primary": f"{primary:.6g}",
            "independent": f"{independent:.6g}",
            "delta": f"{difference:.1e}",
            "ok": difference <= tolerance,
        })
    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template(
            "index.html", values=DEFAULTS, errors={}, schematic=_schematic(DEFAULTS)
        )

    inputs, errors = validate(request.form)
    if errors:
        return render_template(
            "index.html",
            values=request.form,
            errors=errors,
            schematic=_schematic(request.form),
        )

    op = operating_point(inputs)
    region, warnings = classify(op)
    results = [
        (label, (_format_voltage if kind == "voltage" else _format_current)(op[key]))
        for key, label, kind in RESULT_LABELS
    ]
    independent = None if region == "cutoff" else nodal_operating_point(inputs)
    return render_template(
        "index.html",
        values=request.form,
        errors={},
        results=results,
        region=region,
        warnings=warnings,
        comparison=_compare(op, independent),
        vce_display=_format_voltage(op["vce"]),
        schematic=_schematic(request.form),
    )


if __name__ == "__main__":
    app.run(debug=False)
