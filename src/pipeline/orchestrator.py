import time
import os
from src.database.db_manager import DBManager
from src.ingestion.extractors import NSEOptionChainExtractor, EquityPriceExtractor, MacroRatesExtractor
from src.validation.schemas import DataQualityGate
from src.transformation.analytics import calculate_market_microstructure, calculate_sector_rotations
from src.transformation.excel_exporter import ExcelReportGenerator
import pandas as pd
import logging

# Basic structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PipelineOrchestrator:
    def __init__(self):
        self.db = DBManager()
        
    def run(self):
        start_time = time.time()
        logging.info("Starting Data Pipeline...")

        # Ensure processed directory exists on Streamlit Cloud
        import os
        os.makedirs("data/processed", exist_ok=True)

        # 1. Extraction Phase
        nse = NSEOptionChainExtractor().fetch()
        eq, hist_data = EquityPriceExtractor().fetch()
        macro = MacroRatesExtractor().fetch()
        
        # Use nanosecond precision to absolutely prevent Primary Key collisions
        self.db.save_document("nse_options", f"doc_{time.time_ns()}", nse)
        self.db.save_document("equity_yfinance", f"doc_{time.time_ns()}", {"data": eq})
        
        # Calculate Cross-Asset Correlation & Save OHLCV
        if not hist_data.empty:
            hist_data.to_parquet("data/processed/historical_ohlcv.parquet")
            
            import numpy as np
            # Map tickers to sectors using eq list
            close_data = hist_data['Close'] if 'Close' in hist_data else hist_data
            ticker_to_sector = {r['symbol'] + ".NS": r['sector'] for r in eq}
            sector_data = pd.DataFrame()
            for sector in set(ticker_to_sector.values()):
                sector_tickers = [t for t, s in ticker_to_sector.items() if s == sector and t in close_data.columns]
                if sector_tickers:
                    normalized = close_data[sector_tickers] / close_data[sector_tickers].iloc[0] * 100
                    sector_data[sector] = normalized.mean(axis=1)
            # Add Mock India 10Y Macro Yield
            np.random.seed(42)
            sector_data['India 10Y Yield'] = 7.10 + np.cumsum(np.random.normal(0, 0.05, len(sector_data)))
            corr_matrix = sector_data.corr().to_dict()
            self.db.save_document("correlation_matrix", "latest", corr_matrix)

        # Process Option Chain records for validation
        options_raw = []
        if 'records' in nse and 'data' in nse['records']:
            for item in nse['records']['data']:
                strike = item.get('strikePrice')
                exp = item.get('expiryDate')
                for opt_type in ['CE', 'PE']:
                    if opt_type in item:
                        d = item[opt_type]
                        options_raw.append({
                            "strike_price": strike, "option_type": opt_type, "expiry_date": exp,
                            "underlying_value": d.get('underlyingValue', 0), "ltp": d.get('lastPrice', 0),
                            "price_change": d.get('change', 0), "open_interest": d.get('openInterest', 0),
                            "change_in_oi": d.get('changeinOpenInterest', 0),
                            "traded_volume": d.get('totalTradedVolume', 0), "implied_volatility": d.get('impliedVolatility', 0)
                        })

        # 3. Validate
        df_eq, rejected_eq = DataQualityGate.validate_equity_batch(eq)
        df_opt, rejected_opt = DataQualityGate.validate_option_chain_batch(options_raw)
        rejected_all = rejected_eq + rejected_opt

        # 4. Write to SQL
        self.db.upsert_dataframe("equity_snapshot", df_eq, "replace")
        self.db.upsert_dataframe("fo_contracts", df_opt, "replace")
        self.db.upsert_dataframe("macro_rates", pd.DataFrame(macro), "replace")

        # Multi-format Output (Parquet & CSV)
        os.makedirs("data/processed", exist_ok=True)
        if not df_eq.empty:
            df_eq.to_parquet("data/processed/equity_snapshot.parquet", engine="fastparquet")
            df_eq.to_csv("data/processed/equity_snapshot.csv", index=False)
        if not df_opt.empty:
            df_opt.to_parquet("data/processed/fo_contracts.parquet", engine="fastparquet")
            df_opt.to_csv("data/processed/fo_contracts.csv", index=False)

        # 5. Compute Models
        metrics = calculate_market_microstructure(df_opt)
        self.db.save_document("analytics_meta", "latest", metrics)

        # 6. Generate Excel Report
        ExcelReportGenerator(self.db).generate(rejected_all)

        latency = time.time() - start_time
        telemetry = {
            "status": "SUCCESS", "latency_sec": round(latency, 2),
            "rows_equity": len(df_eq), "rows_options": len(df_opt),
            "bad_records": len(rejected_all), "pcr": metrics.get("pcr"),
            "max_pain": metrics.get("max_pain")
        }
        
        self.db.save_document("pipeline_telemetry", "latest", telemetry)
        logging.info(f"Pipeline Completed: {telemetry}")

        # Actual Webhook Alerting
        if len(rejected_all) > 0:
            try:
                import requests
                webhook_url = "https://httpbin.org/post" # Safe mock endpoint
                payload = {
                    "alert": "Pydantic Validation Failure",
                    "failed_records_count": len(rejected_all),
                    "pipeline_run_time": start_time
                }
                resp = requests.post(webhook_url, json=payload, timeout=5)
                logging.warning(f"WEBHOOK ALERT: {len(rejected_all)} records failed validation! Dispatched to {webhook_url} (Status: {resp.status_code})")
            except Exception as e:
                logging.error(f"Failed to fire webhook: {str(e)}")
            
        return telemetry

if __name__ == "__main__":
    PipelineOrchestrator().run()
