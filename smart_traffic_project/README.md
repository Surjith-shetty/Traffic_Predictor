# 🚦 Smart Local Traffic Flow Predictor

## AI-Powered Route Optimization & Traffic Prediction System

A comprehensive machine learning system that predicts short-term traffic flow and provides intelligent route scoring to improve upon traditional navigation systems like Google Maps, especially for local and micro-location scenarios.

## 🎯 Project Overview

This system addresses key limitations in current traffic prediction:
- **Real-time ML Predictions**: 5-15 minute traffic flow forecasting
- **Multi-factor Route Scoring**: Considers traffic, weather, events, and road conditions
- **Local Focus**: Optimized for smaller zones, campuses, and semi-urban areas
- **Explainable AI**: Uses interpretable models instead of black-box solutions

## 🏆 Model Performance

| Model | MAE | RMSE | R² Score | Accuracy |
|-------|-----|------|----------|----------|
| Linear Regression | 52.97 | 72.86 | 0.8897 | 88.97% |
| Polynomial Regression | 32.59 | 41.75 | 0.9638 | 96.38% |
| KNN Regressor | 29.95 | 40.57 | 0.9658 | 96.58% |
| Decision Tree | 28.01 | 36.63 | 0.9721 | 97.21% |
| **Random Forest** | **25.46** | **32.79** | **0.9777** | **97.77%** |

## 🚀 Quick Start

### Option 1: Easy Launch
```bash
python run_app.py
```

### Option 2: Manual Launch
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The application will automatically:
1. Generate realistic traffic dataset (if not exists)
2. Train all ML models
3. Launch the interactive dashboard
4. Open in your browser at `http://localhost:8501`

## 📊 Features

### 🔮 Live Prediction
- Real-time traffic flow prediction
- Route efficiency scoring (0-100)
- Weather integration
- Interactive parameter adjustment
- Smart recommendations

### 📈 Model Analysis
- Performance comparison of all 5 models
- Feature importance visualization
- Accuracy metrics and insights
- Model interpretability

### 📊 Data Insights
- Traffic patterns by hour/day
- Weather impact analysis
- Speed vs traffic correlations
- Dataset statistics

### 🗺️ Route Comparison
- Multi-route optimization
- Scenario-based analysis
- 24-hour traffic predictions
- Best route recommendations

## 🧮 Route Scoring Formula

```
RouteScore = w1*(1 - PredictedTraffic/MaxTraffic)
           + w2*(AvgSpeed/MaxSpeed)
           + w3*(1 - RainIntensity)
           + w4*(1 - EventImpact)
```

Where weights are optimized for: w1=0.4, w2=0.3, w3=0.2, w4=0.1

## 📁 Project Structure

```
smart_traffic_project/
├── app.py                 # Main Streamlit application
├── ml_models.py          # ML pipeline & model training
├── data_generator.py     # Realistic dataset generation
├── weather_api.py        # Weather data integration
├── run_app.py           # Easy launcher script
├── requirements.txt      # Dependencies
├── README.md            # This file
├── traffic_data.csv     # Generated dataset
├── trained_models.pkl   # Saved ML models
├── scaler.pkl          # Feature scaler
└── poly_features.pkl   # Polynomial features
```

## 🧰 Technology Stack

- **ML Framework**: scikit-learn
- **Data Processing**: pandas, numpy
- **Visualization**: plotly, matplotlib, seaborn
- **Web Interface**: streamlit
- **Weather API**: OpenWeatherMap (with mock fallback)
- **Maps**: folium (optional)

## 🎯 Key Features & Innovations

### 1. **Multi-Model Comparison**
- 5 different regression algorithms
- Comprehensive performance metrics
- Automatic best model selection

### 2. **Real-World Data Integration**
- Time-based patterns (rush hours, weekends)
- Weather conditions (rain, temperature, humidity)
- Special events and holidays
- Road speed variations

### 3. **Intelligent Route Scoring**
- Multi-factor weighted algorithm
- Real-time condition adjustment
- Comparative route analysis
- Actionable recommendations

### 4. **Interactive Dashboard**
- Live prediction interface
- Parameter adjustment controls
- Visual analytics and insights
- Route comparison tools

## 📈 Model Insights

### Feature Importance (Random Forest):
1. **avg_speed** (83.13%) - Most critical factor
2. **hour** (4.76%) - Time-of-day patterns
3. **rain_intensity** (4.26%) - Weather impact
4. **rush_hour** (2.62%) - Peak hour effects
5. **event_flag** (2.22%) - Special events

### Performance Highlights:
- **97.77% accuracy** with Random Forest
- **±25 vehicles/hour** prediction precision
- **Real-time processing** capability
- **Explainable predictions** with feature importance

## 🔧 Customization

### Adding New Features:
1. Modify `data_generator.py` to include new data columns
2. Update feature lists in `ml_models.py`
3. Retrain models with new data

### Weather API Integration:
1. Get free API key from OpenWeatherMap
2. Replace `demo_key` in `weather_api.py`
3. Restart application for live weather data

### Route Scoring Weights:
Adjust weights in `calculate_route_score()` method based on your priorities:
- Increase w1 for traffic priority
- Increase w2 for speed priority
- Increase w3 for weather sensitivity
- Increase w4 for event impact

## 🎓 Educational Value

This project demonstrates:
- **End-to-end ML pipeline** development
- **Real-world problem solving** with AI
- **Model comparison** and selection
- **Interactive application** development
- **Data visualization** techniques
- **API integration** patterns

## 🚀 Future Enhancements

- **IoT Integration**: Real traffic sensor data
- **Deep Learning**: LSTM for time series
- **Mobile App**: React Native interface
- **Real-time Updates**: Live data streaming
- **Map Integration**: Visual route display
- **Smart City APIs**: Government data sources

## 📝 License

This project is for educational purposes. Feel free to use and modify for learning and research.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional ML models
- Better weather integration
- Enhanced visualizations
- Mobile responsiveness
- Performance optimizations

---

**Built with ❤️ for smarter traffic management**