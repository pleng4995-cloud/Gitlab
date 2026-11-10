"""Closed-form DC operating point of a voltage-divider biased CE stage."""
from .params import BiasInputs


def operating_point(inputs: BiasInputs) -> dict[str, float]:
    """Solve the bias point with the standard textbook formulas."""
    vbb = inputs.vcc * inputs.r2 / (inputs.r1 + inputs.r2)
    rb = inputs.r1 * inputs.r2 / (inputs.r1 + inputs.r2)

    ib = (vbb - inputs.vbe) / (rb + (1 + inputs.beta) * inputs.re)
    if ib <= 0:
        return {
            "vbb": vbb, "rb": rb,
            "ib": 0.0, "ic": 0.0, "ie": 0.0,
            "vb": vbb, "vc": inputs.vcc, "ve": 0.0, "vce": inputs.vcc,
        }

    ic = inputs.beta * ib
    ie = (1 + inputs.beta) * ib
    ve = ie * inputs.re
    vc = inputs.vcc - ic * inputs.rc
    return {
        "vbb": vbb, "rb": rb,
        "ib": ib, "ic": ic, "ie": ie,
        "vb": inputs.vbe + ve, "vc": vc, "ve": ve, "vce": vc - ve,
    }
