from typing import List

import numpy as np

from src.domain.readed_card import ReadedCard


class CardReader:
    def read(self, image: np.ndarray) -> List[ReadedCard]:
        pass