"""Other manufacturing process analyzers: Investment Casting, MIM, Rotational Molding, Wire Forming, Vacuum Forming."""
from typing import Dict


def _rule(name, standard, status, measured, evaluation, recommendation, rationale, cost_impact):
    return {"name": name, "standard": standard, "status": status, "measured_value": measured,
            "evaluation": evaluation, "recommendation": recommendation, "rationale": rationale,
            "cost_impact": cost_impact}


def _calc_score(issues, warnings, passed):
    total = len(issues) + len(warnings) + len(passed)
    return round((len(passed) * 100 + len(warnings) * 50) / total, 1) if total else 75.0


def _result(process, material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry):
    dims = geometry.get("dimensions", {})
    return {
        "success": True, "process": process, "material": material, "score": score,
        "score_explanation": f"Based on {len(passed)} passed, {len(warnings)} warnings, {len(issues)} issues",
        "issues": len(issues), "warnings": len(warnings), "suggestions": len(suggestions), "passed": len(passed),
        "all_rules": all_rules,
        "geometry_info": {"dimensions": f"{dims.get('x',0):.1f} x {dims.get('y',0):.1f} x {dims.get('z',0):.1f} mm",
                         "min_thickness": f"{geometry.get('estimated_min_thickness',0):.2f} mm"},
        "summary": f"**{process} Analysis** | Score: {score}/100 | {len(issues)} issues, {len(warnings)} warnings",
        "rationale": rationale,
        "details": {"critical_issues": issues[:5], "warnings": warnings[:5], "cost_savings": suggestions[:3]},
    }


def analyze_investment_casting(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []
    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)

    # Wall thickness: 1.5-25mm typical
    if min_thickness > 0:
        if min_thickness < 1.5:
            issues.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm too thin"})
            all_rules.append(_rule("Wall Thickness", "Min 1.5mm, optimal 3-6mm", "FAIL", f"{min_thickness:.2f}mm",
                                   "Below 1.5mm minimum", "Increase to ≥1.5mm",
                                   "Thin walls cause misruns in investment casting.", "Part will not fill"))
        else:
            passed.append({"check": "Wall Thickness", "status": f"{min_thickness:.2f}mm OK"})
            all_rules.append(_rule("Wall Thickness", "Min 1.5mm, optimal 3-6mm", "PASS", f"{min_thickness:.2f}mm",
                                   "Adequate for investment casting", "No changes needed",
                                   "Good metal flow characteristics.", "Standard cost"))

    # Draft: 0° possible but 0.5-1° recommended
    all_rules.append(_rule("Draft Angle", "0° possible, 0.5-1° recommended for wax ejection", "INFO",
                           "0.5-1° recommended", "Investment casting allows near-zero draft",
                           "Add 0.5° minimum for easier wax pattern ejection",
                           "Zero draft possible but increases wax pattern cost and breakage.", "0° draft: +10-20% wax cost"))

    # Surface finish
    passed.append({"check": "Surface Finish", "status": "Ra 3.2-6.3μm as-cast"})
    all_rules.append(_rule("Surface Finish", "As-cast: Ra 3.2-6.3μm. Best of all casting processes", "PASS",
                           "Ra 3.2-6.3μm achievable", "Excellent as-cast surface finish",
                           "Investment casting provides best surface of all casting methods",
                           "Near-net-shape with minimal machining required.", "Minimal post-processing"))

    suggestions.append({"opportunity": "Consolidate multiple machined parts into one casting",
                       "savings": "40-60% assembly cost reduction", "difficulty": "Medium"})

    score = _calc_score(issues, warnings, passed)
    return _result("Investment Casting", material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry)


def analyze_mim(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []
    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)

    # MIM: small parts, 0.5-10mm walls, <100g typical
    if min_thickness > 0:
        if min_thickness < 0.5:
            issues.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm too thin for MIM"})
            all_rules.append(_rule("Wall Thickness", "Min 0.5mm, optimal 1-6mm. Max 10mm", "FAIL", f"{min_thickness:.2f}mm",
                                   "Below 0.5mm minimum", "Increase to ≥0.5mm",
                                   "Thin walls cause incomplete fill and cracking during sintering.", "Redesign required"))
        elif min_thickness > 10:
            warnings.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm too thick for MIM"})
            all_rules.append(_rule("Wall Thickness", "Min 0.5mm, optimal 1-6mm. Max 10mm", "WARNING", f"{min_thickness:.2f}mm",
                                   "Exceeds 10mm practical maximum", "Core out thick sections",
                                   "Thick sections cause long debinding times and sintering defects.", "+50-100% cycle time"))
        else:
            passed.append({"check": "Wall Thickness", "status": f"{min_thickness:.2f}mm OK"})
            all_rules.append(_rule("Wall Thickness", "Min 0.5mm, optimal 1-6mm. Max 10mm", "PASS", f"{min_thickness:.2f}mm",
                                   "Within optimal range", "No changes needed",
                                   "Good for MIM processing.", "Standard cost"))

    # Part size check
    if dims:
        max_dim = max(dims.values())
        if max_dim > 100:
            warnings.append({"category": "Part Size", "message": f"{max_dim:.1f}mm large for MIM"})
            all_rules.append(_rule("Part Size", "Optimal: <50mm. Max practical: ~100mm", "WARNING", f"{max_dim:.1f}mm",
                                   "Large for MIM - sintering distortion risk", "Consider machining or casting instead",
                                   "Large MIM parts distort during sintering and are expensive.", "Consider alternative process"))
        else:
            passed.append({"check": "Part Size", "status": "Good for MIM"})
            all_rules.append(_rule("Part Size", "Optimal: <50mm. Max practical: ~100mm", "PASS", f"{max_dim:.1f}mm",
                                   "Within MIM size range", "No changes needed",
                                   "Part size suitable for MIM processing.", "Standard cost"))

    suggestions.append({"opportunity": "MIM achieves ±0.3% tolerances as-sintered",
                       "savings": "Eliminates machining for most features", "difficulty": "Easy"})

    score = _calc_score(issues, warnings, passed)
    return _result("Metal Injection Molding", material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry)


