"""CNC Machining DFM Analyzer."""
from typing import Dict


def analyze_cnc(geometry: Dict, material: str) -> Dict:
    """Analyze part for CNC machining manufacturability."""
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []

    dims = geometry.get("dimensions", {})
    volume = geometry.get("volume", 0)
    surface_area = geometry.get("surface_area", 0)
    min_thickness = geometry.get("estimated_min_thickness", 0)

    # RULE 1: Wall Thickness (ISO 2768)
    _check_wall_thickness(min_thickness, material, issues, warnings, passed, all_rules, rationale)

    # RULE 2: Part Size and Machine Capacity
    _check_part_size(dims, issues, warnings, passed, all_rules, rationale)

    # RULE 3: Internal Corner Radii
    _check_corner_radii(dims, warnings, suggestions, all_rules, rationale)

    # RULE 4: Material Machinability
    _check_material(material, warnings, passed, suggestions, all_rules, rationale)

    # RULE 5: Geometry Integrity
    if geometry.get("is_watertight", False):
        passed.append({"check": "Geometry Integrity", "status": "Watertight solid"})
        all_rules.append(_rule("Geometry Integrity", "Watertight solid model required for CAM", "PASS",
                               "Watertight", "Model is valid for CAM programming", "No changes needed",
                               "Non-watertight geometry causes CAM failures.", "Standard cost"))
    else:
        issues.append({"category": "Geometry", "message": "Model has gaps or open surfaces"})
        all_rules.append(_rule("Geometry Integrity", "Watertight solid model required for CAM", "FAIL",
                               "Not watertight", "Model has gaps - will be rejected by machine shops",
                               "Fix geometry to ensure watertight solid", "Open surfaces cannot generate valid toolpaths.",
                               "Part will be rejected - fix before quoting"))

    # RULE 6: Tolerances
    suggestions.append({"opportunity": "Apply ISO 2768-m general tolerances",
                        "savings": "20-30% cost reduction vs tight tolerances everywhere", "difficulty": "Easy"})
    all_rules.append(_rule("Tolerance Specification", "ISO 2768-m: ±0.1mm (<30mm), ±0.2mm (<120mm)", "INFO",
                           "N/A", "Verify only critical features have tight tolerances",
                           "Use ISO 2768-m general tolerances, specify tighter only where needed",
                           "Each tight tolerance adds 15-25% cost due to inspection requirements.", "20-30% savings possible"))

    # RULE 7: Surface Finish
    suggestions.append({"opportunity": "Specify Ra 3.2μm standard finish", "savings": "15-25% vs Ra 1.6μm", "difficulty": "Easy"})
    all_rules.append(_rule("Surface Finish", "Standard: Ra 3.2μm. Fine: Ra 1.6μm (30-50% more)", "INFO",
                           "N/A", "Standard CNC achieves Ra 3.2μm as-machined",
                           "Only specify fine finishes on sealing/bearing surfaces",
                           "Ra 1.6μm requires additional passes. Ra 0.8μm requires grinding (100-200% more).",
                           "Standard finish: no premium. Fine finish: +30-50%"))

    score = _calc_score(issues, warnings, passed)
    return _build_result("CNC Machining", material, score, issues, warnings, suggestions, passed,
                         all_rules, rationale, geometry)


def _check_wall_thickness(t, material, issues, warnings, passed, all_rules, rationale):
    std = "Minimum 0.8mm aluminum, 1.0mm steel. Optimal: 2.0mm+"
    if t <= 0:
        all_rules.append(_rule("Wall Thickness (ISO 2768)", std, "INFO", "Not measured",
                               "Could not measure from geometry", "Verify manually", "N/A", "N/A"))
        return
    if t < 0.5:
        issues.append({"category": "Wall Thickness", "message": f"Critical: {t:.2f}mm too thin"})
        rationale.append(f"❌ Wall {t:.2f}mm critically thin - will deflect during machining.")
        all_rules.append(_rule("Wall Thickness (ISO 2768)", std, "FAIL", f"{t:.2f}mm",
                               f"Wall {t:.2f}mm below 0.5mm minimum", "Increase to ≥0.8mm (Al) or ≥1.0mm (steel)",
                               "Walls <0.5mm deflect under cutting forces causing chatter and tool breakage.",
                               "200-300% premium for micro-machining"))
    elif t < 1.5:
        warnings.append({"category": "Wall Thickness", "message": f"Marginal: {t:.2f}mm"})
        rationale.append(f"⚠️ Wall {t:.2f}mm marginal - 30-40% cost premium.")
        all_rules.append(_rule("Wall Thickness (ISO 2768)", std, "WARNING", f"{t:.2f}mm",
                               f"Wall {t:.2f}mm machinable but requires reduced feed rates",
                               "Increase to 2.0mm for standard machining parameters",
                               "Thin walls require 50% slower feeds and special fixturing.",
                               "30-40% cost increase"))
    else:
        passed.append({"check": "Wall Thickness", "status": f"{t:.2f}mm - Excellent"})
        rationale.append(f"✓ Wall {t:.2f}mm provides excellent rigidity.")
        all_rules.append(_rule("Wall Thickness (ISO 2768)", std, "PASS", f"{t:.2f}mm",
                               f"Wall {t:.2f}mm exceeds minimum - excellent rigidity",
                               "No changes needed", "Sufficient rigidity for standard parameters.", "Standard cost"))


