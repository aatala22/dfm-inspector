"""Welding DFM Analyzer based on 960-00169_R01 and AWS D1.x standards."""
from typing import Dict


def analyze_welding(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []

    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)
    mat = material.lower()

    # RULE 1: Material Thickness per AWS
    std_thick = "AWS D1.1: ≥3mm steel. D1.3: <5mm sheet steel. D1.6: ≥1.5mm stainless"
    if min_thickness > 0:
        if min_thickness < 1.5:
            issues.append({"category": "Thickness", "message": f"{min_thickness:.2f}mm too thin for welding"})
            rationale.append(f"❌ Thickness {min_thickness:.2f}mm below AWS minimum.")
            all_rules.append(_rule("Material Thickness (AWS)", std_thick, "FAIL", f"{min_thickness:.2f}mm",
                                   "Below minimum for reliable welding", "Increase to ≥1.5mm (stainless) or ≥3mm (steel)",
                                   "Thin material burns through during welding. AWS D1.6 minimum is 1.5mm.",
                                   "Parts will be rejected or require specialized micro-welding"))
        elif min_thickness < 3.0 and "steel" in mat and "stainless" not in mat:
            warnings.append({"category": "Thickness", "message": f"{min_thickness:.2f}mm - use AWS D1.3 (sheet steel)"})
            rationale.append(f"⚠️ Thickness {min_thickness:.2f}mm falls under AWS D1.3 sheet steel code.")
            all_rules.append(_rule("Material Thickness (AWS)", std_thick, "WARNING", f"{min_thickness:.2f}mm",
                                   "Sheet steel range - requires D1.3 procedures", "Verify WPS per AWS D1.3",
                                   "Sheet steel <5mm requires specific procedures to prevent burn-through.",
                                   "May require pulsed welding (+10-20% cost)"))
        else:
            passed.append({"check": "Material Thickness", "status": f"{min_thickness:.2f}mm - Adequate"})
            rationale.append(f"✓ Thickness {min_thickness:.2f}mm adequate for welding.")
            all_rules.append(_rule("Material Thickness (AWS)", std_thick, "PASS", f"{min_thickness:.2f}mm",
                                   "Meets AWS minimum requirements", "No changes needed",
                                   "Sufficient material for full-penetration welds.", "Standard cost"))

    # RULE 2: Groove Angle
    groove_angles = {"steel": "50-60°", "aluminum": "60-65°", "stainless": "55-60°"}
    angle_rec = groove_angles.get("aluminum" if "aluminum" in mat else "stainless" if "stainless" in mat else "steel", "50-60°")
    suggestions.append({"opportunity": f"Groove angle: {angle_rec}", "savings": "Proper fusion", "difficulty": "Easy"})
    all_rules.append(_rule("Groove Angle", f"Steel: 50-60°, Aluminum: 60-65°, Stainless: 55-60°", "INFO",
                           f"Recommended: {angle_rec}",
                           "Groove angle affects weld penetration and filler consumption",
                           f"Use {angle_rec} groove angle for {material}",
                           "Too narrow: lack of fusion. Too wide: excessive filler, distortion, cost.",
                           "Proper angle minimizes filler consumption (10-30% savings)"))

    # RULE 3: Weld Access
    warnings.append({"category": "Weld Access", "message": "Verify gun/torch access to all joints"})
    rationale.append("⚠️ Verify adequate weld access - gun angle and visibility critical.")
    all_rules.append(_rule("Weld Access", "Min 45° gun angle, clear line of sight to joint", "WARNING",
                           "Cannot verify from geometry alone",
                           "Weld access must be verified in assembly context",
                           "Ensure 45° minimum gun angle and arc visibility at all joints",
                           "Poor access causes defects (porosity, lack of fusion). Rework costs $50-200/joint.",
                           "Inaccessible joints require redesign or manual welding (+100-200%)"))

    # RULE 4: Joint Design
    all_rules.append(_rule("Joint Design", "CJP for structural, PJP/fillet for non-critical", "INFO",
                           "N/A", "Joint type selection affects strength and cost",
                           "Use fillet welds where possible (50% cheaper than groove welds)",
                           "CJP groove welds require back-gouging and are 2× cost of fillet welds.",
                           "Fillet welds: standard cost. CJP: 2× cost. Back-gouging: +$10-30/ft"))

    # RULE 5: Distortion Control
    suggestions.append({"opportunity": "Design for distortion control",
                       "savings": "Prevents rework (straightening costs $20-100/part)", "difficulty": "Medium"})
    all_rules.append(_rule("Distortion Control", "Balanced welds, staggered sequence, minimum weld size", "INFO",
                           "N/A", "Welding causes thermal distortion - design must account for it",
                           "Use balanced weld placement, staggered sequence, and minimum effective weld size",
                           "Unbalanced welds cause bowing/twisting. Straightening adds $20-100/part.",
                           "Good design: no rework. Poor design: $20-100/part straightening"))

    # RULE 6: Drain/Outgassing Holes
    suggestions.append({"opportunity": "Add drain holes for enclosed weldments",
                       "savings": "Prevents porosity and coating failures", "difficulty": "Easy"})
    all_rules.append(_rule("Drain & Outgassing Holes", "Required for all-around welds and enclosed sections", "INFO",
                           "N/A", "Enclosed sections trap air/moisture causing porosity",
                           "Add 6-10mm drain holes in enclosed sections before welding",
                           "Trapped air expands during welding causing porosity. Moisture causes hydrogen cracking.",
                           "Drain holes: $1-2/hole. Rework porosity: $50-200/joint"))

    score = _calc_score(issues, warnings, passed)
    return {
        "success": True, "process": "Welding", "material": material, "score": score,
        "score_explanation": f"Based on {len(passed)} passed, {len(warnings)} warnings, {len(issues)} issues",
        "issues": len(issues), "warnings": len(warnings), "suggestions": len(suggestions), "passed": len(passed),
        "all_rules": all_rules,
        "geometry_info": {"dimensions": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm",
                         "min_thickness": f"{min_thickness:.2f} mm"},
        "summary": f"**Welding Analysis (AWS D1.x)** | Score: {score}/100 | {len(issues)} issues, {len(warnings)} warnings",
        "rationale": rationale,
        "details": {"critical_issues": issues[:5], "warnings": warnings[:5], "cost_savings": suggestions[:3]},
    }


def _rule(name, standard, status, measured, evaluation, recommendation, rationale, cost_impact):
    return {"name": name, "standard": standard, "status": status, "measured_value": measured,
            "evaluation": evaluation, "recommendation": recommendation, "rationale": rationale,
            "cost_impact": cost_impact}


def _calc_score(issues, warnings, passed):
    total = len(issues) + len(warnings) + len(passed)
    return round((len(passed) * 100 + len(warnings) * 50) / total, 1) if total else 75.0