def analyze_rotational_molding(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []
    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)

    # Rotomolding: 2-12mm walls, hollow parts
    if min_thickness > 0:
        if min_thickness < 2.0:
            warnings.append({"category": "Wall Thickness", "message": f"{min_thickness:.2f}mm thin for rotomolding"})
            all_rules.append(_rule("Wall Thickness", "Min 2mm, optimal 3-6mm. Max 12mm", "WARNING", f"{min_thickness:.2f}mm",
                                   "Below 2mm practical minimum", "Increase to ≥3mm for uniform coverage",
                                   "Thin walls have uneven thickness distribution in rotomolding.", "High scrap rate"))
        else:
            passed.append({"check": "Wall Thickness", "status": f"{min_thickness:.2f}mm OK"})
            all_rules.append(_rule("Wall Thickness", "Min 2mm, optimal 3-6mm. Max 12mm", "PASS", f"{min_thickness:.2f}mm",
                                   "Adequate for rotomolding", "No changes needed",
                                   "Good powder distribution expected.", "Standard cost"))

    # Draft: 1-2° minimum
    warnings.append({"category": "Draft", "message": "Minimum 1-2° draft for mold release"})
    all_rules.append(_rule("Draft Angle", "Min 1° female, 2° male features", "WARNING",
                           "≥1° required", "Draft needed for part removal from mold",
                           "Apply ≥1° to female features, ≥2° to male features",
                           "Parts stick without draft. Rotomolding molds are typically aluminum - easy to damage.",
                           "Stuck parts damage mold ($5K-20K replacement)"))

    # Corner radii: generous required
    all_rules.append(_rule("Corner Radii", "Min radius = wall thickness. Larger is better", "INFO",
                           f"≥{max(min_thickness, 3.0):.1f}mm recommended",
                           "Powder does not flow into sharp corners",
                           "Use generous radii (≥ wall thickness) on all corners",
                           "Sharp corners result in thin spots and stress concentrations. Powder bridges across sharp corners.",
                           "Sharp corners: thin spots, early failure. Radii: uniform wall"))

    suggestions.append({"opportunity": "Design as hollow part - rotomolding's strength",
                       "savings": "50-70% lighter than solid equivalent", "difficulty": "Easy"})

    score = _calc_score(issues, warnings, passed)
    return _result("Rotational Molding", material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry)


