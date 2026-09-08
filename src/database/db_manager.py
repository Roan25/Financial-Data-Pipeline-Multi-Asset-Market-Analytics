import sqlite3
import json
import pandas as pd
from datetime import datetime

class DBManager:
    def __init__(self, db_path="data/market_analytics.db"):
        self.db_path = db_path
        import os
        # Ensure directory exists on ephemeral Streamlit Cloud instances
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS raw_document_store 
                         (doc_id TEXT, collection_name TEXT, payload JSON, ingested_at TIMESTAMP,
                          PRIMARY KEY (collection_name, doc_id))''')
            c.execute('''CREATE TABLE IF NOT EXISTS equity_snapshot 
                         (symbol TEXT PRIMARY KEY, sector TEXT, market_cap REAL, current_price REAL, 
                          pct_change REAL, volume INTEGER, updated_at TIMESTAMP)''')
            c.execute('''CREATE TABLE IF NOT EXISTS fo_contracts 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, strike_price REAL, option_type TEXT, 
                          ltp REAL, price_change REAL, open_interest INTEGER, change_in_oi INTEGER, 
                          traded_volume INTEGER, market_phase TEXT, expiry_date TEXT, implied_volatility REAL, underlying_value REAL, updated_at TIMESTAMP)''')
            c.execute('''CREATE TABLE IF NOT EXISTS macro_rates 
                         (instrument TEXT PRIMARY KEY, yield_rate REAL, daily_bps_change REAL, as_of_date TEXT)''')
            conn.commit()

    def save_document(self, collection: str, doc_id: str, payload: dict):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO raw_document_store (doc_id, collection_name, payload, ingested_at) 
                         VALUES (?, ?, ?, ?)''', (doc_id, collection, json.dumps(payload), datetime.utcnow()))
            conn.commit()

    def get_latest_document(self, collection: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''SELECT payload FROM raw_document_store WHERE collection_name = ? 
                         ORDER BY ingested_at DESC LIMIT 1''', (collection,))
            row = c.fetchone()
            return json.loads(row[0]) if row else None

    def upsert_dataframe(self, table_name: str, df: pd.DataFrame, if_exists='append'):
        if df.empty: return
        df['updated_at'] = datetime.utcnow()
        with sqlite3.connect(self.db_path) as conn:
            if if_exists == 'replace':
                # Safely delete rows without dropping the schema
                conn.execute(f"DELETE FROM {table_name}")
                # Reset auto-increment counter to prevent ID leaks
                try:
                    conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                except sqlite3.OperationalError:
                    pass
                if_exists = 'append'
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)

    def query(self, sql: str) -> pd.DataFrame:
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql(sql, conn)
