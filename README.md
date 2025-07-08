# MoveGuiderAI 🏙️

**A comparative analytics dashboard for personal productivity and environmental metrics.**

MoveGuiderAI is an interactive web application built with Streamlit that helps users, particularly remote workers, compare two cities side-by-side. It fetches real-time environmental data and combines it with personalized user inputs to generate a suite of visualizations covering weather forecasts, daily routines, and personal wellness metrics like cognitive performance and hydration needs.

  <!-- You can replace this with your own screenshot -->

---

## ✨ Features

*   **Comparative Weather Analysis**: View 7-day hourly forecasts for Temperature, Humidity, and UV Index for two cities overlaid on a single, time-normalized chart.
*   **Dynamic Daylight Highlighting**: Automatically visualizes the daylight hours (sunrise to sunset) for the primary city, providing context for the environmental data.
*   **Personalized Energy Curve**: Models your unique cognitive performance throughout the day based on your sleep schedule (circadian rhythm).
*   **Comparative Hydration Timeline**: Calculates and visualizes your personalized hourly water intake needs for both cities, factoring in temperature, humidity, and your body weight.
*   **Polar Comfort Wheel**: A multi-metric radar chart that compares current environmental conditions in both cities against ideal comfort ranges for well-being.
*   **Robust & Resilient Data Pipeline**: Utilizes the reliable Nominatim API for geocoding and WeatherAPI.com for forecast data, ensuring high availability and uptime.

---

## 🛠️ Tech Stack & Architecture

MoveGuiderAI is built with a modular and scalable Python architecture designed for clarity and easy extension.

*   **Frontend**: [Streamlit](https://streamlit.io/) - For building the interactive web dashboard.
*   **Data Manipulation**: [Pandas](https://pandas.pydata.org/) - For all data transformation and time-series analysis.
*   **Data Visualization**: [Plotly](https://plotly.com/python/) - For creating rich, interactive, and publication-quality charts.
*   **External APIs**:
    *   [**WeatherAPI.com**](https://www.weatherapi.com/): Primary source for all weather, astronomical, and timezone data.
    *   [**Nominatim (OpenStreetMap)**](https://nominatim.org/): Used for robust and reliable geocoding (City Name → Lat/Lon).
*   **Core Libraries**:
    *   `requests`: For making HTTP requests to external APIs.
    *   `pytz`: For robust timezone calculations and conversions.
    *   `python-dotenv`: For securely managing environment variables and API keys.

### Architectural Overview

The project is structured with a clear separation of concerns, making it easy to maintain and debug:

* `app.py`: The main Streamlit application. It handles UI layout, state management (`st.session_state`), and orchestrates calls to the logic and plotting modules.
* `api_clients.py`: Contains all functions responsible for communicating with external APIs (Nominatim, WeatherAPI).
* `logic/`: A package containing all business logic, data processing, and modeling modules.
  * `weather_parser.py`: Parses raw API data into clean DataFrames.
  * `performance.py`: Models the user's energy curve.
  * `hydration.py`: Calculates personalized hydration needs.
  * `planner.py`: Handles daily routine logic, data unification, and recommendations.
  * `user_profiles.py`: Manages loading and saving of user profiles and routines.
  * `utils.py`: Contains common utility functions (e.g., timezone conversions).
* `plotting/`: A package containing all data visualization functions. Each module returns a Plotly Figure object.
* `data/`: Contains data files, such as the `user_profiles.json` for storing user settings.
* `config.py`: Loads and provides access to configuration and secret keys from the `.env` file.
* `.env`: A local, untracked file for storing secret API keys.

---

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### 1. Prerequisites

*   Python 3.9+
*   `uv` (or `pip` and `venv`) - `uv` is recommended for its speed. You can install it with `pip install uv`.

### 2. Clone the Repository

```bash
git clone https://github.com/himudigonda/MoveGuiderAI.git
cd MoveGuiderAI
```

### 3. Set Up the Environment

We recommend using `uv` to create and manage the virtual environment.

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 4. Install Dependencies

Install all required Python packages from the `requirements.txt` file.

```bash
uv pip install -r requirements.txt
```

### 5. Configure API Keys

The application requires an API key from WeatherAPI.com.

1.  **Sign Up**: Create a free account at [WeatherAPI.com](https://www.weatherapi.com/signup.aspx).
2.  **Get Key**: Copy your API key from the dashboard.
3.  **Create `.env` file**: In the root of the project, create a file named `.env`.
4.  **Add your key**: Add the following line to the `.env` file, replacing `YOUR_KEY_HERE` with the key you just copied.

    ```ini
    # .env
    WEATHERAPI_API_KEY="YOUR_KEY_HERE"
    OPENWEATHER_API_KEY="dummy_key" # This is no longer used but kept for legacy purposes
    ```

### 6. Run the Application

You are now ready to launch the Streamlit dashboard!

```bash
uv run streamlit run app.py
```

Your web browser should automatically open to `http://localhost:8501`, where you can see the running application.

---

## 💡 Future Enhancements & Roadmap

This project has a solid foundation for many exciting future features:

*   **Code Quality**:
    *   Implement a full test suite using `pytest` for logic and plotting functions.
    *   Set up a CI/CD pipeline with GitHub Actions to automate testing.
    *   Integrate static analysis with `mypy` for improved type safety.
*   **Core Features**:
    *   **Time-Zone Toggle**: Add a global toggle to view all charts in either "Home Time (AZ)" or the selected city's local time.
    *   **Apple Health Integration**: Add a file uploader to ingest Apple Health `export.xml` data (RHR, HRV, Sleep Stages) to create a more accurate and personalized energy curve model.
*   **UX & Interactivity**:
    *   **Export Buttons**: Add buttons to download charts as PNG images.
    *   **Dark Mode**: Implement a theme toggle for user comfort.
    *   **Advanced Tooltips**: Enhance chart tooltips to show more data or actionable advice.
*   **Data Extensibility**:
    *   **AQI & Pollen**: Integrate an Air Quality API to add another layer to the comfort wheel.
    *   **Cost of Living**: Connect to an API like Numbeo to add a financial comparison component.

Contributions are welcome! Please feel free to fork the repository, make changes, and open a pull request.
