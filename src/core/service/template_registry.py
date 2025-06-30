import os
from typing import Dict, Optional
import numpy as np
from loguru import logger

from src.core.utils.opencv_utils import load_templates


class TemplateRegistry:
    def __init__(self, country: str, project_root: str):
        self.country = country
        self.project_root = project_root

        self._player_templates: Optional[Dict[str, np.ndarray]] = None
        self._table_templates: Optional[Dict[str, np.ndarray]] = None
        self._position_templates: Optional[Dict[str, np.ndarray]] = None
        self._move_templates: Optional[Dict[str, np.ndarray]] = None

        self._templates_dir = os.path.join(project_root, "resources", "templates", country)

    @property
    def player_templates(self) -> Dict[str, np.ndarray]:
        if self._player_templates is None:
            self._player_templates = self._load_template_category("player_cards")
        return self._player_templates

    @property
    def table_templates(self) -> Dict[str, np.ndarray]:
        if self._table_templates is None:
            self._table_templates = self._load_template_category("table_cards")
        return self._table_templates

    @property
    def position_templates(self) -> Dict[str, np.ndarray]:
        if self._position_templates is None:
            self._position_templates = self._load_template_category("positions")
        return self._position_templates

    @property
    def action_templates(self) -> Dict[str, np.ndarray]:
        if self._move_templates is None:
            self._move_templates = self._load_template_category("actions")
        return self._move_templates

    def _load_template_category(self, category: str) -> Dict[str, np.ndarray]:
        templates_path = os.path.join(self._templates_dir, category)

        if not os.path.exists(templates_path):
            logger.error(f"⚠️  Template directory not found: {templates_path}")
            return {}

        try:
            return load_templates(templates_path)
        except Exception as e:
            logger.error(f"❌ Error loading {category} templates: {str(e)}")
            return {}

    def has_position_templates(self) -> bool:
        return bool(self.position_templates)
