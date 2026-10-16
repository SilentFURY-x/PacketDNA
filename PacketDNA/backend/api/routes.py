"""
PacketDNA - API Routes
========================
REST API endpoints for the PacketDNA application.

Endpoints:
    GET  /api/v1/health         - Health check
    GET  /api/v1/demo           - Generate demo analysis
    POST /api/v1/analyze        - Upload and analyze PCAP file
    GET  /api/v1/results/<id>   - Get analysis results
    GET  /api/v1/sessions       - List all sessions
    GET  /api/v1/stats          - System statistics
"""

import os
import uuid

from flask import Blueprint, request, jsonify, current_app

from config.settings import get_config
from services.analysis_service import AnalysisService

config = get_config()
api_bp = Blueprint("api", __name__, url_prefix=config.API_PREFIX)

# Shared service instance
analysis_service = AnalysisService()


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
    })


@api_bp.route("/demo", methods=["GET"])
def generate_demo():
    """Generate demo analysis with synthetic data."""
    try:
        result = analysis_service.generate_demo_data()
        return jsonify({
            "success": True,
            "message": "Demo analysis generated successfully",
            "data": result.to_dict(),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@api_bp.route("/analyze", methods=["POST"])
def analyze_pcap():
    """
    Upload and analyze a PCAP file.

    Expects multipart form data with:
        - file: PCAP/PCAPNG file
        - model_type (optional): ML model to use
    """
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file provided. Send a PCAP file as 'file' in multipart form data.",
        }), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "Empty filename",
        }), 400

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext.lstrip(".") not in config.ALLOWED_EXTENSIONS:
        return jsonify({
            "success": False,
            "error": f"Unsupported file type: {ext}. Allowed: {config.ALLOWED_EXTENSIONS}",
        }), 400

    # Save uploaded file
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    upload_id = str(uuid.uuid4())[:8]
    safe_filename = f"{upload_id}_{file.filename}"
    filepath = os.path.join(config.UPLOAD_DIR, safe_filename)
    file.save(filepath)

    try:
        model_type = request.form.get("model_type", None)
        result = analysis_service.analyze_pcap(filepath, model_type)

        return jsonify({
            "success": True,
            "message": f"Analysis complete. {result.total_flows} flows classified.",
            "data": result.to_dict(),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}",
        }), 500
    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)


@api_bp.route("/results/<session_id>", methods=["GET"])
def get_results(session_id):
    """Get analysis results by session ID."""
    result = analysis_service.get_result(session_id)
    if result is None:
        return jsonify({
            "success": False,
            "error": f"Session '{session_id}' not found",
        }), 404

    return jsonify({
        "success": True,
        "data": result.to_dict(),
    })


@api_bp.route("/sessions", methods=["GET"])
def list_sessions():
    """List all analysis sessions."""
    sessions = analysis_service.get_all_sessions()
    return jsonify({
        "success": True,
        "count": len(sessions),
        "data": sessions,
    })


@api_bp.route("/stats", methods=["GET"])
def system_stats():
    """Get system statistics."""
    sessions = analysis_service.get_all_sessions()

    total_flows = sum(s.get("total_flows", 0) for s in sessions)
    total_packets = sum(s.get("total_packets", 0) for s in sessions)

    return jsonify({
        "success": True,
        "data": {
            "total_sessions": len(sessions),
            "total_flows_analyzed": total_flows,
            "total_packets_processed": total_packets,
            "supported_models": list(
                analysis_service.classifier.SUPPORTED_MODELS.keys()
            ),
            "feature_count": config.NUM_FEATURES,
            "app_version": config.APP_VERSION,
        },
    })
