import pandas as pd
import numpy as np

def calculate_market_microstructure(df: pd.DataFrame) -> dict:
    if df.empty: return {"pcr": 0, "max_pain": 0}
    
    # Put-Call Ratio
    total_pe_oi = df[df['option_type'] == 'PE']['open_interest'].sum()
    total_ce_oi = df[df['option_type'] == 'CE']['open_interest'].sum()
    pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0

    # Vectorized Max Pain calculation
    strikes = df['strike_price'].unique()
    
    ce_df = df[df['option_type'] == 'CE']
    pe_df = df[df['option_type'] == 'PE']
    
    ce_strikes = ce_df['strike_price'].values
    ce_oi = ce_df['open_interest'].values
    pe_strikes = pe_df['strike_price'].values
    pe_oi = pe_df['open_interest'].values
    
    pain_map = {}
    for strike in strikes:
        ce_loss = np.maximum(0, strike - ce_strikes) * ce_oi
        pe_loss = np.maximum(0, pe_strikes - strike) * pe_oi
        total_loss = np.sum(ce_loss) + np.sum(pe_loss)
        pain_map[strike] = total_loss
        
    max_pain = min(pain_map, key=pain_map.get) if pain_map else 0
    return {"pcr": round(float(pcr), 4), "max_pain": float(max_pain)}

def calculate_sector_rotations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    
    def compute_metrics(x):
        tmc = x['market_cap'].sum()
        wr = (x['pct_change'] * x['market_cap']).sum() / tmc if tmc > 0 else 0
        return pd.Series({
            'total_market_cap': tmc,
            'weighted_return': wr
        })
        
    sector_grouped = df.groupby('sector').apply(compute_metrics).reset_index()
    return sector_grouped
