# Multi-Asset Market Analytics Platform

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
