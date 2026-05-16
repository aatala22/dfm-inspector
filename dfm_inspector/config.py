"""Manufacturing process definitions and configuration."""

PROCESSES = {
    "cnc_machining": {
        "name": "CNC Machining",
        "icon": "⚙️",
        "description": "Milling, turning, drilling",
        "materials": ["Aluminum 6061", "Aluminum 7075", "Steel 1018", "Stainless 304", "Brass", "Titanium"],
    },
    "welding": {
        "name": "Welding",
        "icon": "🔥",
        "description": "MIG, TIG, spot welding",
        "materials": ["Steel Structural", "Aluminum", "Stainless Steel", "Sheet Steel"],
    },
    "sheet_metal": {
        "name": "Sheet Metal",
        "icon": "📋",
        "description": "Bending, forming, laser cutting",
        "materials": ["Steel", "Aluminum 5052", "Aluminum 6061", "Stainless Steel"],
    },
    "injection_molding": {
        "name": "Injection Molding",
        "icon": "💉",
        "description": "Plastic part molding",
        "materials": ["ABS", "Polycarbonate", "Nylon", "PP", "PEEK"],
    },
    "die_casting": {
        "name": "Die Casting (HPDC)",
        "icon": "🏭",
        "description": "High-pressure die casting per 930-00166",
        "materials": ["Aluminum A380", "AlSi12(Fe)", "Zinc Zamak 3", "Magnesium AZ91D"],
    },
    "lpdc": {
        "name": "Low Pressure Die Casting",
        "icon": "⚙️",
        "description": "LPDC - gravity-fed casting per 930-00166",
        "materials": ["Aluminum A380", "Aluminum 319.0", "AlSi12(Fe)"],
    },
    "permanent_mold": {
        "name": "Permanent Mold / Gravity Cast",
        "icon": "🔵",
        "description": "Gravity-fed permanent mold casting per 930-00166",
        "materials": ["Aluminum 319.0", "Aluminum A380", "AlSi12(Fe)"],
    },
    "investment_casting": {
        "name": "Investment Casting",
        "icon": "🎨",
        "description": "Lost-wax casting",
        "materials": ["Steel", "Stainless Steel", "Aluminum", "Titanium"],
    },
    "mim": {
        "name": "Metal Injection Molding",
        "icon": "🔩",
        "description": "Powder metallurgy",
        "materials": ["Stainless Steel 316L", "Tool Steel", "Low Alloy Steel"],
    },
    "rotational_molding": {
        "name": "Rotational Molding",
        "icon": "🔄",
        "description": "Hollow plastic parts",
        "materials": ["Polyethylene", "Polypropylene", "Nylon"],
    },
    "wire_forming": {
        "name": "Wire Forming",
        "icon": "🔗",
        "description": "Wire bending and forming",
        "materials": ["Steel Wire", "Stainless Wire", "Spring Steel", "Aluminum Wire"],
    },
    "vacuum_forming": {
        "name": "Vacuum Forming",
        "icon": "🌬️",
        "description": "Thermoforming",
        "materials": ["ABS", "PETG", "Polystyrene", "Polycarbonate"],
    },
}

ALLOWED_EXTENSIONS = {"step", "stp", "iges", "igs", "stl"}
MAX_FILE_SIZE_MB = 100
