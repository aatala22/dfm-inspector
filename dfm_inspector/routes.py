"""Flask routes for DFM Inspector."""

import os

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from .config import ALLOWED_EXTENSIONS, PROCESSES
from .parser import CADParser
from .analyzers.base import analyze

bp = Blueprint("main", __name__)


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/")
def index():
    return render_template("index.html", processes=PROCESSES)


@bp.route("/api/processes")
def get_processes():
    return jsonify(PROCESSES)


@bp.route("/api/materials/<process>")
def get_materials(process: str):
    proc = PROCESSES.get(process)
    if not proc:
        return jsonify({"error": "Unknown process"}), 404
    return jsonify({"materials": proc["materials"]})


@bp.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not _allowed(file.filename):
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return jsonify({"success": True, "filename": filename, "filepath": filepath, "size": os.path.getsize(filepath)})


@bp.route("/api/analyze", methods=["POST"])
def analyze_file():
    data = request.json
    process = data.get("process")
    material = data.get("material")
    filepath = data.get("filepath")

    if process not in PROCESSES:
        return jsonify({"error": "Invalid process"}), 400
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 400

    parser = CADParser(filepath)
    if not parser.load():
        return jsonify({"success": False, "error": "Failed to parse CAD file"}), 400

    geometry = parser.get_geometry()
    results = analyze(geometry, material, process)
    return jsonify(results)
