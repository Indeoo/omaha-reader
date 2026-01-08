from datetime import datetime
import hashlib
import json

from flask import Blueprint, jsonify, request
from loguru import logger

from apps.server.utils.game_data_formatter import format_game_data_for_web


def create_api_blueprint(
    show_table_cards,
    show_positions,
    show_moves,
    show_solver_link,
    game_state_service,
    game_data_receiver,
):
    blueprint = Blueprint("api", __name__)

    @blueprint.route("/api/config")
    def get_config():
        return jsonify(
            {
                "show_table_cards": show_table_cards,
                "show_positions": show_positions,
                "show_moves": show_moves,
                "show_solver_link": show_solver_link,
            }
        )

    @blueprint.route("/api/client/<client_id>/config")
    def get_client_config(client_id):
        connected_clients = game_data_receiver.get_connected_clients()
        if client_id not in connected_clients:
            return jsonify({"error": "Client not found"}), 404

        return jsonify(
            {
                "client_id": client_id,
                "show_table_cards": show_table_cards,
                "show_positions": show_positions,
                "show_moves": show_moves,
                "show_solver_link": show_solver_link,
            }
        )

    @blueprint.route("/api/client/<client_id>/data")
    def get_client_data(client_id):
        try:
            client_games = game_state_service.get_client_game_states(client_id)
            latest_update = None

            for game in client_games:
                if "last_update" in game:
                    game_time = datetime.fromisoformat(game["last_update"].replace("Z", "+00:00"))
                    if latest_update is None or game_time > latest_update:
                        latest_update = game_time

            return jsonify(
                {
                    "client_id": client_id,
                    "detections": [format_game_data_for_web(game) for game in client_games],
                    "last_update": latest_update.isoformat()
                    if latest_update
                    else datetime.now().isoformat(),
                    "total_tables": len(client_games),
                }
            )
        except Exception as e:
            logger.error(f"Error getting client data for {client_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @blueprint.route("/api/client/<client_id>/detections")
    def get_client_detections(client_id):
        try:
            client_games = game_state_service.get_client_game_states(client_id)

            client_json = json.dumps(client_games, sort_keys=True)
            etag = hashlib.md5(client_json.encode()).hexdigest()[:8]

            if request.headers.get("If-None-Match") == etag:
                return "", 304

            latest_update = None
            for game in client_games:
                if "last_update" in game:
                    game_time = datetime.fromisoformat(game["last_update"].replace("Z", "+00:00"))
                    if latest_update is None or game_time > latest_update:
                        latest_update = game_time

            response_data = {
                "type": "client_detection_update",
                "client_id": client_id,
                "detections": [format_game_data_for_web(game) for game in client_games],
                "last_update": latest_update.isoformat()
                if latest_update
                else datetime.now().isoformat(),
                "total_tables": len(client_games),
                "polling_interval": 5000,
            }

            response = jsonify(response_data)
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = "no-cache"
            return response

        except Exception as e:
            logger.error(f"Error in /api/client/{client_id}/detections: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @blueprint.route("/api/detections")
    def get_detections():
        try:
            current_state = game_data_receiver.get_current_state()

            state_json = json.dumps(current_state, sort_keys=True)
            etag = hashlib.md5(state_json.encode()).hexdigest()[:8]

            if request.headers.get("If-None-Match") == etag:
                return "", 304

            raw_detections = current_state.get("detections", [])
            formatted_detections = [format_game_data_for_web(detection) for detection in raw_detections]

            response_data = {
                "type": "detection_update",
                "detections": formatted_detections,
                "last_update": current_state.get("last_update"),
                "connected_clients": game_data_receiver.get_connected_clients(),
                "total_clients": len(game_data_receiver.get_connected_clients()),
                "polling_interval": 5000,
            }

            response = jsonify(response_data)
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = "no-cache"
            return response

        except Exception as e:
            logger.error(f"Error in /api/detections: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @blueprint.route("/api/clients")
    def get_connected_clients():
        return jsonify(
            {
                "connected_clients": game_data_receiver.get_connected_clients(),
                "total_clients": len(game_data_receiver.get_connected_clients()),
            }
        )

    @blueprint.route("/api/client/update", methods=["POST"])
    def update_game_state():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON data required"}), 400

            response = game_data_receiver.handle_client_message(json.dumps(data))

            if response and response.status == "success":
                return jsonify({"status": "success", "message": response.message})

            return (
                jsonify(
                    {
                        "status": "error",
                        "message": response.message if response else "Unknown error",
                    }
                ),
                500,
            )

        except Exception as e:
            logger.error(f"Error in game state update: {str(e)}")
            return jsonify({"error": str(e)}), 500

    return blueprint
