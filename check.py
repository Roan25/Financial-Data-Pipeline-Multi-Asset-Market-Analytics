import sqlite3
conn = sqlite3.connect('data/market_analytics.db')
print("Analytics Meta:", conn.execute("SELECT * FROM raw_document_store WHERE collection_name='analytics_meta'").fetchall())
print("Pipeline Telemetry:", conn.execute("SELECT * FROM raw_document_store WHERE collection_name='pipeline_telemetry'").fetchall())
