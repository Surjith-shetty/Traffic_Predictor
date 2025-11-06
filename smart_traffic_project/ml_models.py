import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

class TrafficPredictor:
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        self.results = {}
        
    def load_data(self, file_path):
        """Load and prepare the dataset"""
        self.df = pd.read_csv(file_path)
        print(f"Dataset loaded: {self.df.shape}")
        return self.df
    
    def prepare_features(self):
        """Prepare features for training"""
        feature_cols = ['hour', 'day_of_week', 'is_weekend', 'rain_intensity', 
                       'temperature', 'humidity', 'event_flag', 'rush_hour', 'avg_speed']
        
        X = self.df[feature_cols]
        y = self.df['traffic_flow']
        
        self.feature_names = feature_cols
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled
    
    def train_models(self):
        """Train Linear Regression and Random Forest models"""
        X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled = self.prepare_features()
        
        print("Training Linear Regression...")
        lr = LinearRegression()
        lr.fit(X_train_scaled, y_train)
        lr_pred = lr.predict(X_test_scaled)
        self.models['Linear Regression'] = lr
        
        print("Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=15)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        self.models['Random Forest'] = rf
        
        predictions = {
            'Linear Regression': lr_pred,
            'Random Forest': rf_pred
        }
        
        self.results = {}
        for name, pred in predictions.items():
            mae = mean_absolute_error(y_test, pred)
            rmse = np.sqrt(mean_squared_error(y_test, pred))
            r2 = r2_score(y_test, pred)
            
            self.results[name] = {
                'MAE': mae,
                'RMSE': rmse,
                'R2': r2,
                'predictions': pred
            }
        
        self.y_test = y_test
        self.X_test = X_test
        
        return self.results
    
    def get_feature_importance(self):
        """Get feature importance from Random Forest"""
        if 'Random Forest' in self.models:
            rf_model = self.models['Random Forest']
            importance = rf_model.feature_importances_
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False)
            return feature_importance
        return None
    
    def predict_traffic(self, hour, day_of_week, is_weekend, rain_intensity, 
                       temperature, humidity, event_flag, rush_hour, avg_speed):
        """Predict traffic using Random Forest (primary predictor)"""
        features = np.array([[hour, day_of_week, is_weekend, rain_intensity,
                            temperature, humidity, event_flag, rush_hour, avg_speed]])
        
        # Use Random Forest as primary predictor
        rf_model = self.models['Random Forest']
        prediction = rf_model.predict(features)[0]
        return max(0, prediction)
    
    def compare_predictions(self, hour, day_of_week, is_weekend, rain_intensity, 
                          temperature, humidity, event_flag, rush_hour, avg_speed):
        """Compare predictions from both Linear Regression and Random Forest"""
        features = np.array([[hour, day_of_week, is_weekend, rain_intensity,
                            temperature, humidity, event_flag, rush_hour, avg_speed]])
        
        # Linear Regression prediction (scaled features)
        features_scaled = self.scaler.transform(features)
        lr_prediction = self.models['Linear Regression'].predict(features_scaled)[0]
        
        # Random Forest prediction (original features)
        rf_prediction = self.models['Random Forest'].predict(features)[0]
        
        return {
            'Linear Regression': max(0, lr_prediction),
            'Random Forest': max(0, rf_prediction)
        }
    
    def calculate_route_score(self, predicted_traffic, avg_speed, rain_intensity, event_impact):
        """Calculate route score using the weighted formula"""
        max_traffic = 800  # Based on dataset
        max_speed = 60
        
        w1, w2, w3, w4 = 0.4, 0.3, 0.2, 0.1
        
        score = (w1 * (1 - predicted_traffic/max_traffic) + 
                w2 * (avg_speed/max_speed) + 
                w3 * (1 - rain_intensity) + 
                w4 * (1 - event_impact))
        
        return min(100, max(0, score * 100))
    
    def save_models(self):
        """Save trained models"""
        joblib.dump(self.models, 'trained_models.pkl')
        joblib.dump(self.scaler, 'scaler.pkl')
        print("Models saved successfully!")
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            self.models = joblib.load('trained_models.pkl')
            self.scaler = joblib.load('scaler.pkl')
            print("Models loaded successfully!")
            return True
        except:
            print("No saved models found. Please train models first.")
            return False

def main():
    predictor = TrafficPredictor()
    
    predictor.load_data('traffic_data.csv')
    
    results = predictor.train_models()
    
    print("\n" + "="*50)
    print("MODEL PERFORMANCE COMPARISON")
    print("="*50)
    
    for model_name, metrics in results.items():
        print(f"\n{model_name}:")
        print(f"  MAE:  {metrics['MAE']:.2f}")
        print(f"  RMSE: {metrics['RMSE']:.2f}")
        print(f"  R²:   {metrics['R2']:.4f}")
    
    feature_imp = predictor.get_feature_importance()
    print(f"\n{'='*50}")
    print("FEATURE IMPORTANCE (Random Forest)")
    print("="*50)
    for _, row in feature_imp.iterrows():
        print(f"{row['feature']:15}: {row['importance']:.4f}")
    
    predictor.save_models()
    
    print(f"\n{'='*50}")
    print("EXAMPLE PREDICTION (Random Forest)")
    print("="*50)
    
    traffic_pred = predictor.predict_traffic(
        hour=8, day_of_week=1, is_weekend=0, rain_intensity=0.5,
        temperature=22, humidity=80, event_flag=1, rush_hour=1, avg_speed=25
    )
    
    route_score = predictor.calculate_route_score(
        predicted_traffic=traffic_pred, avg_speed=25, 
        rain_intensity=0.5, event_impact=0.3
    )
    
    print(f"Predicted Traffic Flow: {traffic_pred:.0f} vehicles/hour")
    print(f"Route Efficiency Score: {route_score:.1f}/100")
    
    print(f"\n{'='*50}")
    print("MODEL COMPARISON FOR SAME INPUT")
    print("="*50)
    
    comparison = predictor.compare_predictions(
        hour=8, day_of_week=1, is_weekend=0, rain_intensity=0.5,
        temperature=22, humidity=80, event_flag=1, rush_hour=1, avg_speed=25
    )
    
    for model, pred in comparison.items():
        print(f"{model:18}: {pred:.0f} vehicles/hour")
    
    print(f"\nPrimary Predictor: Random Forest (Higher Accuracy: R² = {predictor.results['Random Forest']['R2']:.4f})")
    print(f"Backup Model: Linear Regression (R² = {predictor.results['Linear Regression']['R2']:.4f})")

if __name__ == "__main__":
    main()
