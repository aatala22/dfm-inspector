"""Sheet Metal DFM Analyzer based on 930-00172_R01."""
from typing import Dict


def analyze_sheet_metal(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []

    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)

    # RULE 1: Material Thickness
    _check_thickness(min_thickness, issues, warnings, passed, all_rules, rationale)

    # RULE 2: Part Size
    _check_size(dims, warnings, passed, all_rules, rationale)

    # RULE 3: Material Formability
    _check_formability(material, warnings, passed, all_rules, rationale)

    # RULE 4: Bend Radius
    if min_thickness > 0:
        min_bend = min_thickness * 1.0
        warnings.append({"category": "Bend Radius", "message": f"Min bend radius: {min_bend:.2f}mm (1× thickness)"})
        rationale.append(f"⚠️ Minimum bend radius: {min_bend:.2f}mm (1× material thickness).")
        all_rules.append(_rule("Minimum Bend Radius", "≥1× material thickness (steel), ≥1.5× (aluminum)", "WARNING",
                               f"{min_bend:.2f}mm for {min_thickness:.2f}mm material",
                               "Verify all bends meet minimum radius requirement",
                               f"Use ≥{min_bend:.2f}mm bend radius to prevent cracking",
                               "Bends tighter than 1× thickness crack on the outside surface.",
                               "Standard tooling if using common radii (0.76mm, 1.5mm, 3.0mm)"))

    # RULE 5: Hole-to-Edge Distance
    if min_thickness > 0:
        min_edge = max(2 * min_thickness, 2.5)
        warnings.append({"category": "Hole-to-Edge", "message": f"Min distance: {min_edge:.1f}mm"})
        rationale.append(f"⚠️ Holes must be ≥{min_edge:.1f}mm from edges.")
        all_rules.append(_rule("Hole-to-Edge Distance", "≥2× thickness or 2.5mm minimum", "WARNING",
                               f"≥{min_edge:.1f}mm required",
                               "Verify all holes maintain adequate edge distance",
                               f"Keep holes ≥{min_edge:.1f}mm from edges and bends",
                               "Holes too close to edges deform during bending or punching.",
                               "Rework cost if holes deform: $5-20 per part"))

    # RULE 6: Flange Length
    if min_thickness > 0:
        min_flange = max(4 * min_thickness, 12.7)
        suggestions.append({"opportunity": f"Minimum flange length: {min_flange:.1f}mm",
                           "savings": "Prevents tooling issues", "difficulty": "Easy"})
        all_rules.append(_rule("Minimum Flange Length", "≥4× thickness or 12.7mm (0.5\") minimum", "INFO",
                               f"≥{min_flange:.1f}mm required",
                               "Short flanges cannot be gripped by press brake tooling",
                               f"Maintain ≥{min_flange:.1f}mm flange length",
                               "Press brake V-die requires material to extend past the die shoulder.",
                               "Short flanges require special tooling ($500-2000)"))

    # RULE 7: Cost Optimization
    suggestions.append({"opportunity": "Use standard bend radius (0.76mm or 1.5mm)",
                       "savings": "Eliminates custom tooling ($2,000-$5,000)", "difficulty": "Easy"})
    suggestions.append({"opportunity": "Standardize hole sizes to common punches",
                       "savings": "20-30% by using turret punch vs drilling", "difficulty": "Easy"})

    score = _calc_score(issues, warnings, passed)
    return _build_result("Sheet Metal", material, score, issues, warnings, suggestions, passed,
                         all_rules, rationale, geometry)


def _check_thickness(t, issues, warnings, passed, all_rules, rationale):
    std = "Min 0.5mm (20ga steel), 0.8mm aluminum. Optimal: 0.9-3.0mm"
    if t <= 0:
        all_rules.append(_rule("Material Thickness", std, "INFO", "Not measured",
                               "Could not measure", "Verify manually", "N/A", "N/A"))
        return
    if t < 0.5:
        issues.append({"category": "Thickness", "message": f"{t:.2f}mm too thin for bending"})
        rationale.append(f"❌ Thickness {t:.2f}mm below minimum for sheet metal.")
        all_rules.append(_rule("Material Thickness", std, "FAIL", f"{t:.2f}mm",
                               "Below minimum - tears during bending", "Increase to ≥0.5mm (steel) or ≥0.8mm (aluminum)",
                               "Material <0.5mm tears during bending and distorts under forming pressure.",
                               "150-200% premium for micro-forming"))
    elif t < 0.9:
        warnings.append({"category": "Thickness", "message": f"{t:.2f}mm thin but workable"})
        rationale.append(f"⚠️ Thickness {t:.2f}mm requires careful handling.")
        all_rules.append(_rule("Material Thickness", std, "WARNING", f"{t:.2f}mm",
                               "Thin material - requires careful handling", "Consider 0.9mm+ for easier fabrication",
                               "Thin material (0.5-0.9mm) is prone to distortion and requires slower forming.",
                               "20-30% cost premium"))
    else:
        passed.append({"check": "Material Thickness", "status": f"{t:.2f}mm - Good"})
        rationale.append(f"✓ Thickness {t:.2f}mm optimal for sheet metal.")
        all_rules.append(_rule("Material Thickness", std, "PASS", f"{t:.2f}mm",
                               "Within optimal range", "No changes needed",
                               "0.9-6.0mm provides good formability with standard equipment.", "Standard cost"))


