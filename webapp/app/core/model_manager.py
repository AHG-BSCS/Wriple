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
        self.model_loaded = False
        self.pca_model = None
        self.presence_model = None
        self.config = ModelConfiguration
        self.logger = setup_logger('ModelManager')

        self.load_models()
    
    def load_models(self):
        """Load all required ML models"""
        try:
            if os.path.exists(self.config.PCA_PATH) and os.path.exists(self.config.LOGREG_PATH):
                self.pca_model = joblib.load(self.config.PCA_PATH)
                self.presence_model = joblib.load(self.config.LOGREG_PATH)
                self.model_loaded = True
                self.logger.info("Models loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return None
    
    def predict(self, amplitude_data):
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
            X_pca = self.pca_model.transform(X)
            y_pred = self.presence_model.predict(X_pca)
            presence_pred = 0 if 0 in y_pred else 1
            print(f"Prediction: {y_pred}")

            return presence_pred
            
        except Exception as e:
            self.logger.error(f"Error in logistic regression prediction: {e}")
            return 0
