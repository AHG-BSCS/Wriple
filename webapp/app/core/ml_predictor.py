"""
Handles machine learning predictions and data preprocessing 
for human presence detection for different models
"""

class MLPredictor:
    """Handles ML predictions for presence detection"""
    
    def __init__(self, pca_model, presence_model):
        self.pca_model = pca_model
        self.presence_model = presence_model
    
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
            print(f"Error in prediction: {e}")
            return 0
