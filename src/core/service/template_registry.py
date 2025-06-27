import os
from typing import Dict, Optional
import numpy as np

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
    def move_templates(self) -> Dict[str, np.ndarray]:
        if self._move_templates is None:
            self._move_templates = self._load_template_category("turn_options")
        return self._move_templates

    def _load_template_category(self, category: str) -> Dict[str, np.ndarray]:
        templates_path = os.path.join(self._templates_dir, category)

        if not os.path.exists(templates_path):
            print(f"⚠️  Template directory not found: {templates_path}")
            return {}

        try:
            return load_templates(templates_path)
        except Exception as e:
            print(f"❌ Error loading {category} templates: {str(e)}")
            return {}

    def reload_templates(self):
        print(f"🔄 Reloading all templates for {self.country}")
        self._player_templates = None
        self._table_templates = None
        self._position_templates = None
        self._move_templates = None

    def has_player_templates(self) -> bool:
        return bool(self.player_templates)

    def has_table_templates(self) -> bool:
        return bool(self.table_templates)

    def has_position_templates(self) -> bool:
        return bool(self.position_templates)

    def has_move_templates(self) -> bool:
        return bool(self.move_templates)

    def get_template_stats(self) -> Dict[str, int]:
        return {
            'player_cards': len(self.player_templates),
            'table_cards': len(self.table_templates),
            'positions': len(self.position_templates),
            'turn_options': len(self.move_templates)
        }