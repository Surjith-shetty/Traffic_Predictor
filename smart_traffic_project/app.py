import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import sys

# Import our custom modules
from ml_models import TrafficPredictor
from weather_api import WeatherAPI
from data_generator import generate_traffic_dataset

# Page configuration
st.set_page_config(
    page_title="Smart Traffic Flow Predictor",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .prediction-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .route-score {
        font-size: 3rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_prepare_data():
    """Load or generate dataset"""
    if not os.path.exists('traffic_data.csv'):
        st.info("Generating traffic dataset...")
        df = generate_traffic_dataset(5000)
        df.to_csv('traffic_data.csv', index=False)
    else:
        df = pd.read_csv('traffic_data.csv')
    return df

@st.cache_resource
def initialize_predictor():
    """Initialize and train the predictor"""
    predictor = TrafficPredictor()
    
    # Try to load existing models
    if not predictor.load_models():
        st.info("Training ML models... This may take a moment.")
        predictor.load_data('traffic_data.csv')
        predictor.train_all_models()
        predictor.save_models()
    
    return predictor

def main():
    # Header
    st.markdown('<h1 class="main-header">🚦 Smart Local Traffic Flow Predictor</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered Route Optimization & Traffic Prediction System</p>', unsafe_allow_html=True)
    
    # Initialize components
    df = load_and_prepare_data()
    predictor = initialize_predictor()
    weather_api = WeatherAPI()
    
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Choose Function",
        ["🔮 Live Prediction", "📊 Model Analysis", "📈 Data Insights", "🗺️ Route Comparison"]
    )
    
    if page == "🔮 Live Prediction":
        show_live_prediction(predictor, weather_api)
    elif page == "📊 Model Analysis":
        show_model_analysis(predictor, df)
    elif page == "📈 Data Insights":
        show_data_insights(df)
    elif page == "🗺️ Route Comparison":
        show_route_comparison(predictor, weather_api)

def show_live_prediction(predictor, weather_api):
    st.header("🔮 Real-Time Traffic Prediction")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📍 Current Conditions")
        
        # Get current weather
        weather_data = weather_api.get_weather_data()
        
        # Current time
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()
        is_weekend = 1 if current_day >= 5 else 0
        rush_hour = 1 if (7 <= current_hour <= 9) or (17 <= current_hour <= 19) else 0
        
        # Display current conditions
        st.metric("🌡️ Temperature", f"{weather_data['temperature']}°C")
        st.metric("💧 Humidity", f"{weather_data['humidity']}%")
        st.metric("🌧️ Rain Intensity", f"{weather_data['rain_intensity']:.1f}")
        st.metric("⏰ Current Hour", f"{current_hour}:00")
        
        # Manual overrides
        st.subheader("🎛️ Adjust Parameters")
        
        hour_input = st.slider("Hour of Day", 0, 23, current_hour)
        day_input = st.selectbox("Day of Week", 
                                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                                index=current_day)
        
        rain_input = st.slider("Rain Intensity", 0.0, 1.0, weather_data['rain_intensity'], 0.1)
        temp_input = st.slider("Temperature (°C)", 10, 40, int(weather_data['temperature']))
        humidity_input = st.slider("Humidity (%)", 20, 100, int(weather_data['humidity']))
        
        event_flag = st.checkbox("Special Event Happening", False)
        avg_speed_input = st.slider("Current Average Speed (km/h)", 10, 60, 35)
    
    with col2:
        st.subheader("🎯 Prediction Results")
        
        # Calculate derived features
        day_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day_input)
        is_weekend_calc = 1 if day_of_week >= 5 else 0
        rush_hour_calc = 1 if (7 <= hour_input <= 9) or (17 <= hour_input <= 19) else 0
        
        # Make prediction
        predicted_traffic = predictor.predict_traffic(
            hour=hour_input,
            day_of_week=day_of_week,
            is_weekend=is_weekend_calc,
            rain_intensity=rain_input,
            temperature=temp_input,
            humidity=humidity_input,
            event_flag=1 if event_flag else 0,
            rush_hour=rush_hour_calc,
            avg_speed=avg_speed_input
        )
        
        # Calculate route score
        route_score = predictor.calculate_route_score(
            predicted_traffic=predicted_traffic,
            avg_speed=avg_speed_input,
            rain_intensity=rain_input,
            event_impact=0.3 if event_flag else 0.0
        )
        
        # Display prediction in a nice box
        st.markdown(f"""
        <div class="prediction-box">
            <h3>🚗 Traffic Prediction</h3>
            <div style="font-size: 2.5rem; font-weight: bold;">
                {predicted_traffic:.0f} vehicles/hour
            </div>
            <h3>🎯 Route Efficiency Score</h3>
            <div class="route-score" style="color: {'#4CAF50' if route_score >= 70 else '#FF9800' if route_score >= 40 else '#F44336'}">
                {route_score:.1f}/100
            </div>
            <p>{'🟢 Excellent Route' if route_score >= 70 else '🟡 Moderate Traffic' if route_score >= 40 else '🔴 Heavy Congestion'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Traffic level indicator
        if predicted_traffic < 200:
            traffic_level = "🟢 Light Traffic"
            color = "#4CAF50"
        elif predicted_traffic < 400:
            traffic_level = "🟡 Moderate Traffic"
            color = "#FF9800"
        elif predicted_traffic < 600:
            traffic_level = "🟠 Heavy Traffic"
            color = "#FF5722"
        else:
            traffic_level = "🔴 Very Heavy Traffic"
            color = "#F44336"
        
        st.markdown(f"""
        <div style="background: {color}; padding: 1rem; border-radius: 10px; color: white; text-align: center; margin: 1rem 0;">
            <h3>{traffic_level}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendations
        st.subheader("💡 Recommendations")
        
        recommendations = []
        if route_score < 40:
            recommendations.append("🚨 Consider alternative routes")
            recommendations.append("⏰ Delay travel if possible")
        if rain_input > 0.3:
            recommendations.append("🌧️ Drive carefully due to rain")
        if rush_hour_calc:
            recommendations.append("⏰ Peak hour - expect delays")
        if event_flag:
            recommendations.append("🎪 Event traffic - plan extra time")
        
        if not recommendations:
            recommendations.append("✅ Good conditions for travel")
        
        for rec in recommendations:
            st.write(rec)

def show_model_analysis(predictor, df):
    st.header("📊 Machine Learning Model Analysis")
    
    # Load results if available
    if hasattr(predictor, 'results') and predictor.results:
        results = predictor.results
    else:
        st.info("Training models for analysis...")
        predictor.load_data('traffic_data.csv')
        results = predictor.train_all_models()
    
    # Model comparison table
    st.subheader("🏆 Model Performance Comparison")
    
    comparison_data = []
    for model_name, metrics in results.items():
        comparison_data.append({
            'Model': model_name,
            'MAE': f"{metrics['MAE']:.2f}",
            'RMSE': f"{metrics['RMSE']:.2f}",
            'R² Score': f"{metrics['R2']:.4f}",
            'Accuracy': f"{metrics['R2']*100:.1f}%"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # R² Score comparison
        fig_r2 = px.bar(
            comparison_df, 
            x='Model', 
            y=[float(x) for x in comparison_df['R² Score']], 
            title="R² Score Comparison",
            color=[float(x) for x in comparison_df['R² Score']],
            color_continuous_scale="viridis"
        )
        fig_r2.update_layout(showlegend=False)
        st.plotly_chart(fig_r2, use_container_width=True)
    
    with col2:
        # MAE comparison
        mae_values = [float(x) for x in comparison_df['MAE']]
        fig_mae = px.bar(
            comparison_df, 
            x='Model', 
            y=mae_values, 
            title="Mean Absolute Error (Lower is Better)",
            color=mae_values,
            color_continuous_scale="viridis_r"
        )
        fig_mae.update_layout(showlegend=False)
        st.plotly_chart(fig_mae, use_container_width=True)
    
    # Feature importance
    st.subheader("🎯 Feature Importance (Random Forest)")
    
    feature_importance = predictor.get_feature_importance()
    if feature_importance is not None:
        fig_importance = px.bar(
            feature_importance, 
            x='importance', 
            y='feature', 
            orientation='h',
            title="Which factors affect traffic most?",
            color='importance',
            color_continuous_scale="plasma"
        )
        fig_importance.update_layout(height=400)
        st.plotly_chart(fig_importance, use_container_width=True)
        
        # Insights
        st.subheader("🔍 Key Insights")
        top_feature = feature_importance.iloc[0]
        st.write(f"• **{top_feature['feature']}** is the most important factor ({top_feature['importance']:.3f})")
        st.write(f"• Random Forest achieved **{results['Random Forest']['R2']*100:.1f}%** accuracy")
        st.write(f"• The model can predict traffic within ±{results['Random Forest']['MAE']:.0f} vehicles/hour")

def show_data_insights(df):
    st.header("📈 Traffic Data Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Traffic by hour
        hourly_traffic = df.groupby('hour')['traffic_flow'].mean().reset_index()
        fig_hourly = px.line(
            hourly_traffic, 
            x='hour', 
            y='traffic_flow',
            title="Average Traffic Flow by Hour",
            markers=True
        )
        fig_hourly.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig_hourly, use_container_width=True)
        
        # Weekend vs Weekday
        weekend_comparison = df.groupby('is_weekend')['traffic_flow'].mean().reset_index()
        weekend_comparison['day_type'] = weekend_comparison['is_weekend'].map({0: 'Weekday', 1: 'Weekend'})
        
        fig_weekend = px.bar(
            weekend_comparison, 
            x='day_type', 
            y='traffic_flow',
            title="Weekday vs Weekend Traffic",
            color='traffic_flow',
            color_continuous_scale="blues"
        )
        st.plotly_chart(fig_weekend, use_container_width=True)
    
    with col2:
        # Rain impact
        df['rain_category'] = pd.cut(df['rain_intensity'], 
                                   bins=[0, 0.1, 0.5, 1.0], 
                                   labels=['No Rain', 'Light Rain', 'Heavy Rain'])
        rain_impact = df.groupby('rain_category')['traffic_flow'].mean().reset_index()
        
        fig_rain = px.bar(
            rain_impact, 
            x='rain_category', 
            y='traffic_flow',
            title="Impact of Rain on Traffic",
            color='traffic_flow',
            color_continuous_scale="blues"
        )
        st.plotly_chart(fig_rain, use_container_width=True)
        
        # Speed vs Traffic correlation
        fig_scatter = px.scatter(
            df.sample(1000), 
            x='avg_speed', 
            y='traffic_flow',
            title="Speed vs Traffic Flow Correlation",
            opacity=0.6,
            color='rain_intensity',
            color_continuous_scale="viridis"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Summary statistics
    st.subheader("📊 Dataset Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Avg Traffic Flow", f"{df['traffic_flow'].mean():.0f}")
    with col3:
        st.metric("Peak Traffic", f"{df['traffic_flow'].max():.0f}")
    with col4:
        st.metric("Avg Speed", f"{df['avg_speed'].mean():.1f} km/h")

def show_route_comparison(predictor, weather_api):
    st.header("🗺️ Route Comparison & Optimization")
    
    st.subheader("🛣️ Compare Multiple Routes")
    
    # Get current conditions
    weather_data = weather_api.get_weather_data()
    now = datetime.now()
    
    # Route comparison
    routes = [
        {"name": "Route A (Main Road)", "base_speed": 45, "traffic_factor": 1.2},
        {"name": "Route B (Highway)", "base_speed": 60, "traffic_factor": 0.8},
        {"name": "Route C (Local Roads)", "base_speed": 30, "traffic_factor": 1.5}
    ]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ Scenario Settings")
        
        scenario_hour = st.slider("Time of Day", 0, 23, now.hour)
        scenario_day = st.selectbox("Day", 
                                  ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                                  index=now.weekday())
        scenario_rain = st.slider("Rain Intensity", 0.0, 1.0, weather_data['rain_intensity'], 0.1)
        scenario_event = st.checkbox("Special Event", False)
    
    with col2:
        st.subheader("📊 Route Analysis")
        
        route_results = []
        
        for route in routes:
            # Calculate conditions for this route
            day_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(scenario_day)
            is_weekend = 1 if day_of_week >= 5 else 0
            rush_hour = 1 if (7 <= scenario_hour <= 9) or (17 <= scenario_hour <= 19) else 0
            
            # Adjust speed based on route characteristics
            adjusted_speed = route["base_speed"] * (1 - scenario_rain * 0.3)
            
            # Predict traffic for this route
            predicted_traffic = predictor.predict_traffic(
                hour=scenario_hour,
                day_of_week=day_of_week,
                is_weekend=is_weekend,
                rain_intensity=scenario_rain,
                temperature=weather_data['temperature'],
                humidity=weather_data['humidity'],
                event_flag=1 if scenario_event else 0,
                rush_hour=rush_hour,
                avg_speed=adjusted_speed
            ) * route["traffic_factor"]
            
            # Calculate route score
            route_score = predictor.calculate_route_score(
                predicted_traffic=predicted_traffic,
                avg_speed=adjusted_speed,
                rain_intensity=scenario_rain,
                event_impact=0.3 if scenario_event else 0.0
            )
            
            route_results.append({
                'Route': route['name'],
                'Predicted Traffic': f"{predicted_traffic:.0f}",
                'Expected Speed': f"{adjusted_speed:.1f} km/h",
                'Route Score': f"{route_score:.1f}",
                'Recommendation': '🟢 Best' if route_score == max([r['Route Score'] for r in route_results] + [route_score]) else '🟡 OK' if route_score > 50 else '🔴 Avoid'
            })
        
        # Display results
        results_df = pd.DataFrame(route_results)
        st.dataframe(results_df, use_container_width=True)
        
        # Best route recommendation
        best_route = max(route_results, key=lambda x: float(x['Route Score']))
        st.success(f"🏆 **Recommended Route:** {best_route['Route']} (Score: {best_route['Route Score']}/100)")
    
    # Time-based analysis
    st.subheader("⏰ Traffic Prediction Throughout the Day")
    
    # Generate hourly predictions
    hourly_predictions = []
    for hour in range(24):
        day_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(scenario_day)
        is_weekend = 1 if day_of_week >= 5 else 0
        rush_hour = 1 if (7 <= hour <= 9) or (17 <= hour <= 19) else 0
        
        traffic_pred = predictor.predict_traffic(
            hour=hour,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            rain_intensity=scenario_rain,
            temperature=weather_data['temperature'],
            humidity=weather_data['humidity'],
            event_flag=1 if scenario_event else 0,
            rush_hour=rush_hour,
            avg_speed=35
        )
        
        hourly_predictions.append({
            'Hour': hour,
            'Traffic Flow': traffic_pred,
            'Period': 'Rush Hour' if rush_hour else 'Normal'
        })
    
    hourly_df = pd.DataFrame(hourly_predictions)
    
    fig_hourly = px.line(
        hourly_df, 
        x='Hour', 
        y='Traffic Flow',
        color='Period',
        title=f"24-Hour Traffic Prediction for {scenario_day}",
        markers=True
    )
    fig_hourly.add_vline(x=now.hour, line_dash="dash", line_color="red", 
                        annotation_text="Current Time")
    
    st.plotly_chart(fig_hourly, use_container_width=True)

if __name__ == "__main__":
    main()