"""Assumption loading and case selection.

The YAML in ``smrtwin/assumptions`` stores many parameters as ``[low, central, high]``
triplets.  :func:`resolve` collapses every triplet to a scalar for a chosen *case*
(``0`` = low, ``1`` = central, ``2`` = high), optionally with per-block overrides so
that, e.g., CAPEX can be "high" while prices are "central".
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping

import yaml

ASSUMPTIONS_DIR = Path(__file__).resolve().parent / "assumptions"
CASE_INDEX = {"low": 0, "central": 1, "high": 2, 0: 0, 1: 1, 2: 2}

# Keys whose 3-lists are *paths* over anchor years, not low/central/high triplets.
_PATH_KEYS = {"anchor_years", "low", "central", "high", "spend_profile", "spend_profile_5yr"}


def load_raw(name: str = "default") -> dict:
    with open(ASSUMPTIONS_DIR / f"{name}.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _is_triplet(v: Any) -> bool:
    return isinstance(v, list) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v)


def _resolve_block(node: Any, case: int, key: str | None = None) -> Any:
    if isinstance(node, dict):
        # price/gas/eua paths: select the case-named list
        if "anchor_years" in node and all(k in node for k in ("low", "central", "high")):
            pick = ["low", "central", "high"][case]
            return {"anchor_years": list(node["anchor_years"]), "values": list(node[pick])}
        return {k: _resolve_block(v, case, k) for k, v in node.items()}
    if isinstance(node, list):
        if key in _PATH_KEYS:
            return list(node)
        if _is_triplet(node):
            return node[case]
        return [_resolve_block(x, case) for x in node]
    return node


def resolve(raw: Mapping | None = None, case: str | int = "central",
            overrides: Mapping[str, str | int] | None = None,
            edits: Mapping[str, Any] | None = None) -> dict:
    """Return a fully scalar assumption dict.

    Parameters
    ----------
    case : default case for all blocks.
    overrides : mapping of top-level block name (``market``, ``smr``, ``gas``, ``macro``, ``tax``)
        to a case, e.g. ``{"smr": "high", "market": "low"}``.
    edits : dotted-path point edits applied after resolution, e.g. ``{"smr.capex_pln_per_kw": 45000}``.
    """
    raw = copy.deepcopy(raw if raw is not None else load_raw())
    overrides = overrides or {}
    out: dict[str, Any] = {}
    for block, node in raw.items():
        c = CASE_INDEX[overrides.get(block, case)]
        out[block] = _resolve_block(node, c, block)
    for path, val in (edits or {}).items():
        d = out
        parts = path.split(".")
        for p in parts[:-1]:
            d = d[p]
        d[parts[-1]] = val
    out["_case"] = {"default": case, **overrides}
    return out


def path_value(path: Mapping, year: float) -> float:
    """Piecewise-linear interpolation of an anchor-year path (flat outside)."""
    import numpy as np

    xs, ys = path["anchor_years"], path["values"]
    return float(np.interp(year, xs, ys))
