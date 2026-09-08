# Multi-Asset Market Analytics Platform

## About the Project
This is an institutional-grade, end-to-end Financial Data ETL (Extract, Transform, Load) Pipeline and Interactive Dashboard. Built entirely in Python, it fetches live and historical market data (Equities, Options, and Macro Rates) and processes it into a localized SQLite and JSON Document hybrid database.

**Key Features:**
* **3D Volatility Surface:** Models Implied Volatility across varying Expiries and Strike Prices using Plotly 3D graphs.
* **Cross-Asset Correlation:** Computes and visualizes real-time correlation matrices between equity sectors and macro yield curves.
* **F&O Microstructure:** Maps Nifty 50 Open Interest (OI) build-up and unwinding phases to detect market sentiment.
* **Data Quality Gates:** Implements strict Pydantic V2 schema validations and automated circuit breakers to reject anomalous data spikes.
* **Technical Charting:** Interactive OHLCV Candlesticks overlaid with Moving Averages (SMA) and volume profiles.


## Initialization Steps
1. Create a python virtual environment and install packages:
   ```bash
   pip install -r requirements.txt
   python bootstrap.py
   python src/pipeline/orchestrator.py
   streamlit run src/dashboard/app.py
   
   pip install -r requirements.txt
   
   python bootstrap.py
   
   python -m src.pipeline.orchestrator
   
   streamlit run src/dashboard/app.py
   ```

## Project Structure
Here is a breakdown of where the files and folders are located in this repository:

* **`src/dashboard/app.py`**: The main Streamlit dashboard file. This is what runs the visual web interface.
* **`src/pipeline/orchestrator.py`**: The main data pipeline runner. It controls fetching, calculating, and saving the data.
* **`src/ingestion/`**: Contains the code that extracts data from Yahoo Finance and the NSE.
* **`src/transformation/`**: Contains the math engines for cross-asset correlation, max pain, and Excel exports.
* **`src/validation/`**: Contains the strict Pydantic rules and circuit breakers.
* **`src/database/`**: Contains the SQLite database connections.


Streamlit Community Cloud (Fastest)
Since Streamlit Cloud instances sleep after inactivity and wipe local files, your SQLite database and NoSQL documents will reset. The app will rely on the "Run Pipeline Now" button to fetch fresh data on demand.
1.Push to GitHub:Requires a public or private repository.Initialize git in your project root, commit all files, and push to a new GitHub repository. Ensure requirements.txt is in the root directory.
2.Connect to Streamlit Cloud:Log into [share.streamlit.io](https://share.streamlit.io/) using your GitHub account. Click New app.
3.Configure the Deployment:Set the correct file path.Repository: Select your newly created repo.
Branch: main (or your default branch).
Main file path: src/dashboard/app.py
