from flask import Flask, render_template, request

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
    return render_template(
        "index.html",
        values=request.form,
        errors={},
        results=results,
        region=region,
        warnings=warnings,
    )


if __name__ == "__main__":
    app.run(debug=False)
