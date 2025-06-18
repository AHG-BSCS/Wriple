"""Model Manager Module"""

import joblib
import os

from config.settings import ModelConfiguration
from utils.logger import setup_logger


class ModelManager:
    """
    Handles machine learning predictions and data preprocessing 
    for human presence detection for different models
    """
    
    def __init__(self):
        self._model_loaded = False
        self._pca_model = None
        self._presence_model = None
        self._config = ModelConfiguration
        self._logger = setup_logger('ModelManager')

        self.load_models()
    
    def load_models(self):
        """Load all required ML models"""
        try:
            if os.path.exists(self._config.PCA_PATH) and os.path.exists(self._config.LOGREG_PATH):
                self._pca_model = joblib.load(self._config.PCA_PATH)
                self._presence_model = joblib.load(self._config.LOGREG_PATH)
                self._model_loaded = True
                self._logger.info("Models loaded successfully")
        except Exception as e:
            self._logger.error(f"Error loading models: {e}")
    
    def predict(self, amplitude_data: list) -> int:
        """
        Predict human presence from amplitude data
        
        Args:
            amplitude_data: List of amplitude arrays
            
        Returns:
            int: Presence prediction (0 or 1)
        """
        try:
            if len(amplitude_data) > 2:
                return 0
            
            # Use the newest data for prediction
            X = amplitude_data[:2]
            X_pca = self._pca_model.transform(X)
            y_pred = self._presence_model.predict(X_pca)
            presence_pred = 0 if 0 in y_pred else 1
            self._logger.debug(f"Prediction: {presence_pred}")
            
            return presence_pred
            
        except Exception as e:
            self._logger.error(f"Error in logistic regression prediction: {e}")
            return 0

    @property
    def model_loaded(self) -> bool:
        """Check if the model is loaded"""
        return self._model_loaded
