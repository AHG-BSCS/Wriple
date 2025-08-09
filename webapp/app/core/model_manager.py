"""Model Manager Module"""

import joblib
import json
import numpy as np
import os

# from tensorflow.keras.models import load_model

from config.settings import ModelConfiguration, PredictionConfiguration
from utils.logger import setup_logger


class ModelManager:
    """
    Handles machine learning predictions and data preprocessing 
    for human presence detection for different models
    """
    
    def __init__(self):
        self._model_loaded = False
        self._mode = 1
        self._presence_model = None
        self.thresholds = None
        self.mmWave_thresholds = None
        self.signal_window = PredictionConfiguration.PRED_SIGNAL_WINDOW
        self._logger = setup_logger('ModelManager')

        self.load_threshold()
        # self.load_models(self._mode)
    
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
            # elif mode == 4:
            #     self._presence_model = load_model(ModelConfiguration.CONVLSTM_PATH)
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
    
    def apply_thresholds(self, wriple_list, thresholds):
        """
        Apply the threshold logic on each sample.
        If (value * 2) < threshold → set to 1, else leave as is.

        Args:
            wriple_list: list of 3x16 samples
            thresholds: 3x16 threshold matrix
        
        Returns:
            return: list of 3x16 thresholded samples
        """
        result = []
        for sample in wriple_list:
            updated_sample = []
            for d in range(3):
                updated_doppler = []
                for r in range(16):
                    value = sample[d][r]
                    thresh = thresholds[d][r]
                    if value * 2 < thresh:
                        updated_doppler.append(1.0)
                    else:
                        updated_doppler.append(value)
                updated_sample.append(updated_doppler)
            result.append(updated_sample)
        return result
    
    def apply_moving_average(self, samples_3d, window):
        """
        Apply rolling mean (along time axis) over flattened 3x16 = 48 features.

        Args:
            samples_3d: list of 3x16 samples
            window: number of samples to average over

        Returns:
            return: smoothed list of same shape
        """
        data = np.array([np.array(s).flatten() for s in samples_3d])  # (N, 48)
        smoothed = np.array([
            np.mean(data[i:i + window], axis=0)
            for i in range(len(data) - window + 1)
        ])
        return smoothed
    
    def predict_classical(self, data: list) -> int:
        """
        Predict human presence from amplitude data

        Args:
            data: List of 7 samples of amplitude arrays (each sample: 3 doppler x 16 range gates)

        Returns:
            str: Presence prediction
        """
        try:
            if len(data) < self.signal_window:
                return 'No'

            thresholded_data = self.apply_thresholds(data, self.thresholds)
            X = self.apply_moving_average(thresholded_data, window=self.signal_window)
            
            y_pred = self._presence_model.predict(X)
            presence_pred = 'No' if 0 in y_pred else 'Yes'
            self._logger.info(f'Prediction: {y_pred}')

            return presence_pred
        except Exception as e:
            self._logger.error(f'Error in Logistic Regression prediction: {e}')
            return 'No'

    def predict_neural(self, data: list) -> int:
        """
        Predict human presence using ConvLSTM model

        Args:
            data: List of 7 samples of amplitude arrays (each sample: 3 doppler x 16 range gates)

        Returns:
            str: Presence prediction
        """
        try:
            if len(data) < self.signal_window or not self._model_loaded:
                return 'No'

            thresholded_data = self.apply_thresholds(data, self.thresholds)
            X = self.apply_moving_average(thresholded_data, window=self.signal_window)

            num_sequences = len(X) // self.signal_window
            X_trimmed = X[:num_sequences * self.signal_window]
            X = X_trimmed.reshape((1, self.signal_window, 3, 16, 1))
            
            y_pred = self._presence_model.predict(X)
            presence_pred = 'No' if y_pred[0][0] < 0.7 else 'Yes'
            self._logger.info(f'Prediction: {presence_pred}')

            return presence_pred
        except Exception as e:
            self._logger.error(f'Error in ConvLSTM prediction: {e}')
            return 'No'

    def predict(self, data: list) -> int:
        if self._mode in [1, 2, 3]:
            return self.predict_classical(data)
        elif self._mode in {4, 5}:
            return self.predict_neural(data)


    @property
    def model_loaded(self) -> bool:
        """
        Check if the model is loaded
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self._model_loaded
