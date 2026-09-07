import os
import openpyxl
from openpyxl.styles import Font

def setup_environment():
    # 1. Create directory structure
    directories = [
        "data/raw_documents",
        "data/processed",
        "src/database",
        "src/validation",
        "src/ingestion",
        "src/transformation",
        "src/pipeline",
        "src/dashboard"
    ]
    for d in directories:
        os.makedirs(d, exist_ok=True)
        if d.startswith("src/"):
            open(os.path.join(d, "__init__.py"), 'a').close()
    open("src/__init__.py", 'a').close()

    # 2. Create Master Reference Excel
    excel_path = "data/nifty_master_reference.xlsx"
    if not os.path.exists(excel_path):
        wb = openpyxl.Workbook()
        
        # Sheet 1: Constituents Master
        ws1 = wb.active
        ws1.title = "Constituents_Master"
        headers1 = ["Symbol", "Yahoo_Ticker", "Sector", "Benchmark_Weight", "Lot_Size"]
        ws1.append(headers1)
        for cell in ws1[1]:
            cell.font = Font(bold=True)
            
        constituents = [
            ("RELIANCE", "RELIANCE.NS", "Energy", 10.5, 250),
            ("HDFCBANK", "HDFCBANK.NS", "Financial Services", 13.5, 550),
            ("ICICIBANK", "ICICIBANK.NS", "Financial Services", 7.5, 700),
            ("INFY", "INFY.NS", "IT", 6.0, 400),
            ("ITC", "ITC.NS", "FMCG", 4.5, 1600),
            ("TCS", "TCS.NS", "IT", 4.0, 175),
            ("LT", "LT.NS", "Construction", 3.0, 300),
            ("KOTAKBANK", "KOTAKBANK.NS", "Financial Services", 2.8, 400),
            ("AXISBANK", "AXISBANK.NS", "Financial Services", 3.0, 625),
            ("SBIN", "SBIN.NS", "Financial Services", 2.8, 1500),
            ("BHARTIARTL", "BHARTIARTL.NS", "Telecom", 2.5, 950),
            ("BAJFINANCE", "BAJFINANCE.NS", "Financial Services", 2.1, 125),
            ("ASIANPAINT", "ASIANPAINT.NS", "Consumer Goods", 1.8, 200),
            ("MARUTI", "MARUTI.NS", "Automobile", 1.7, 50),
            ("HINDUNILVR", "HINDUNILVR.NS", "FMCG", 2.5, 300)
        ]
        for row in constituents:
            ws1.append(row)

        # Sheet 2: Macro Benchmarks
        ws2 = wb.create_sheet(title="Macro_Benchmarks")
        headers2 = ["Instrument", "Baseline_Target_Yield"]
        ws2.append(headers2)
        for cell in ws2[1]:
            cell.font = Font(bold=True)
        ws2.append(["India 10Y Benchmark", 7.05])
        ws2.append(["US 10Y Yield", 4.25])
        ws2.append(["RBI Policy Repo Rate", 6.50])

        wb.save(excel_path)
        print(f"Created: {excel_path}")
    print("Bootstrap complete. Directory tree and seed files are ready.")

if __name__ == "__main__":
    setup_environment()
