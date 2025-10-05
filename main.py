import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import date, timedelta
import requests # You will use this library for real API calls

# --- Configuration for Streamlit App ---
st.set_page_config(
    page_title="Will It Rain On My Parade? | NASA Space Apps",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Utility Functions ---

def geocode_location(location_name):
    """
    STEP 1: Geocoding the user's location input into Lat/Lon coordinates.
    
    ACTION: Replace this with a fast geocoding service (e.g., GeoPy, or an 
    open-source geocoding API) to get precise coordinates from the city name.
    """
    # Placeholder: Maps "San Francisco" to a fixed Lat/Lon
    if "san francisco" in location_name.lower():
        return 37.7749, -122.4194, "San Francisco, CA"
    elif "tokyo" in location_name.lower():
        return 35.6895, 139.6917, "Tokyo, Japan"
    else:
        # Default fallback for simulation
        return 34.0522, -118.2437, location_name # Default to Los Angeles, CA

def fetch_historical_climate_data_api(lat, lon, month, day):
    """
    HACKATHON STEP 1 BLUEPRINT: FAST DATA FETCH
    
    ACTION: Replace the simulation below with your actual API integration.
    You will need to use 'requests.get(nasa_api_url)' here.
    
    The goal is to get 30 yearly data points for the specific day of the year (month/day).
    """
    
    # -------------------------------------------------------------------------
    # !!! START OF REAL API INTEGRATION ZONE !!!
    # -------------------------------------------------------------------------
    
    # Example API endpoint structure (NOT REAL, just for illustration):
    # nasa_api_url = f"https://api.nasa.gov/earthdata/merra2?lat={lat}&lon={lon}&month={month}&day={day}&start_year=1995"
    
    # try:
    #     response = requests.get(nasa_api_url, timeout=10)
    #     data = response.json()
    #     # Parse the 'data' structure into a list of dictionaries, one for each year
    #     # Example: [{"year": 1995, "max_temp": 25.5, "rain": 1.2, ...}, ...]
    # except Exception as e:
    #     st.error(f"Error fetching NASA data: {e}")
    #     # Fallback or error handling
    #     return None

    # -------------------------------------------------------------------------
    # !!! END OF REAL API INTEGRATION ZONE (REPLACING WITH SIMULATION) !!!
    # -------------------------------------------------------------------------
    
    np.random.seed(int(abs(hash(str(lat) + str(lon) + str(month) + str(day)))) % (2**32 - 1))
    
    num_years = 30
    
    # Use random parameters based on the location/date hash for a stable simulation
    base_temp = 20 + lat * 0.5 - 30 * np.random.rand()
    
    # Simulated Historical Data (30 years of observation for the specific day-of-year)
    simulated_data = []
    for year in range(date.today().year - num_years, date.today().year):
        max_temp = np.random.uniform(base_temp - 5, base_temp + 15)
        
        # Add a slight increasing trend for Max_Temp to demonstrate climate change detection
        max_temp += (year - (date.today().year - num_years) ) * 0.05
        
        simulated_data.append({
            'Year': year,
            'Max_Temp_C': max_temp,
            'Min_Temp_C': np.random.uniform(base_temp - 15, base_temp + 5),
            'Rain_mm': np.random.lognormal(mean=np.log(1.5), sigma=1.0),
            'Wind_m_s': np.random.uniform(5, 15),
            'Humidex': np.random.uniform(20, 45)
        })
        
    return simulated_data


def analyze_historical_data(lat, lon, target_date, hot_thresh, cold_thresh, rain_thresh):
    """
    CORE DATA PROCESSING: Calls the fetch function and implements Steps 2 & 3.
    """
    
    st.info(f"🚀 Analyzing decades of NASA EO data for Lat: {lat:.2f}, Lon: {lon:.2f} on {target_date.strftime('%B %d')}...")
    
    # 1. FETCH DATA
    data_list = fetch_historical_climate_data_api(
        lat, lon, 
        target_date.month, 
        target_date.day
    )
    
    if not data_list:
        return None
        
    simulated_history = pd.DataFrame(data_list)
    num_years = len(simulated_history)

    # 2. DEFINING EXTREME EVENTS (Implemented using user thresholds)
    # -------------------------------------------------------------------------

    # A. Very Hot: Max Temp exceeds user's Max Comfort
    extreme_hot_count = (simulated_history['Max_Temp_C'] > hot_thresh).sum()
    
    # B. Very Cold: Min Temp falls below user's Min Comfort
    extreme_cold_count = (simulated_history['Min_Temp_C'] < cold_thresh).sum()
    
    # C. Very Wet: Rain exceeds user's Max Acceptable Rain
    extreme_wet_count = (simulated_history['Rain_mm'] > rain_thresh).sum()
    
    # D. Very Windy: Wind Speed exceeds a standard high wind threshold (e.g., 12 m/s)
    extreme_wind_count = (simulated_history['Wind_m_s'] > 12).sum() 
    
    # E. Very Uncomfortable: Humidex exceeds a common discomfort index (e.g., 35)
    extreme_uncomfortable_count = (simulated_history['Humidex'] > 35).sum() 

    # 3. PROBABILITY CALCULATION (Implemented) & TREND ANALYSIS
    # -------------------------------------------------------------------------
    
    total_observations = num_years
    
    # Calculate the linear trend for Max Temperature (C/decade)
    x = simulated_history['Year']
    y = simulated_history['Max_Temp_C']
    slope, intercept = np.polyfit(x, y, 1)
    
    # Convert slope (C/year) to C/decade
    temp_trend_c_per_decade = slope * 10
    
    results = {
        "historical_period_years": num_years,
        "avg_daily_high_c": round(simulated_history['Max_Temp_C'].mean(), 1),
        "avg_rainfall_mm": round(simulated_history['Rain_mm'].mean(), 1),
        "temp_trend_c_per_decade": round(temp_trend_c_per_decade, 2),
        
        "extreme_probabilities": {
            "very_hot": extreme_hot_count / total_observations,
            "very_cold": extreme_cold_count / total_observations,
            "very_wet": extreme_wet_count / total_observations,
            "very_windy": extreme_wind_count / total_observations,
            "very_uncomfortable_humidex": extreme_uncomfortable_count / total_observations
        }
    }
    
    return results

def format_probability(prob):
    """Formats a float probability (0.0 to 1.0) into a clean percentage string."""
    return f"{int(round(prob * 100))}%"

def get_risk_level(prob):
    """Determines a risk level and associated color for display."""
    if prob >= 0.35:
        return "High Risk 🔴"
    elif prob >= 0.15:
        return "Moderate Risk 🟠"
    else:
        return "Low Risk 🟢"
        
def format_trend(trend_value):
    """Formats the temperature trend with a delta and color."""
    if trend_value > 0.05:
        return f"+{trend_value}°C", "inverse"
    elif trend_value < -0.05:
        return f"{trend_value}°C", "off"
    else:
        return "Stable", "off"

# --- Main Streamlit Application ---

st.title("🌧️ Will It Rain On My Parade? | Event Planner Assistant")
st.markdown(
    """
    **Leveraging Decades of NASA Earth Observation Data for Long-Term Event Planning.**
    This tool uses historical data to calculate the probability of adverse weather conditions
    for your chosen date and location, helping you plan months in advance.
    """
)
st.divider()

# --- 1. Sidebar for Inputs and Personalization (CRITICAL FOR THE CHALLENGE) ---
with st.sidebar:
    st.header("Plan Your Event")
    
    # Input 1: Location
    location_input = st.text_input(
        "Location (City, or Lat/Lon)",
        value="San Francisco, CA",
        key="location_input"
    )

    # Input 2: Date
    # Force the date to be in the future (long-term planning)
    min_date = date.today() + timedelta(days=30)
    target_date_input = st.date_input(
        "Target Event Date (Min. 30 Days Out)",
        value=min_date,
        min_value=min_date,
        key="date_input"
    )

    st.header("Personalized Thresholds")
    st.markdown("Define what 'Very' means to you for better personalization.")
    
    # Input 3: User-defined thresholds
    col_temp1, col_temp2 = st.columns(2)
    with col_temp1:
        hot_threshold = st.number_input(
            "Max Comfort Temp (°C)",
            value=30,
            min_value=15,
            max_value=50,
            step=1,
            key="hot_threshold"
        )
    with col_temp2:
        cold_threshold = st.number_input(
            "Min Comfort Temp (°C)",
            value=10,
            min_value=-20,
            max_value=25,
            step=1,
            key="cold_threshold"
        )

    rain_threshold = st.slider(
        "Max Acceptable Daily Rain (mm)",
        min_value=0,
        max_value=20,
        value=5,
        step=1,
        key="rain_threshold"
    )
    
    if st.button("Analyze Parade Odds", type="primary"):
        st.session_state['analyze_clicked'] = True
    
# Initialize state if not present
if 'analyze_clicked' not in st.session_state:
    st.session_state['analyze_clicked'] = False

# --- 2. Main Display Area ---

if st.session_state['analyze_clicked']:
    
    # Geocode the location first
    lat, lon, resolved_location = geocode_location(location_input)
    
    # Fetch data (or run the simulation)
    with st.spinner("Crunching decades of climate data..."):
        analysis_data = analyze_historical_data(
            lat, lon, 
            target_date_input, 
            hot_threshold, 
            cold_threshold, 
            rain_threshold
        )
        
    if analysis_data is None:
        st.error("Could not complete analysis. Check data fetching steps.")
    else:
        st.success(f"Analysis complete for {target_date_input.strftime('%A, %B %d')} in {resolved_location}.")
        
        # Extract data for visualization
        probs = analysis_data['extreme_probabilities']
        avg_temp = analysis_data['avg_daily_high_c']
        avg_rain = analysis_data['avg_rainfall_mm']
        temp_trend = analysis_data['temp_trend_c_per_decade']
        
        trend_display, trend_color = format_trend(temp_trend)
    
        st.header("Calculated Adverse Weather Probabilities")
        st.markdown(
            f"""
            These probabilities represent the historical likelihood of the day falling into a
            **user-defined extreme** for that specific date and location over the last **{analysis_data['historical_period_years']} years**.
            """
        )
    
        # --- Metrics Dashboard ---
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # 1. Very Hot
        with col1:
            st.metric(
                label=f"Very Hot (>{hot_threshold}°C)",
                value=format_probability(probs['very_hot']),
                delta=get_risk_level(probs['very_hot']),
                delta_color="off" 
            )
    
        # 2. Very Cold
        with col2:
            st.metric(
                label=f"Very Cold (<{cold_threshold}°C)",
                value=format_probability(probs['very_cold']),
                delta=get_risk_level(probs['very_cold']),
                delta_color="off"
            )
    
        # 3. Very Wet
        with col3:
            st.metric(
                label=f"Very Wet (>{rain_threshold}mm Rain)",
                value=format_probability(probs['very_wet']),
                delta=get_risk_level(probs['very_wet']),
                delta_color="off"
            )
    
        # 4. Very Windy
        with col4:
            st.metric(
                label="Very Windy (High Wind Speed)",
                value=format_probability(probs['very_windy']),
                delta=get_risk_level(probs['very_windy']),
                delta_color="off"
            )
    
        # 5. Very Uncomfortable
        with col5:
            st.metric(
                label="Very Uncomfortable (High Humidex)",
                value=format_probability(probs['very_uncomfortable_humidex']),
                delta=get_risk_level(probs['very_uncomfortable_humidex']),
                delta_color="off"
            )
    
        st.divider()
    
        # --- Visualization and Insights ---
        
        st.header("Long-Term Climate Insights")
    
        col_chart, col_data = st.columns([3, 2])
        
        # Bar Chart of Probabilities
        with col_chart:
            # Create a DataFrame for the bar chart
            chart_data = pd.DataFrame(
                {
                    'Condition': ['Hot', 'Cold', 'Wet', 'Windy', 'Uncomfortable'],
                    'Probability (%)': [int(p * 100) for p in probs.values()]
                }
            ).set_index('Condition')
    
            st.bar_chart(chart_data, height=350, color="#1f77b4") # NASA blue-ish
    
        # Average Historical Data
        with col_data:
            st.subheader("Historical Averages for this Day")
            st.markdown(f"Based on **{analysis_data['historical_period_years']} years** of NASA Earth Data")
            
            st.metric(
                label="Average Daily High Temperature",
                value=f"{avg_temp}°C",
                delta="Use this baseline to adjust your expectations."
            )
    
            st.metric(
                label="Average Daily Rainfall",
                value=f"{avg_rain} mm",
                delta="This is the expected long-term average."
            )
            
            st.metric(
                label="Max Temp Trend (C/Decade)",
                value=trend_display,
                delta="Likelihood of heat increasing over time.",
                delta_color=trend_color
            )
    
    
        st.subheader("Actionable Recommendation")
        
        # Provide a simple, actionable recommendation based on the highest risk
        max_prob = max(probs.values())
        max_condition = [k for k, v in probs.items() if v == max_prob][0].replace('_', ' ').title()
        
        if max_prob >= 0.35:
            st.error(f"🚨 High-Risk Alert: The highest risk is **{max_condition}** ({format_probability(max_prob)}). You should strongly consider an alternative date or location, or prepare comprehensive contingency plans (e.g., cooling stations, indoor venues).")
        elif max_prob >= 0.15:
            st.warning(f"⚠️ Moderate Risk: The highest risk is **{max_condition}** ({format_probability(max_prob)}). Proceed with caution and have backup plans for that specific condition (e.g., heavy coats, wind barriers).")
        else:
            st.success("✅ All conditions show Low Risk. Based on historical data, your date and location look promising! Always check the short-term forecast closer to the date.")
            
else:
    # Initial landing message
    st.info("👈 Use the sidebar to input your desired event location and date, define your personal comfort thresholds, and click 'Analyze Parade Odds' to begin the long-term historical analysis!")
