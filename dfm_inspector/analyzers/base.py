"""Base analyzer utilities and dispatcher."""

from typing import Dict
from . import cnc, sheet_metal, welding, die_casting, injection_molding, other

_DISPATCH = {
    "cnc_machining": cnc.analyze_cnc,
    "sheet_metal": sheet_metal.analyze_sheet_metal,
    "welding": welding.analyze_welding,
    "die_casting": lambda g, m: die_casting.analyze_die_casting(g, m, "hpdc"),
    "lpdc": lambda g, m: die_casting.analyze_die_casting(g, m, "lpdc"),
    "permanent_mold": lambda g, m: die_casting.analyze_die_casting(g, m, "gravity"),
    "injection_molding": injection_molding.analyze_injection_molding,
    "investment_casting": other.analyze_investment_casting,
    "mim": other.analyze_mim,
    "rotational_molding": other.analyze_rotational_molding,
    "wire_forming": other.analyze_wire_forming,
    "vacuum_forming": other.analyze_vacuum_forming,
}


def analyze(geometry: Dict, material: str, process: str) -> Dict:
    """Run DFM analysis for the given process."""
    fn = _DISPATCH.get(process)
    if not fn:
        return _generic_result(geometry, material, process)
    return fn(geometry, material)


def _generic_result(geometry: Dict, material: str, process: str) -> Dict:
    dims = geometry.get("dimensions", {})
    return {
        "success": True,
        "process": process,
        "material": material,
        "score": 75.0,
        "score_explanation": "Generic analysis - process-specific rules not yet implemented",
        "issues": 0,
        "warnings": 0,
        "suggestions": 0,
        "passed": 1,
        "all_rules": [{
            "name": "Basic Geometry Check",
            "standard": "General DFM guidelines",
            "status": "PASS",
            "measured_value": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm",
            "evaluation": "Part geometry loaded successfully",
            "recommendation": "Review process-specific guidelines manually",
            "rationale": "Automated rules for this process are under development.",
            "cost_impact": "N/A",
        }],
        "geometry_info": {"dimensions": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm"},
        "summary": f"Part analyzed for {process}. Review manually for process-specific requirements.",
        "rationale": ["Part geometry loaded successfully."],
        "details": {"critical_issues": [], "warnings": [], "cost_savings": []},
    }