def _check_part_size(dims, issues, warnings, passed, all_rules, rationale):
    if not dims:
        return
    max_dim = max(dims.values())
    std = "Standard 3-axis: 500×500×500mm. Large-format: up to 1000mm"
    if max_dim > 1000:
        issues.append({"category": "Part Size", "message": f"Oversized: {max_dim:.1f}mm"})
        rationale.append(f"❌ Part {max_dim:.1f}mm requires specialized equipment.")
        all_rules.append(_rule("Part Size", std, "FAIL", f"{max_dim:.1f}mm",
                               "Exceeds standard machine capacity", "Split into assemblies or use large-format shop",
                               "Parts >1000mm require rare large-format 5-axis machines.", "300-500% cost increase"))
    elif max_dim > 500:
        warnings.append({"category": "Part Size", "message": f"Large: {max_dim:.1f}mm"})
        rationale.append(f"⚠️ Part {max_dim:.1f}mm limits shop options.")
        all_rules.append(_rule("Part Size", std, "WARNING", f"{max_dim:.1f}mm",
                               "Requires large-bed machine", "Verify machine capacity or split part",
                               "Parts 500-1000mm reduce shop options by 60-70%.", "50-100% cost premium"))
    else:
        passed.append({"check": "Part Size", "status": "Fits standard machines"})
        rationale.append(f"✓ Part fits standard CNC envelopes.")
        all_rules.append(_rule("Part Size", std, "PASS", f"{max_dim:.1f}mm",
                               "Within standard machine capacity", "No changes needed",
                               "Maximum shop compatibility.", "Standard cost"))


def _check_corner_radii(dims, warnings, suggestions, all_rules, rationale):
    if not dims:
        return
    depth = dims.get("z", 0)
    if depth <= 0:
        return
    min_r = max(depth / 3, 0.5)
    warnings.append({"category": "Internal Corners", "message": f"Min radius: {min_r:.2f}mm"})
    rationale.append(f"⚠️ Internal corners need ≥{min_r:.2f}mm radius (1/3 depth rule).")
    all_rules.append(_rule("Internal Corner Radii", "Min radius = 1/3 pocket depth or 0.5mm", "WARNING",
                           f"Depth: {depth:.1f}mm → radius ≥{min_r:.2f}mm",
                           f"Pockets {depth:.1f}mm deep need {min_r:.2f}mm corner radius",
                           f"Add {min_r:.2f}mm radius to all internal corners",
                           "Tools are round - sharp corners impossible. Smaller radii = smaller tools = slower.",
                           f"Standard with {min_r:.2f}mm. Tighter: +30-60%"))


def _check_material(material, warnings, passed, suggestions, all_rules, rationale):
    mat_lower = material.lower()
    std = "Aluminum: excellent (5/5). Steel: moderate (3/5). Stainless: poor (2/5). Titanium: very poor (1/5)"
    if "aluminum" in mat_lower:
        passed.append({"check": "Material", "status": "Excellent machinability"})
        rationale.append(f"✓ {material} - excellent machinability, 3-4× faster than steel.")
        all_rules.append(_rule("Material Machinability", std, "PASS", material,
                               "Excellent machinability - high speeds and feeds possible",
                               "Optimal choice for CNC", "Machines 3-4× faster than steel.", "Standard cost"))
    elif "stainless" in mat_lower:
        warnings.append({"category": "Material", "message": "Stainless - poor machinability"})
        rationale.append(f"⚠️ {material} - 4-6× longer cycle time than aluminum.")
        all_rules.append(_rule("Material Machinability", std, "WARNING", material,
                               "Poor machinability - work-hardens during cutting",
                               "Consider 303 stainless (free-machining) or aluminum",
                               "Requires 50-70% reduced feeds. Tool life 1/5 of aluminum.", "200-300% vs aluminum"))
    elif "titanium" in mat_lower:
        warnings.append({"category": "Material", "message": "Titanium - very poor machinability"})
        rationale.append(f"⚠️ {material} - 8-10× longer than aluminum.")
        all_rules.append(_rule("Material Machinability", std, "WARNING", material,
                               "Very poor machinability - specialized tooling required",
                               "Verify titanium is required - consider alternatives",
                               "70-80% reduced feeds, high-pressure coolant needed.", "400-600% vs aluminum"))
    else:
        passed.append({"check": "Material", "status": "Acceptable machinability"})
        rationale.append(f"✓ {material} - acceptable for CNC.")
        all_rules.append(_rule("Material Machinability", std, "PASS", material,
                               "Moderate to good machinability", "No changes needed",
                               "Standard machining parameters apply.", "Standard cost"))


def _rule(name, standard, status, measured, evaluation, recommendation, rationale, cost_impact):
    return {"name": name, "standard": standard, "status": status, "measured_value": measured,
            "evaluation": evaluation, "recommendation": recommendation, "rationale": rationale,
            "cost_impact": cost_impact}


def _calc_score(issues, warnings, passed):
    total = len(issues) + len(warnings) + len(passed)
    if total == 0:
        return 75.0
    return round((len(passed) * 100 + len(warnings) * 50) / total, 1)


def _build_result(process, material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry):
    dims = geometry.get("dimensions", {})
    return {
        "success": True,
        "process": process,
        "material": material,
        "score": score,
        "score_explanation": f"Based on {len(passed)} passed, {len(warnings)} warnings, {len(issues)} issues",
        "issues": len(issues),
        "warnings": len(warnings),
        "suggestions": len(suggestions),
        "passed": len(passed),
        "all_rules": all_rules,
        "geometry_info": {
            "dimensions": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm",
            "min_thickness": f"{geometry.get('estimated_min_thickness',0):.2f} mm",
        },
        "summary": f"**CNC Machining Analysis** | Score: {score}/100 | {len(issues)} issues, {len(warnings)} warnings, {len(passed)} passed",
        "rationale": rationale,
        "details": {"critical_issues": issues[:5], "warnings": warnings[:5], "cost_savings": suggestions[:3]},
    }
