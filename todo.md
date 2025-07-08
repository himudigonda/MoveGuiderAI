# MoveGuiderAI - Project TODO List

This document tracks the remaining features and enhancements for the MoveGuiderAI project.

---

## Phase 3: Advanced Personalization & Logistics Intelligence (In Progress)

This phase focuses on adding deeper layers of personalization and integrating crucial logistical data beyond just weather and routines.

-   [x] **Chronotype-selectable Energy Curve** - *Implemented.*
-   [ ] **Weather-based Sleep Predictor**
    -   **Goal:** Provide a simple daily forecast for sleep quality.
    -   **Logic:** Create a heuristic model in `logic/performance.py`.
        -   Input: Overnight (e.g., 10 PM - 6 AM) weather data for a city.
        -   Logic: Score sleep quality based on temperature and humidity. (e.g., ideal overnight temp: 18-20°C; ideal humidity: 40-60%).
        -   Output: A simple rating like "Optimal Sleep Conditions," "Slightly Warm," or "Potentially Restless Night (High Heat/Humidity)."
    -   **UI:** Display the rating as a small metric or `st.info` box for each city.

-   [ ] **Time Zone Pain Map**
    -   **Goal:** Visually highlight the "pain points" of collaborating across time zones.
    -   **Logic:** Create a function in `logic/planner.py`.
        -   Input: User's routine (specifically tasks marked with `type: 'meetings'`) and the two city timezones.
        -   Logic: Assume a standard 9-5 working day for the "home" timezone (AZ time). Generate a heatmap or table showing which of the user's meetings fall outside these core hours for the home team.
    -   **UI:** Display a simple heatmap or color-coded table showing the overlapping work hours and highlighting "unsociable" hours in red.

-   [ ] **Initial Logistics API Integration (Stubbed)**
    -   **Goal:** Begin integrating real-world logistics data. We will start by adding the API calls and parsers, with the UI integration to follow.
    -   **Tasks:**
        1.  **Internet Quality (`api_clients.py`):**
            -   Research and select an API (e.g., Ookla Speedtest API - may require application; or scrape data from public sources if an open API is unavailable).
            -   Write a function `get_internet_speed(city_name)` to return average download/upload speeds.
        2.  **Delivery Density (`api_clients.py`):**
            -   Research and select an API (e.g., Yelp Fusion API, which has a business search endpoint).
            -   Write a function `get_delivery_density(lat, lon)` that searches for a radius around the city center for categories like "fooddelivery" or "grocery" and returns the total count.
        3.  **Electricity Cost (`api_clients.py`):**
            -   This is often the hardest to get via API. The plan is to research state/utility-level public data (e.g., from the U.S. Energy Information Administration - EIA).
            -   Write a function `get_avg_electricity_cost(state_abbr)` that returns the average cost per kWh from a pre-compiled data source.

---

## Future Enhancements & System Improvements (Post-Phase 3)

These are features from the original high-level plan that will complete the vision of the project.

-   [ ] **Smart Data Caching & Trend Analysis**
    -   **Goal:** Show trends over time.
    -   **Logic:** Modify the caching mechanism to store data with timestamps. When a user queries a city they've searched before, fetch both the new data and the old cached data.
    -   **UI:** Add small `st.metric` indicators showing trends, e.g., "Temperature: 25°C (↑ 2°C vs last week)".

-   [ ] **Markdown/Email Export**
    -   **Goal:** Allow users to share their full comparison dashboard.
    -   **Logic:** Create a new function in `logic/generator.py` that compiles a summary of all charts and data into a single, comprehensive Markdown string.
    -   **UI:** Add an "Export Full Report" button that downloads the `.md` file.

-   [ ] **Voice/CLI Interaction Layer**
    -   **Goal:** Allow for quick, programmatic queries.
    -   **Logic:** Create a separate `cli.py` script that uses a library like `argparse` or `typer`.
    -   **Functionality:** Enable running commands like `python cli.py compare "Tempe, AZ" "Dallas, TX" --save-charts`. The script would perform the API calls and save the plot objects directly to image files.

-   [ ] **Code Quality & Testing**
    -   **Goal:** Ensure long-term stability and maintainability.
    -   **Tasks:**
        -   Write unit tests using `pytest` for all functions in the `logic/` directory.
        -   Write basic integration tests to ensure the `app.py` UI components render without crashing.
        -   Set up a simple CI/CD pipeline using GitHub Actions to automatically run tests on every push.

---
