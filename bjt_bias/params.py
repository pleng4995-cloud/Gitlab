"""Validation of the seven bias inputs."""
import math
from dataclasses import dataclass
from typing import Mapping

FIELD_ORDER = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
POSITIVE_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta")

MSG_NUMBER = "กรุณากรอกตัวเลข"
MSG_POSITIVE = "ต้องมากกว่า 0"
MSG_VBE_RANGE = "ต้องอยู่ระหว่าง 0 ถึง VCC"


@dataclass(frozen=True)
class BiasInputs:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


def validate(raw: Mapping[str, str]) -> tuple[BiasInputs | None, dict[str, str]]:
    """Parse and validate a form mapping.

    Returns ``(inputs, {})`` when every field is valid, otherwise
    ``(None, errors)`` with one Thai message per invalid field.
    """
    values: dict[str, float] = {}
    errors: dict[str, str] = {}

    for field in FIELD_ORDER:
        text = str(raw.get(field, "")).strip()
        if not text:
            errors[field] = MSG_NUMBER
            continue
        try:
            value = float(text)
        except ValueError:
            errors[field] = MSG_NUMBER
            continue
        if not math.isfinite(value):
            errors[field] = MSG_NUMBER
            continue
        values[field] = value

    for field in POSITIVE_FIELDS:
        if field in values and values[field] <= 0:
            errors[field] = MSG_POSITIVE

    vbe = values.get("vbe")
    vcc = values.get("vcc")
    if vbe is not None:
        if vbe < 0 or (vcc is not None and vbe >= vcc):
            errors["vbe"] = MSG_VBE_RANGE

    if errors:
        return None, errors

    return BiasInputs(**{field: values[field] for field in FIELD_ORDER}), {}
