import numpy as np

from src.core.service.template_matcher_service import TemplateMatchService
from src.core.utils.opencv_utils import coords_to_search_region

ACTION_POSITIONS = {
    1: (300, 440, 99, 99),  # Bottom center (hero)
    2: (10, 400, 99, 99),  # Left side
    3: (25, 120, 99, 99),  # Top left
    4: (315, 80, 99, 99),  # Top center
    5: (580, 130, 99, 99),  # Top right
    6: (580, 380, 99, 99),  # Right side
}

def get_street_actions(image: np.ndarray):
    return get_player_actions(image)


def get_player_actions(image: np.ndarray):
    player_actions = {}

    for player_id, region in ACTION_POSITIONS.items():
        search_region = coords_to_search_region(
            x=region[0],
            y=region[1],
            w=region[2],
            h=region[3],
        )

        actions = TemplateMatchService.find_jurojin_actions(image, search_region=search_region)
        player_actions[player_id] = actions

    return player_actions
