"""Azure instance → GPU accelerator mapping.

Maps Azure VM SKU names to canonical accelerator names that match MLPerf
submission strings, plus GPU count per instance for TDP scaling.
Used by pricing_bronze_to_silver to populate the accelerator column.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstanceGPU:
    accelerator: str   # canonical name matching MLPerf strings
    gpu_count: int     # GPUs per instance (TDP = gpu_count * per_gpu_tdp)


# Azure NC/ND/NV series → GPU mapping.
# SKU matching: case-insensitive substring, first match wins.
_AZURE_MAP: list[tuple[str, InstanceGPU]] = [
    # H100 series
    ("nd96isr_h100_v5",   InstanceGPU("NVIDIA H100 SXM5 80GB", 8)),
    ("nd96isrv5",         InstanceGPU("NVIDIA H100 SXM5 80GB", 8)),
    # A100 series
    ("nd96amsr_a100_v4",  InstanceGPU("NVIDIA A100 SXM4 80GB", 8)),
    ("nd96asr_v4",        InstanceGPU("NVIDIA A100 SXM4 40GB", 8)),
    ("nc24ads_a100_v4",   InstanceGPU("NVIDIA A100 PCIe 80GB", 1)),
    ("nc48ads_a100_v4",   InstanceGPU("NVIDIA A100 PCIe 80GB", 2)),
    ("nc96ads_a100_v4",   InstanceGPU("NVIDIA A100 PCIe 80GB", 4)),
    # A10 series
    ("nc6ads_a10_v5",     InstanceGPU("NVIDIA A10", 1)),
    ("nc12ads_a10_v5",    InstanceGPU("NVIDIA A10", 2)),
    ("nc24ads_a10_v5",    InstanceGPU("NVIDIA A10", 4)),
    # V100 series
    ("nd40rs_v2",         InstanceGPU("NVIDIA V100 SXM2 32GB", 8)),
    ("nc6s_v3",           InstanceGPU("NVIDIA V100 PCIe 16GB", 1)),
    ("nc12s_v3",          InstanceGPU("NVIDIA V100 PCIe 16GB", 2)),
    ("nc24s_v3",          InstanceGPU("NVIDIA V100 PCIe 16GB", 4)),
    # T4 series
    ("nc4as_t4_v3",       InstanceGPU("NVIDIA T4", 1)),
    ("nc8as_t4_v3",       InstanceGPU("NVIDIA T4", 1)),
    ("nc16as_t4_v3",      InstanceGPU("NVIDIA T4", 1)),
    ("nc64as_t4_v3",      InstanceGPU("NVIDIA T4", 4)),
]


def get_instance_gpu(sku_name: str) -> InstanceGPU | None:
    """Return GPU info for *sku_name*, or None if unknown.

    Matching is case-insensitive substring; first match wins.
    """
    lower = sku_name.lower().replace("standard_", "").replace("-", "_")
    for keyword, info in _AZURE_MAP:
        if keyword in lower:
            return info
    return None
