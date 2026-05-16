"""Die Casting DFM Analyzer (HPDC, LPDC, Gravity) based on 930-00166_R01."""
from typing import Dict


def analyze_die_casting(geometry: Dict, material: str, process_type: str = "hpdc") -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []

    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)
    volume = geometry.get("volume", 0)
    mat = material.lower()

    process_names = {"hpdc": "Die Casting (HPDC)", "lpdc": "Low Pressure Die Casting", "gravity": "Permanent Mold / Gravity Cast"}
    process_name = process_names.get(process_type, "Die Casting")

    # Wall thickness limits vary by process
    min_walls = {"hpdc": (1.0, 6.0), "lpdc": (2.0, 10.0), "gravity": (3.0, 15.0)}
    min_w, max_w = min_walls.get(process_type, (1.0, 6.0))

    if "zinc" in mat:
        min_w = 0.75  # Zinc allows thinner walls

    # RULE 1: Wall Thickness
    std = f"Min: {min_w}mm, Max: {max_w}mm. Uniform ±10% preferred"
    if min_thickness > 0:
        if min_thickness < min_w:
            issues.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm below {min_w}mm minimum"})
            rationale.append(f"❌ Wall {min_thickness:.2f}mm below {process_type.upper()} minimum of {min_w}mm.")
            all_rules.append(_rule("Wall Thickness", std, "FAIL", f"{min_thickness:.2f}mm",
                                   f"Below {min_w}mm minimum for {process_type.upper()}",
                                   f"Increase to ≥{min_w}mm", "Thin walls cause cold shuts and misruns.",
                                   "Part will not fill - redesign required"))
        elif min_thickness > max_w:
            warnings.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm exceeds {max_w}mm optimal max"})
            rationale.append(f"⚠️ Wall {min_thickness:.2f}mm thick - porosity and sink mark risk.")
            all_rules.append(_rule("Wall Thickness", std, "WARNING", f"{min_thickness:.2f}mm",
                                   f"Exceeds {max_w}mm optimal maximum", "Core out thick sections",
                                   "Thick sections solidify slowly causing shrinkage porosity and long cycle times.",
                                   "Porosity rework: $5-20/part. Longer cycle: +20-40%"))
        else:
            passed.append({"check": "Wall Thickness", "status": f"{min_thickness:.2f}mm - Optimal"})
            rationale.append(f"✓ Wall {min_thickness:.2f}mm within optimal range for {process_type.upper()}.")
            all_rules.append(_rule("Wall Thickness", std, "PASS", f"{min_thickness:.2f}mm",
                                   "Within optimal range", "No changes needed",
                                   "Good fill and solidification characteristics.", "Standard cost"))

    # RULE 2: Draft Angle
    draft_min = {"hpdc": 1.0, "lpdc": 1.5, "gravity": 2.0}[process_type]
    warnings.append({"category": "Draft Angle", "message": f"Minimum {draft_min}° draft required"})
    rationale.append(f"⚠️ All surfaces need ≥{draft_min}° draft for ejection.")
    all_rules.append(_rule("Draft Angle", f"Min {draft_min}° external, {draft_min+1}° internal", "WARNING",
                           f"≥{draft_min}° required (cannot verify from mesh)",
                           "Draft angles cannot be fully verified from triangulated mesh",
                           f"Apply ≥{draft_min}° to all surfaces parallel to die pull direction",
                           "Insufficient draft causes die wear, part sticking, and ejection marks.",
                           f"No draft: die rework $5,000-20,000. Proper draft: standard cost"))

    # RULE 3: Fillet Radii
    min_fillet = {"hpdc": 0.5, "lpdc": 1.0, "gravity": 1.5}[process_type]
    warnings.append({"category": "Fillet Radii", "message": f"Min {min_fillet}mm radii on all corners"})
    all_rules.append(_rule("Fillet Radii", f"Min {min_fillet}mm internal, {min_fillet/2}mm external", "WARNING",
                           f"≥{min_fillet}mm required",
                           "Sharp corners cause hot spots and premature die failure",
                           f"Add ≥{min_fillet}mm radius to all internal corners",
                           "Sharp corners create stress concentrations in the die and turbulent metal flow.",
                           f"Die life with radii: 100K+ shots. Without: 20-50K shots"))

    # RULE 4: Undercuts
    suggestions.append({"opportunity": "Eliminate undercuts to avoid slides",
                       "savings": "$10,000-$25,000 per slide eliminated", "difficulty": "Medium"})
    all_rules.append(_rule("Undercuts / Slides", "Avoid undercuts. Each slide adds $10K-25K to die cost", "INFO",
                           "Cannot detect from mesh",
                           "Undercuts require mechanical slides in the die",
                           "Redesign for straight pull direction where possible",
                           "Each slide adds $10K-25K, increases maintenance, and adds cycle time.",
                           "Each slide: +$10K-25K die cost, +2-5s cycle time"))

    # RULE 5: Material Selection
    if "aluminum" in mat:
        passed.append({"check": "Material", "status": "Good for die casting"})
        all_rules.append(_rule("Material Selection", "A380 most common. A383 for pressure tightness", "PASS",
                               material, "Aluminum is standard die casting material",
                               "Use A380 for best balance of castability and cost",
                               "A380: excellent fluidity, good strength. Avoid wrought alloys (6061/7075).",
                               "Standard material cost"))
    elif "zinc" in mat:
        passed.append({"check": "Material", "status": "Excellent castability"})
        all_rules.append(_rule("Material Selection", "Zamak 3 most common. Thinnest walls possible", "PASS",
                               material, "Zinc offers best castability and tightest tolerances",
                               "Zinc enables 0.75mm walls and ±0.05mm tolerances",
                               "Zamak 3/5: thinnest walls, best finish, tightest tolerances. Lower strength than Al.",
                               "Standard cost. 30-40% better dimensional accuracy than aluminum"))
    else:
        passed.append({"check": "Material", "status": "Acceptable"})
        all_rules.append(_rule("Material Selection", "Verify alloy is die-castable", "PASS",
                               material, "Material appears suitable", "Verify with foundry",
                               "Not all alloys are suitable for die casting.", "Verify with supplier"))

    # RULE 6: Tolerances
    all_rules.append(_rule("Tolerances", "HPDC: ±0.1mm (Al), ±0.05mm (Zn). Machine critical features only", "INFO",
                           "N/A", "As-cast tolerances are process-limited",
                           "Only machine critical features - as-cast finish Ra 1.6-3.2μm",
                           "Tighter tolerances require secondary machining. Only machine what's needed.",
                           "Each machined feature: +$0.50-5.00/part"))

    score = _calc_score(issues, warnings, passed)
    return {
        "success": True, "process": process_name, "material": material, "score": score,
        "score_explanation": f"Based on {len(passed)} passed, {len(warnings)} warnings, {len(issues)} issues",
        "issues": len(issues), "warnings": len(warnings), "suggestions": len(suggestions), "passed": len(passed),
        "all_rules": all_rules,
        "geometry_info": {"dimensions": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm",
                         "min_thickness": f"{min_thickness:.2f} mm"},
        "summary": f"**{process_name} Analysis** | Score: {score}/100 | {len(issues)} issues, {len(warnings)} warnings",
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
