import numpy as np

from src.core.service.matcher.jurojin_action_matcher import JurojinActionMatcher
from src.core.service.template_registry import TemplateRegistry
from src.core.utils.opencv_utils import coords_to_search_region

ACTION_POSITIONS = {
    1: (300, 440, 99, 99),  # Bottom center (hero)
    2: (10, 400, 99, 99),  # Left side
    3: (25, 120, 99, 99),  # Top left
    4: (315, 80, 99, 99),  # Top center
    5: (580, 130, 99, 99),  # Top right
    6: (580, 380, 99, 99),  # Right side
}

def get_street_actions(image: np.ndarray, project_root):
    return get_player_actions(image, project_root)


def get_player_actions(image: np.ndarray, project_root):
    template_registry = TemplateRegistry("canada", project_root)

    player_actions = {}

    for player_id, region in ACTION_POSITIONS.items():
        search_region = coords_to_search_region(
            x=region[0],
            y=region[1],
            w=region[2],
            h=region[3],
        )

        jurojin_action_matcher = JurojinActionMatcher(template_registry.jurojin_action_templates, search_region=search_region)
        actions = jurojin_action_matcher.read(image)
        player_actions[player_id] = actions

    return player_actions
