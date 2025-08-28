from pathlib import Path
from typing import Dict, Optional

import numpy as np
from loguru import logger

from table_detector.utils.opencv_utils import read_cv2_image


class TemplateRegistry:
    def __init__(self, country: str, project_root: str):
        self.country = country
        self.project_root = project_root

        self._player_templates: Optional[Dict[str, np.ndarray]] = None
        self._table_templates: Optional[Dict[str, np.ndarray]] = None
        self._position_templates: Optional[Dict[str, np.ndarray]] = None
        self._actions_templates: Optional[Dict[str, np.ndarray]] = None
        self._jurojin_action_templates: Optional[Dict[str, np.ndarray]] = None

        self._templates_dir = Path(project_root) / "apps" / "table_detector" / "resources" / "templates" / country

    @staticmethod
    def load_templates(template_dir):
        logger.info(f"📁 Loading templates from: {template_dir}")

        templates = {}
        template_path = Path(template_dir)
        for tpl_path in template_path.glob('*.png'):
            name = tpl_path.stem
            tpl = read_cv2_image(tpl_path)
            templates[name] = tpl

        if not templates:
            raise Exception("❌ No player templates loaded! Please check the templates directory.")
        else:
            logger.info(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")

        return templates

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
        if self._actions_templates is None:
            self._actions_templates = self._load_template_category("actions")
        return self._actions_templates

    @property
    def jurojin_action_templates(self) -> Dict[str, np.ndarray]:
        if self._jurojin_action_templates is None:
            self._jurojin_action_templates = self._load_template_category("moves")
        return self._jurojin_action_templates

    def _load_template_category(self, category: str) -> Dict[str, np.ndarray]:
        templates_path = self._templates_dir / category

        if not templates_path.exists():
            logger.error(f"⚠️  Template directory not found: {templates_path}")
            return {}

        try:
            return TemplateRegistry.load_templates(templates_path)
        except Exception as e:
            logger.error(f"❌ Error loading {category} templates: {str(e)}")
            return {}

    def has_position_templates(self) -> bool:
        return bool(self.position_templates)
