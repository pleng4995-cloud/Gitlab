"""Cutoff / active / saturation classification for the bias point."""
from typing import Mapping

SATURATION_VCE_V = 0.3

WARNING_CUTOFF = "ทรานซิสเตอร์อยู่ในช่วง cutoff (IB ≈ 0)"
WARNING_SATURATION = (
    "ทรานซิสเตอร์อยู่ในช่วง saturation (VCE < 0.3 V) "
    "ค่า Q-point ใช้เป็นแอมพลิฟายเออร์ไม่ได้"
)


def classify(op: Mapping[str, float]) -> tuple[str, list[str]]:
    """Return the region name and any warning messages."""
    if op["ib"] <= 0:
        return "cutoff", [WARNING_CUTOFF]
    if op["vce"] < SATURATION_VCE_V:
        return "saturation", [WARNING_SATURATION]
    return "active", []
