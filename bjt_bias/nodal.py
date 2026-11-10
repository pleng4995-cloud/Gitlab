"""Independent nodal-analysis solution of the same bias circuit.

Unknowns are the node voltages VB, VC, VE and the base current IB. The BJT is
modelled as a fixed VBE source plus a current-controlled current source
IC = beta * IB, so the solution comes from KCL alone and never reuses the
closed-form algebra in ``operating_point``.
"""
from .params import BiasInputs


def _solve(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting."""
    size = len(matrix)
    rows = [list(row) + [rhs[index]] for index, row in enumerate(matrix)]

    for column in range(size):
        pivot = max(range(column, size), key=lambda r: abs(rows[r][column]))
        if rows[pivot][column] == 0:
            raise ValueError("singular system")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        for row in range(column + 1, size):
            factor = rows[row][column] / rows[column][column]
            for k in range(column, size + 1):
                rows[row][k] -= factor * rows[column][k]

    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        total = rows[row][size] - sum(
            rows[row][k] * solution[k] for k in range(row + 1, size)
        )
        solution[row] = total / rows[row][row]
    return solution


def nodal_operating_point(inputs: BiasInputs) -> dict[str, float]:
    """Solve KCL at B, C, E plus VB - VE = VBE."""
    conductance_divider = 1 / inputs.r1 + 1 / inputs.r2
    matrix = [
        [conductance_divider, 0.0, 0.0, 1.0],
        [0.0, 1 / inputs.rc, 0.0, inputs.beta],
        [0.0, 0.0, 1 / inputs.re, -(1 + inputs.beta)],
        [1.0, 0.0, -1.0, 0.0],
    ]
    rhs = [
        inputs.vcc / inputs.r1,
        inputs.vcc / inputs.rc,
        0.0,
        inputs.vbe,
    ]

    vb, vc, ve, ib = _solve(matrix, rhs)
    ic = inputs.beta * ib
    ie = (1 + inputs.beta) * ib
    return {
        "ib": ib, "ic": ic, "ie": ie,
        "vb": vb, "vc": vc, "ve": ve, "vce": vc - ve,
    }
