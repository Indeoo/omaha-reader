import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from loguru import logger

from apps.server.routes.api import create_api_blueprint
from apps.server.routes.web import create_web_blueprint
from apps.server.services.game_data_receiver import GameDataReceiver
from apps.server.services.server_game_state import ServerGameStateService


def create_app(
    show_table_cards=True,
    show_positions=True,
    show_moves=True,
    show_solver_link=True,
    require_password=False,
    password="_test_password_",
):
    current_path = Path(__file__).resolve().parent
    template_dir = current_path / "web" / "templates"
    static_dir = current_path / "web" / "static"

    # Debug logging for deployment diagnostics.
    logger.info(f"🔍 Current directory: {current_path}")
    logger.info(f"🔍 Template directory: {template_dir}")
    logger.info(f"🔍 Template directory exists: {template_dir.exists()}")
    if template_dir.exists():
        logger.info(f"🔍 Template files: {list(template_dir.iterdir())}")
    logger.info(f"🔍 Static directory: {static_dir}")
    logger.info(f"🔍 Static directory exists: {static_dir.exists()}")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
    )
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    CORS(app, origins="*")

    game_state_service = ServerGameStateService()
    game_data_receiver = GameDataReceiver(game_state_service)

    app.extensions["game_state_service"] = game_state_service
    app.extensions["game_data_receiver"] = game_data_receiver

    app.register_blueprint(
        create_web_blueprint(
            require_password=require_password,
            password=password,
            game_data_receiver=game_data_receiver,
        )
    )
    app.register_blueprint(
        create_api_blueprint(
            show_table_cards=show_table_cards,
            show_positions=show_positions,
            show_moves=show_moves,
            show_solver_link=show_solver_link,
            game_state_service=game_state_service,
            game_data_receiver=game_data_receiver,
        )
    )

    return app
