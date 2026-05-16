"""STEP/STL/IGES file parser using trimesh + cascadio."""

import logging
import os
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CADParser:
    """Parse CAD files (STEP, STL, IGES) and extract geometry metrics."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.mesh = None
        self._geometry: Optional[Dict] = None

    def load(self) -> bool:
        """Load CAD file. Returns True on success."""
        try:
            import trimesh

            self.mesh = trimesh.load(self.file_path)
            if isinstance(self.mesh, trimesh.Scene):
                self.mesh = self.mesh.dump(concatenate=True)
            logger.info(f"Loaded {os.path.basename(self.file_path)}: {len(self.mesh.faces)} faces")
            return True
        except Exception as e:
            logger.warning(f"Primary load failed: {e}, trying text parse")
            return self._fallback_text_parse()

    def _fallback_text_parse(self) -> bool:
        """Extract bounding box from STEP text when trimesh fails."""
        import re

        try:
            with open(self.file_path, "r", errors="ignore") as f:
                content = f.read()
            coords = re.findall(r"CARTESIAN_POINT\('.*?',\(([-\d.eE+]+),([-\d.eE+]+),([-\d.eE+]+)\)\)", content)
            if not coords:
                return False
            pts = np.array([[float(x), float(y), float(z)] for x, y, z in coords])
            mins, maxs = pts.min(axis=0), pts.max(axis=0)
            dims = maxs - mins
            self._geometry = {
                "dimensions": {"x": dims[0], "y": dims[1], "z": dims[2]},
                "volume": float(np.prod(dims)) * 0.3,
                "surface_area": 2 * (dims[0] * dims[1] + dims[1] * dims[2] + dims[0] * dims[2]),
                "is_watertight": False,
                "estimated_min_thickness": float(min(dims)),
            }
            return True
        except Exception:
            return False

    def get_geometry(self) -> Dict:
        """Return geometry analysis dict."""
        if self._geometry:
            return self._geometry

        if self.mesh is None:
            return {"dimensions": {}, "volume": 0, "surface_area": 0, "is_watertight": False, "estimated_min_thickness": 0}

        bounds = self.mesh.bounds
        dims = bounds[1] - bounds[0]

        # Auto-detect units: if max dimension < 1, likely meters → convert to mm
        scale = 1.0
        max_dim = float(max(dims))
        if max_dim < 1.0:
            scale = 1000.0  # meters to mm
        elif max_dim < 10.0:
            scale = 100.0  # possible cm to mm

        dims_mm = dims * scale
        sorted_dims = sorted(dims_mm)

        volume = float(self.mesh.volume) * (scale ** 3) if self.mesh.is_watertight else float(np.prod(dims_mm)) * 0.3
        area = float(self.mesh.area) * (scale ** 2)

        return {
            "dimensions": {"x": float(dims_mm[0]), "y": float(dims_mm[1]), "z": float(dims_mm[2])},
            "volume": volume,
            "surface_area": area,
            "is_watertight": bool(self.mesh.is_watertight),
            "estimated_min_thickness": float(sorted_dims[0]) if sorted_dims[0] < sorted_dims[2] * 0.3 else float(sorted_dims[0] * 0.4),
        }
