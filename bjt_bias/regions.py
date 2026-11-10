"""Cutoff / active / saturation classification for the bias point."""
import math
from typing import Mapping

SATURATION_VCE_V = 0.3

CAVEAT = (
    "ผลนี้มาจาก forward-active approximation (β และ VBE คงที่) "
    "ไม่ใช่ผลจำลองที่แม่นยำ"
)
WARNING_CUTOFF = (
    "ทรานซิสเตอร์อยู่ในช่วง cutoff (VTH ≤ VBE คือแรงดันจากตัวแบ่ง R1/R2 "
    "ที่ base ต่ำกว่า VBE, IB ≈ 0) — " + CAVEAT
)
WARNING_SATURATION = (
    "ทรานซิสเตอร์อยู่ในช่วง saturation (VCE < 0.3 V) "
    "ค่า Q-point ใช้เป็นแอมพลิฟายเออร์ไม่ได้ — " + CAVEAT
)
WARNING_INVALID = "ค่าผิดปกติ: ผลลัพธ์ไม่ใช่จำนวนจริง (ตรวจสอบค่าอินพุต)"


def classify(op: Mapping[str, float]) -> tuple[str, list[str]]:
    """Return the region name and any warning messages."""
    if not (math.isfinite(op["ib"]) and math.isfinite(op["vce"])):
        return "invalid", [WARNING_INVALID]
    if op["ib"] <= 0:
        return "cutoff", [WARNING_CUTOFF]
    if op["vce"] < SATURATION_VCE_V:
        return "saturation", [WARNING_SATURATION]
    return "active", []
