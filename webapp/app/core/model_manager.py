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
        self._logger = setup_logger('ModelManager')

        # Temporarily avoid loading models during development
        # self.load_models()
    
    def load_models(self):
        """Load all required ML models"""
        try:
            if os.path.exists(ModelConfiguration.PCA_PATH) and os.path.exists(ModelConfiguration.LOGREG_PATH):
                self._pca_model = joblib.load(ModelConfiguration.PCA_PATH)
                self._presence_model = joblib.load(ModelConfiguration.LOGREG_PATH)
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
            int: Presence prediction. 0 for absense, 1 for presence
        """
        try:
            if amplitude_data is None:
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
        """
        Check if the model is loaded
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self._model_loaded
