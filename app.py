from flask import Flask, render_template, request

from bjt_bias.nodal import nodal_operating_point
from bjt_bias.operating_point import operating_point
from bjt_bias.params import validate
from bjt_bias.regions import classify

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
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
    return f"{amps * 1000:.4g} mA"


def _format_voltage(volts: float) -> str:
    return f"{volts:.4g} V"


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
        return render_template("index.html", values=DEFAULTS, errors={})

    inputs, errors = validate(request.form)
    if errors:
        return render_template("index.html", values=request.form, errors=errors)

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
    )


if __name__ == "__main__":
    app.run(debug=False)
