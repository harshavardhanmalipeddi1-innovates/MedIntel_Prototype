import numpy as np
from typing import Dict, List


class FeatureProcessor:
    """
    Converts clinical input data into ML feature vectors.
    """

    def __init__(self):
        self.feature_names = [
            "age",
            "fever",
            "cough",
            "breathlessness",
            "chest_pain"
        ]

    def process(self, clinical_data: Dict) -> np.ndarray:
        """
        Convert dictionary input into numerical feature vector.
        """

        features = []

        for name in self.feature_names:
            value = clinical_data.get(name, 0)

            if isinstance(value, bool):
                value = int(value)

            features.append(float(value))

        return np.array(features)

    def get_feature_schema(self) -> List[str]:
        return self.feature_names