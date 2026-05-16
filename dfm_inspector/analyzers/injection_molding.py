"""Injection Molding DFM Analyzer based on 930-00164_R01."""
from typing import Dict


def analyze_injection_molding(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []

    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)
    mat = material.lower()

    # Material-specific wall thickness
    min_walls = {"abs": (1.0, 3.5), "polycarbonate": (1.0, 4.0), "nylon": (0.75, 3.0),
                 "pp": (0.8, 3.5), "peek": (1.0, 3.0)}
    min_w, max_w = (1.0, 4.0)
    for key, val in min_walls.items():
        if key in mat:
            min_w, max_w = val
            break

    # RULE 1: Wall Thickness
    std = f"Min: {min_w}mm, Max: {max_w}mm. Uniform ±10% to prevent warping"
    if min_thickness > 0:
        if min_thickness < min_w:
            issues.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm below {min_w}mm"})
            rationale.append(f"❌ Wall {min_thickness:.2f}mm below minimum for {material}.")
            all_rules.append(_rule("Wall Thickness", std, "FAIL", f"{min_thickness:.2f}mm",
                                   f"Below {min_w}mm minimum - short shots likely",
                                   f"Increase to ≥{min_w}mm for {material}",
                                   "Thin walls cause short shots (incomplete fill) and high injection pressure.",
                                   "Part will not fill reliably - mold modification required"))
        elif min_thickness > max_w:
            warnings.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm thick - sink marks likely"})
            rationale.append(f"⚠️ Wall {min_thickness:.2f}mm exceeds optimal - sink marks and warping risk.")
            all_rules.append(_rule("Wall Thickness", std, "WARNING", f"{min_thickness:.2f}mm",
                                   f"Exceeds {max_w}mm optimal - sink marks and long cycle time",
                                   "Core out thick sections, use ribs instead of solid walls",
                                   "Thick sections cool slowly causing sink marks, voids, and warping. Cycle time increases.",
                                   "Cycle time +30-50%. Sink marks may require texture to hide"))
        else:
            passed.append({"check": "Wall Thickness", "status": f"{min_thickness:.2f}mm - Optimal"})
            rationale.append(f"✓ Wall {min_thickness:.2f}mm optimal for {material}.")
            all_rules.append(_rule("Wall Thickness", std, "PASS", f"{min_thickness:.2f}mm",
                                   "Within optimal range for material", "No changes needed",
                                   "Good fill, minimal sink marks, reasonable cycle time.", "Standard cost"))

    # RULE 2: Draft Angle
    warnings.append({"category": "Draft Angle", "message": "Minimum 1° draft required (3° for textured)"})
    rationale.append("⚠️ All surfaces need ≥1° draft (≥3° if textured).")
    all_rules.append(_rule("Draft Angle", "Min 1° smooth, 3° textured. Add 1° per 0.025mm texture depth", "WARNING",
                           "≥1° required (cannot verify from mesh)",
                           "Draft angles critical for part ejection",
                           "Apply ≥1° to all surfaces. Add 1° per 0.025mm texture depth",
                           "No draft causes ejector pin marks, scratches, and part sticking. Mold damage risk.",
                           "No draft: mold rework $5K-20K. Proper draft: standard"))

    # RULE 3: Rib Design
    if min_thickness > 0:
        rib_thickness = min_thickness * 0.6
        rib_height = min_thickness * 3
        suggestions.append({"opportunity": f"Rib thickness: {rib_thickness:.2f}mm (60% of wall)",
                           "savings": "Prevents sink marks opposite ribs", "difficulty": "Easy"})
        all_rules.append(_rule("Rib Design", "Thickness: 50-60% of wall. Height: ≤3× wall. Draft: 0.5-1°/side", "INFO",
                               f"Rib: {rib_thickness:.2f}mm thick, ≤{rib_height:.1f}mm tall",
                               "Ribs must be thinner than walls to prevent sink marks",
                               f"Keep ribs ≤{rib_thickness:.2f}mm thick with ≥0.5° draft per side",
                               "Ribs thicker than 60% of wall cause visible sink marks on opposite surface.",
                               "Proper ribs: no sink. Thick ribs: texture needed to hide sinks (+$2K-5K)"))

    # RULE 4: Undercuts
    suggestions.append({"opportunity": "Eliminate undercuts to simplify mold",
                       "savings": "$5,000-$15,000 per action eliminated", "difficulty": "Medium"})
    all_rules.append(_rule("Undercuts / Side Actions", "Avoid where possible. Each adds $5K-15K to mold", "INFO",
                           "Cannot detect from mesh",
                           "Undercuts require side actions, lifters, or collapsing cores",
                           "Redesign for straight pull. Use snap-fits or living hinges instead",
                           "Each side action adds $5K-15K to mold cost and increases maintenance.",
                           "Each action: +$5K-15K mold cost, +2-4s cycle time"))

    # RULE 5: Gate Location
    all_rules.append(_rule("Gate Location", "Gate at thickest section. Away from cosmetic surfaces", "INFO",
                           "N/A", "Gate placement affects fill pattern and cosmetics",
                           "Place gate at thickest wall section, away from visible surfaces",
                           "Gate at thin section causes hesitation and short shots. Gate vestige visible on cosmetic surfaces.",
                           "Proper gating: standard. Regate mold: $2K-8K"))

    # RULE 6: Shrinkage
    shrinkage = {"abs": 0.5, "polycarbonate": 0.6, "nylon": 1.5, "pp": 1.5, "peek": 1.0}.get(
        next((k for k in ["abs", "polycarbonate", "nylon", "pp", "peek"] if k in mat), "abs"), 0.5)
    all_rules.append(_rule("Shrinkage Allowance", f"Material shrinkage: ~{shrinkage}%", "INFO",
                           f"~{shrinkage}% for {material}",
                           "Mold must be oversized to compensate for material shrinkage",
                           f"Apply {shrinkage}% shrinkage factor to all dimensions",
                           "Incorrect shrinkage compensation causes out-of-tolerance parts.",
                           "Correct: standard. Wrong: mold rework $5K-20K"))

    score = _calc_score(issues, warnings, passed)
    return {
        "success": True, "process": "Injection Molding", "material": material, "score": score,
        "score_explanation": f"Based on {len(passed)} passed, {len(warnings)} warnings, {len(issues)} issues",
        "issues": len(issues), "warnings": len(warnings), "suggestions": len(suggestions), "passed": len(passed),
        "all_rules": all_rules,
        "geometry_info": {"dimensions": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm",
                         "min_thickness": f"{min_thickness:.2f} mm"},
        "summary": f"**Injection Molding Analysis** | Score: {score}/100 | {len(issues)} issues, {len(warnings)} warnings",
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
