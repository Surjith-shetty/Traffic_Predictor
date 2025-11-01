import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

class TrafficPredictor:
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.poly_features = PolynomialFeatures(degree=2, include_bias=False)
        self.feature_names = []
        self.results = {}
        
    def load_data(self, file_path):
        """Load and prepare the dataset"""
        self.df = pd.read_csv(file_path)
        print(f"Dataset loaded: {self.df.shape}")
        return self.df
    
    def prepare_features(self):
        """Prepare features for training"""
        # Select features
        feature_cols = ['hour', 'day_of_week', 'is_weekend', 'rain_intensity', 
                       'temperature', 'humidity', 'event_flag', 'rush_hour', 'avg_speed']
        
        X = self.df[feature_cols]
        y = self.df['traffic_flow']
        
        self.feature_names = feature_cols
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled
    
    def train_all_models(self):
        """Train all 5 models and compare performance"""
        X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled = self.prepare_features()
        
        # 1. Linear Regression
        print("Training Linear Regression...")
        lr = LinearRegression()
        lr.fit(X_train_scaled, y_train)
        lr_pred = lr.predict(X_test_scaled)
        self.models['Linear Regression'] = lr
        
        # 2. Polynomial Regression
        print("Training Polynomial Regression...")
        X_train_poly = self.poly_features.fit_transform(X_train_scaled)
        X_test_poly = self.poly_features.transform(X_test_scaled)
        poly_lr = LinearRegression()
        poly_lr.fit(X_train_poly, y_train)
        poly_pred = poly_lr.predict(X_test_poly)
        self.models['Polynomial Regression'] = poly_lr
        
        # 3. KNN Regressor
        print("Training KNN Regressor...")
        knn = KNeighborsRegressor(n_neighbors=5)
        knn.fit(X_train_scaled, y_train)
        knn_pred = knn.predict(X_test_scaled)
        self.models['KNN Regressor'] = knn
        
        # 4. Decision Tree
        print("Training Decision Tree...")
        dt = DecisionTreeRegressor(random_state=42, max_depth=10)
        dt.fit(X_train, y_train)
        dt_pred = dt.predict(X_test)
        self.models['Decision Tree'] = dt
        
        # 5. Random Forest (Main Model)
        print("Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=15)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        self.models['Random Forest'] = rf
        
        # Store predictions and actual values
        predictions = {
            'Linear Regression': lr_pred,
            'Polynomial Regression': poly_pred,
            'KNN Regressor': knn_pred,
            'Decision Tree': dt_pred,
            'Random Forest': rf_pred
        }
        
        # Calculate metrics for all models
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
        
        # Store test data for visualization
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
        """Predict traffic using the best model (Random Forest)"""
        features = np.array([[hour, day_of_week, is_weekend, rain_intensity,
                            temperature, humidity, event_flag, rush_hour, avg_speed]])
        
        rf_model = self.models['Random Forest']
        prediction = rf_model.predict(features)[0]
        return max(0, prediction)
    
    def calculate_route_score(self, predicted_traffic, avg_speed, rain_intensity, event_impact):
        """Calculate route score using the weighted formula"""
        max_traffic = 800  # Based on dataset
        max_speed = 60
        
        # Weights (can be optimized)
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
        joblib.dump(self.poly_features, 'poly_features.pkl')
        print("Models saved successfully!")
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            self.models = joblib.load('trained_models.pkl')
            self.scaler = joblib.load('scaler.pkl')
            self.poly_features = joblib.load('poly_features.pkl')
            print("Models loaded successfully!")
            return True
        except:
            print("No saved models found. Please train models first.")
            return False

def main():
    # Initialize predictor
    predictor = TrafficPredictor()
    
    # Load data
    predictor.load_data('traffic_data.csv')
    
    # Train all models
    results = predictor.train_all_models()
    
    # Print results
    print("\n" + "="*60)
    print("MODEL COMPARISON RESULTS")
    print("="*60)
    
    for model_name, metrics in results.items():
        print(f"\n{model_name}:")
        print(f"  MAE:  {metrics['MAE']:.2f}")
        print(f"  RMSE: {metrics['RMSE']:.2f}")
        print(f"  R²:   {metrics['R2']:.4f}")
    
    # Feature importance
    feature_imp = predictor.get_feature_importance()
    print(f"\n{'='*60}")
    print("FEATURE IMPORTANCE (Random Forest)")
    print("="*60)
    for _, row in feature_imp.iterrows():
        print(f"{row['feature']:15}: {row['importance']:.4f}")
    
    # Save models
    predictor.save_models()
    
    # Example prediction
    print(f"\n{'='*60}")
    print("EXAMPLE PREDICTION")
    print("="*60)
    
    # Rush hour, rainy day
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

if __name__ == "__main__":
    main()