"""Handles loading and managing ML models for presence detection"""

import os
import joblib
from config.settings import ModelConfiguration
from core.ml_predictor import MLPredictor
from utils.logger import setup_logger


class ModelLoader:
    """Manages ML model loading and validation"""
    
    def __init__(self):
        self.config = ModelConfiguration
        self.is_model_loaded = False
        self.pca_model = None
        self.presence_model = None
        self.logger = setup_logger('ModelLoader')
    
    def load_models(self):
        """Load all required ML models"""
        try:
            if os.path.exists(self.config.PCA_PATH) and os.path.exists(self.config.LOGREG_PATH):
                pca_model = joblib.load(self.config.PCA_PATH)
                presence_model = joblib.load(self.config.LOGREG_PATH)
                self.model_loaded = True
                self.logger.info("Models loaded successfully")
                return MLPredictor(pca_model, presence_model)
            
            return None
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return None
