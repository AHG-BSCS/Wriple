"""Model Manager Module"""

import os

import joblib
import json
import numpy as np

from keras.models import load_model

from app.config.settings import ModelConfiguration, PredictionConfiguration
from app.utils.logger import setup_logger


class ModelManager:
    """
    Handles machine learning predictions and data preprocessing 
    for human presence detection for different models
    """
    
    def __init__(self):
        self._mode = 4
        self._model_loaded = False

        self._presence_model = None
        self._scaler_pca_pipeline = None

        self.thresholds = None
        self._xheight = PredictionConfiguration.FEATURE_XHEIGHT
        self._xwidth = PredictionConfiguration.FEATURE_XWIDTH
        self._model_threshold = PredictionConfiguration.PRED_THRESHOLD
        self.mmWave_thresholds = None

        self._logger = setup_logger('ModelManager')

        self.load_threshold()
        self.load_models(self._mode)
    
    def load_threshold(self):
        try:
            with open(ModelConfiguration.THRESHOLD_MMWAVE_VIZ_PATH, 'r') as file:
                    self.mmWave_thresholds = json.load(file)
        except Exception as e:
            self._logger.error(f'Error loading mmWave thresholds: {e}')
    
    def load_models(self, mode: int):
        """
        Load all required ML models

        Args:
            mode: Indicate the model to be used
        """
        try:
            if mode == 1:
                self._presence_model = joblib.load(ModelConfiguration.LOGREG_PATH)
            elif mode == 2:
                self._presence_model = joblib.load(ModelConfiguration.RANDFOR_PATH)
            elif mode == 3:
                self._presence_model = joblib.load(ModelConfiguration.ADABOOST_PATH)
            elif mode == 4:
                self._presence_model = load_model(ModelConfiguration.CONVLSTM_PATH)
                self._scaler_pca_pipeline = joblib.load(ModelConfiguration.SCALER_PCA_PATH)
            # elif mode == 5:
            #     self._presence_model = load_model(ModelConfiguration.TCN_PATH)
            else:
                raise Exception

            with open(ModelConfiguration.THRESHOLD_MODEL_PATH, 'r') as file:
                    self.thresholds = json.load(file)
            
            self._model_loaded = True
            self._logger.info('Models loaded successfully')
        except Exception as e:
            self._logger.error(f'Error loading models: {e}')
    
    def predict_classical(self, X: list) -> int:
        """
        Detect human presence using classical ML models

        Args:
            data: List of RSSI mean, RSSI std, 163 amplitude values and amplitude sum difference

        Returns:
            str: Presence prediction
        """
        try:
            X2 = np.asarray(X).reshape(1, -1)
            y_proba = self._presence_model.predict_proba(X2)[0]
            label = 'Yes' if y_proba > self._model_threshold else 'No'
            print(f'PRED PROBA: {y_proba}')
            return label
        except Exception as e:
            self._logger.error(f'Error in Logistic Regression prediction: {e}')
            return 'No'
    
    def predict_convlstm(self, X: list) -> str:
        """
        Detect human presence using ConvLSTM model

        Args:
            data: List of RSSI mean, RSSI std, 163 amplitude values and amplitude sum difference

        Returns:
            str: Presence prediction
        """
        try:
            X = np.asarray(X).reshape(1, -1)            # shape (1, 166)
            X_trans = self._scaler_pca_pipeline.transform(X) # shape (1, 20)
            X_seq = X_trans.reshape(1, 1, self._xheight, self._xwidth, 1)
            y_proba = self._presence_model.predict(X_seq, verbose=0).ravel()[0]
            label = 'Yes' if y_proba > self._model_threshold else 'No'
            print(f'PRED PROBA: {y_proba}')
            return label
        except Exception as e:
            self._logger.error(f'Error in ConvLSTM prediction: {e}')
            return 'No'

    def predict(self, data: list) -> int:
        """
        Make presence prediction using the selected model

        Args:
            data: Input data for prediction
        
        Returns:
            int: Presence prediction (1 for presence, 0 for absence)
        """
        if self._mode in [1, 2, 3]:
            return self.predict_classical(data)
        elif self._mode == 4:
            return self.predict_convlstm(data)


    @property
    def model_loaded(self) -> bool:
        """
        Check if the model is loaded
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self._model_loaded