def analyze_wire_forming(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []
    dims = geometry.get("dimensions", {})
    min_dim = min(dims.values()) if dims else 0

    # Wire diameter: 0.5-12mm typical
    if min_dim > 0:
        if min_dim < 0.5:
            issues.append({"category": "Wire Diameter", "message": f"{min_dim:.2f}mm too thin"})
            all_rules.append(_rule("Wire Diameter", "Min 0.5mm, optimal 1-6mm, max 12mm", "FAIL", f"{min_dim:.2f}mm",
                                   "Below 0.5mm - breaks during forming", "Increase to ≥1.0mm",
                                   "Wire <0.5mm is fragile and breaks during bending.", "Not formable"))
        elif min_dim > 12:
            warnings.append({"category": "Wire Diameter", "message": f"{min_dim:.2f}mm thick - consider bar stock"})
            all_rules.append(_rule("Wire Diameter", "Min 0.5mm, optimal 1-6mm, max 12mm", "WARNING", f"{min_dim:.2f}mm",
                                   "Exceeds 12mm - requires heavy equipment", "Consider machining from bar stock",
                                   "Wire >12mm requires heavy-duty forming equipment.", "May be cheaper to machine"))
        else:
            passed.append({"check": "Wire Diameter", "status": f"{min_dim:.2f}mm OK"})
            all_rules.append(_rule("Wire Diameter", "Min 0.5mm, optimal 1-6mm, max 12mm", "PASS", f"{min_dim:.2f}mm",
                                   "Within standard forming range", "No changes needed",
                                   "Standard CNC wire benders handle this diameter.", "Standard cost"))

    # Bend radius: ≥3× diameter
    if min_dim > 0:
        min_bend = min_dim * 3
        warnings.append({"category": "Bend Radius", "message": f"Min: {min_bend:.2f}mm (3× diameter)"})
        all_rules.append(_rule("Bend Radius", "≥3× wire diameter. Spring steel: 5-6×", "WARNING", f"≥{min_bend:.2f}mm",
                               "Minimum bend radius based on wire diameter",
                               f"Use ≥{min_bend:.2f}mm radius (4× recommended)",
                               "Bends tighter than 3× diameter cause cracking and work-hardening.",
                               "Standard with proper radius. Tight bends: high scrap rate"))

    # Leg length
    if min_dim > 0:
        min_leg = min_dim * 3
        all_rules.append(_rule("Minimum Leg Length", "≥3× wire diameter between bends", "INFO", f"≥{min_leg:.2f}mm",
                               "Short legs are difficult to grip and form",
                               f"Maintain ≥{min_leg:.2f}mm straight length between bends",
                               "Legs shorter than 3× diameter cannot be gripped by forming tools.",
                               "Short legs require special tooling (+$500-2000)"))

    # Springback
    suggestions.append({"opportunity": "Account for 2-10° springback",
                       "savings": "Prevents rework", "difficulty": "Medium"})
    all_rules.append(_rule("Springback Compensation", "Steel: 4-8°, Stainless: 6-10°, Aluminum: 2-4°", "INFO",
                           "Material-dependent", "Wire springs back after bending",
                           "CNC benders compensate automatically. Manual: overbend by springback angle",
                           "Springback varies by material, diameter, and bend angle.", "CNC handles automatically"))

    score = _calc_score(issues, warnings, passed)
    return _result("Wire Forming", material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry)


def analyze_vacuum_forming(geometry: Dict, material: str) -> Dict:
    issues, warnings, suggestions, passed, all_rules, rationale = [], [], [], [], [], []
    dims = geometry.get("dimensions", {})
    min_thickness = geometry.get("estimated_min_thickness", 0)

    # Vacuum forming: 0.5-6mm sheet, large parts possible
    if min_thickness > 0:
        if min_thickness < 0.5:
            issues.append({"category": "Sheet Thickness", "message": f"{min_thickness:.2f}mm too thin"})
            all_rules.append(_rule("Sheet Thickness", "Min 0.5mm, optimal 1-3mm, max 6mm", "FAIL", f"{min_thickness:.2f}mm",
                                   "Below minimum for vacuum forming", "Increase to ≥1.0mm",
                                   "Thin sheets tear during forming and have poor detail reproduction.",
                                   "Not formable reliably"))
        else:
            passed.append({"check": "Sheet Thickness", "status": f"{min_thickness:.2f}mm OK"})
            all_rules.append(_rule("Sheet Thickness", "Min 0.5mm, optimal 1-3mm, max 6mm", "PASS", f"{min_thickness:.2f}mm",
                                   "Adequate for vacuum forming", "No changes needed",
                                   "Good detail reproduction and structural integrity.", "Standard cost"))

    # Draft: 2-5° required
    warnings.append({"category": "Draft Angle", "message": "Minimum 2° draft (5° for textured)"})
    all_rules.append(_rule("Draft Angle", "Min 2° female, 3° male. 5° for textured surfaces", "WARNING",
                           "≥2° required", "More draft needed than injection molding",
                           "Apply ≥2° to female molds, ≥3° to male molds",
                           "Vacuum formed parts grip the mold tightly. Insufficient draft causes tearing on removal.",
                           "Stuck parts: scrap + mold damage risk"))

    # Draw ratio
    if dims:
        depth = dims.get("z", 0)
        width = min(dims.get("x", 1), dims.get("y", 1))
        if width > 0:
            draw_ratio = depth / width
            if draw_ratio > 0.5:
                warnings.append({"category": "Draw Ratio", "message": f"Deep draw: {draw_ratio:.2f}"})
                all_rules.append(_rule("Draw Ratio", "Max 0.5:1 (depth:width). Deep draws thin corners", "WARNING",
                                       f"{draw_ratio:.2f}:1", "Deep draw causes excessive thinning",
                                       "Reduce depth or increase width. Consider plug assist",
                                       "Material thins 50-70% at corners of deep draws. Structural weakness.",
                                       "Plug assist: +$2K-5K tooling. Deep draw scrap: 10-30%"))
            else:
                passed.append({"check": "Draw Ratio", "status": f"{draw_ratio:.2f}:1 OK"})
                all_rules.append(_rule("Draw Ratio", "Max 0.5:1 (depth:width)", "PASS",
                                       f"{draw_ratio:.2f}:1", "Within acceptable range", "No changes needed",
                                       "Uniform wall thickness expected.", "Standard cost"))

    suggestions.append({"opportunity": "Add texture to hide thinning variations",
                       "savings": "Improves cosmetic appearance at no cost", "difficulty": "Easy"})

    score = _calc_score(issues, warnings, passed)
    return _result("Vacuum Forming", material, score, issues, warnings, suggestions, passed, all_rules, rationale, geometry)
