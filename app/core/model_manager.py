"""Model Manager Module"""

import threading

import joblib
import numpy as np

from app.config.settings import ModelConfig
from app.utils.logger import setup_logger


class ModelManager:
    """
    Handles machine learning predictions and data preprocessing 
    for human presence detection for different models
    """
    
    def __init__(self):
        self._model = 2
        self._model_loaded = False

        self._presence_model = None
        self._scaler_pca_pipeline = None

        self._xheight = ModelConfig.FEATURE_XHEIGHT
        self._xwidth = ModelConfig.FEATURE_XWIDTH
        self._model_threshold = ModelConfig.PRED_THRESHOLD

        self._logger = setup_logger('ModelManager')
        threading.Thread(target=self._load_model, daemon=True).start()
    
    def _load_model(self):
        """Load all required models"""
        # Peform imports loading here for faster startup time
        # Explicitly import something from sklearn to allow PyInstaller to include sklearn
        from keras.models import load_model
        from sklearn.pipeline import Pipeline
        try:
            if self._model == 1:
                self._presence_model = joblib.load(ModelConfig.RANDOM_FOROREST_PATH)
            elif self._model == 2:
                self._presence_model = load_model(ModelConfig.CONVLSTM_PATH)
                self._scaler_pca_pipeline = joblib.load(ModelConfig.SCALER_PCA_PATH)
            else:
                raise Exception

            self._model_loaded = True
            self._logger.info('Models loaded successfully')
        except Exception as e:
            self._logger.error(f'Error loading models: {e}')
    
    def _predict_classical(self, X: list) -> int:
        """
        Detect human presence using classical ML models

        Args:
            X: List of RSSI mean, RSSI std, 163 amplitude values and amplitude sum difference

        Returns:
            str: Presence prediction
        """
        try:
            X2 = np.asarray(X).reshape(1, -1)
            y_proba = self._presence_model.predict_proba(X2)[0]
            label = 'Yes' if y_proba > self._model_threshold else 'No'
            self._logger.info(f'PRED PROBA: {y_proba}')
            return label
        except Exception as e:
            self._logger.error(f'Error in Logistic Regression prediction: {e}')
            return 'No'
    
    def _predict_convlstm(self, X: list) -> str:
        """
        Detect human presence using ConvLSTM model

        Args:
            X: List of RSSI mean, RSSI std, 163 amplitude values and amplitude sum difference

        Returns:
            str: Presence prediction
        """
        try:
            X = np.asarray(X).reshape(1, -1)                    # shape (1, 166)
            X_trans = self._scaler_pca_pipeline.transform(X)    # shape (1, 20)
            X_seq = X_trans.reshape(1, 1, self._xheight, self._xwidth, 1)
            y_proba = self._presence_model.predict(X_seq, verbose=0).ravel()[0]
            label = 'Yes' if y_proba > self._model_threshold else 'No'
            self._logger.info(f'PRED PROBA: {y_proba}')
            return label
        except Exception as e:
            self._logger.error(f'Error in ConvLSTM prediction: {e}')
            return 'No'

    def predict(self, data: list) -> str:
        """
        Make presence prediction using the selected model

        Args:
            data: Input data for prediction
        
        Returns:
            str: Presence prediction
        """
        if self._model == 1:
            return self._predict_classical(data)
        elif self._model == 2:
            return self._predict_convlstm(data)

    @property
    def model_loaded(self) -> bool:
        """Check if the model is loaded"""
        return self._model_loaded