def _check_size(dims, warnings, passed, all_rules, rationale):
    if not dims:
        return
    max_dim = max(dims.values())
    std = "Standard press brake: 1500mm. Large: up to 2500mm"
    if max_dim > 2500:
        warnings.append({"category": "Part Size", "message": f"Oversized: {max_dim:.1f}mm"})
        rationale.append(f"❌ Part {max_dim:.1f}mm exceeds press brake capacity.")
        all_rules.append(_rule("Part Size", std, "FAIL", f"{max_dim:.1f}mm",
                               "Exceeds standard capacity", "Split into welded assembly",
                               "Parts >2500mm require specialized equipment.", "200-400% cost increase"))
    elif max_dim > 1500:
        warnings.append({"category": "Part Size", "message": f"Large: {max_dim:.1f}mm"})
        rationale.append(f"⚠️ Part {max_dim:.1f}mm requires large press brake.")
        all_rules.append(_rule("Part Size", std, "WARNING", f"{max_dim:.1f}mm",
                               "Requires large-format press brake", "Verify fabricator capacity",
                               "Reduces shop options by 40-50%.", "30-50% cost premium"))
    else:
        passed.append({"check": "Part Size", "status": "Fits standard equipment"})
        rationale.append(f"✓ Part fits standard press brake.")
        all_rules.append(_rule("Part Size", std, "PASS", f"{max_dim:.1f}mm",
                               "Within standard capacity", "No changes needed",
                               "Maximum shop compatibility.", "Standard cost"))


def _check_formability(material, warnings, passed, all_rules, rationale):
    mat = material.lower()
    std = "5052-H32 aluminum or mild steel recommended"
    if "6061" in mat:
        warnings.append({"category": "Formability", "message": "6061 has limited formability"})
        rationale.append("⚠️ 6061 aluminum prone to cracking at bends.")
        all_rules.append(_rule("Material Formability", std, "WARNING", material,
                               "6061-T6 has poor formability (8% elongation)", "Use 5052-H32 or anneal before forming",
                               "6061-T6 cracks at tight bend radii. 5052-H32 has 25% elongation.",
                               "20-30% scrap rate if formed in T6 condition"))
    elif "5052" in mat:
        passed.append({"check": "Material", "status": "Excellent formability"})
        rationale.append("✓ 5052 aluminum - excellent formability.")
        all_rules.append(_rule("Material Formability", std, "PASS", material,
                               "Excellent formability (25% elongation)", "Optimal choice",
                               "Industry standard for sheet metal fabrication.", "Standard cost"))
    elif "stainless" in mat:
        warnings.append({"category": "Formability", "message": "Stainless needs larger bend radii"})
        rationale.append("⚠️ Stainless requires 2× thickness bend radius.")
        all_rules.append(_rule("Material Formability", std, "WARNING", material,
                               "Work-hardens during bending", "Use 2× thickness minimum bend radius",
                               "Stainless requires larger radii than mild steel. 20-30% higher forming costs.",
                               "20-30% cost premium vs mild steel"))
    else:
        passed.append({"check": "Material", "status": "Good formability"})
        rationale.append(f"✓ {material} suitable for sheet metal.")
        all_rules.append(_rule("Material Formability", std, "PASS", material,
                               "Good formability", "No changes needed",
                               "Material is suitable for standard forming operations.", "Standard cost"))


def _rule(name, standard, status, measured, evaluation, recommendation, rationale, cost_impact):
    return {"name": name, "standard": standard, "status": status, "measured_value": measured,
            "evaluation": evaluation, "recommendation": recommendation, "rationale": rationale,
            "cost_impact": cost_impact}


def _calc_score(issues, warnings, passed):
    total = len(issues) + len(warnings) + len(passed)
    return round((len(passed) * 100 + len(warnings) * 50) / total, 1) if total else 75.0


def _build_result(process, material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry):
    dims = geometry.get("dimensions", {})
    return {
        "success": True, "process": process, "material": material, "score": score,
        "score_explanation": f"Based on {len(passed)} passed, {len(warnings)} warnings, {len(issues)} issues",
        "issues": len(issues), "warnings": len(warnings), "suggestions": len(suggestions), "passed": len(passed),
        "all_rules": all_rules,
        "geometry_info": {"dimensions": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm",
                         "min_thickness": f"{geometry.get('estimated_min_thickness',0):.2f} mm"},
        "summary": f"**Sheet Metal Analysis** | Score: {score}/100 | {len(issues)} issues, {len(warnings)} warnings, {len(passed)} passed",
        "rationale": rationale,
        "details": {"critical_issues": issues[:5], "warnings": warnings[:5], "cost_savings": suggestions[:3]},
    }
