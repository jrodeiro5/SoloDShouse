"""Static GPU TDP lookup table (Thermal Design Power, watts).

Source: manufacturer spec sheets + MLPerf submission system descriptions.
Used by mlperf_bronze_to_silver to compute Wh/million-tokens efficiency metric.
"""

from __future__ import annotations

# Maps canonical GPU family keywords (lowercase) → TDP in watts.
# Match order: first hit wins, so put more specific strings first.
_TDP_TABLE: list[tuple[str, float]] = [
    ("h100 sxm5", 700.0),
    ("h100 sxm", 700.0),
    ("h100 nvl", 400.0),
    ("h100 pcie", 350.0),
    ("h100", 700.0),          # fallback for unspecified H100
    ("h200 sxm", 700.0),
    ("h200", 700.0),
    ("a100 sxm4 80", 400.0),
    ("a100 sxm4 40", 400.0),
    ("a100 sxm", 400.0),
    ("a100 pcie 80", 300.0),
    ("a100 pcie", 300.0),
    ("a100", 400.0),          # fallback
    ("a10g", 150.0),
    ("a10", 150.0),
    ("t4", 70.0),
    ("v100 sxm2", 300.0),
    ("v100 pcie", 250.0),
    ("v100", 300.0),
    ("l40s", 350.0),
    ("l40", 300.0),
    ("l4", 72.0),
    ("rtx 4090", 450.0),
    ("rtx 4080", 320.0),
    ("mi300x", 750.0),
    ("mi300", 750.0),
    ("mi250x", 500.0),
    ("gaudi2", 600.0),
    ("gaudi", 600.0),
]

_UNKNOWN_TDP = float("nan")


def get_tdp(accelerator_name: str) -> float:
    """Return TDP watts for *accelerator_name*, or NaN if unknown.

    Matching is case-insensitive substring; first match in _TDP_TABLE wins.
    """
    lower = accelerator_name.lower()
    for keyword, tdp in _TDP_TABLE:
        if keyword in lower:
            return tdp
    return _UNKNOWN_TDP
