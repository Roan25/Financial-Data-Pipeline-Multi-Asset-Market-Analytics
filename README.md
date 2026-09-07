# Multi-Asset Market Analytics Platform

## Initialization Steps

1. **Create and activate a python virtual environment, then install packages:**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   # On Unix or MacOS:
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

2. **Initialize data directories and generate seed files:**
   ```bash
   python bootstrap.py
   ```

3. **Run the pipeline:**
   ```bash
   python -m src.pipeline.orchestrator
   ```

4. **Run the Streamlit dashboard:**
   ```bash
   streamlit run src/dashboard/app.py
   ```

## Deployment

### Streamlit Community Cloud (Fastest)

Since Streamlit Cloud instances sleep after inactivity and wipe local files, your SQLite database and NoSQL documents will reset. The app will rely on the "Run Pipeline Now" button to fetch fresh data on demand.

1. **Push to GitHub**:
   Requires a public or private repository. Initialize git in your project root, commit all files, and push to a new GitHub repository. Ensure `requirements.txt` is in the root directory.

2. **Connect to Streamlit Cloud**:
   Log into [share.streamlit.io](https://share.streamlit.io/) using your GitHub account. Click **New app**.

3. **Configure the Deployment**:
   Set the correct file path.
   - **Repository**: Select your newly created repo.
   - **Branch**: `main` (or your default branch).
   - **Main file path**: `src/dashboard/app.py`
