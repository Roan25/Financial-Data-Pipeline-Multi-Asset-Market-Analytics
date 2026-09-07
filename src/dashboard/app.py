import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.database.db_manager import DBManager
from src.pipeline.orchestrator import PipelineOrchestrator
import os

st.set_page_config(page_title="Multi-Asset Analytics", layout="wide")
db = DBManager("data/market_analytics.db")

def load_data():
    try:
        df_eq = db.query("SELECT * FROM equity_snapshot")
        df_fo = db.query("SELECT * FROM fo_contracts")
        meta = db.get_latest_document("analytics_meta") or {"pcr": 0, "max_pain": 0}
        macro = db.query("SELECT * FROM macro_rates")
        return df_eq, df_fo, meta, macro
    except Exception:
        # Fallback to empty dataframes if the orchestrator hasn't built the tables yet
        return pd.DataFrame(), pd.DataFrame(), {"pcr": 0, "max_pain": 0}, pd.DataFrame()

def run_dashboard():
    # Sidebar
    st.sidebar.title("System Controls")
    if st.sidebar.button("Run Pipeline Now"):
        with st.spinner("Running Orchestrator..."):
            telemetry = PipelineOrchestrator().run()
        st.sidebar.success(f"Success! Latency: {telemetry['latency_sec']}s")

    excel_path = "data/processed/Nifty_Executive_Report.xlsx"
    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            st.sidebar.download_button("📥 Download Executive Excel Report", f, file_name="Nifty_Executive_Report.xlsx")

    telemetry = db.get_latest_document("pipeline_telemetry")
    if telemetry:
        st.sidebar.markdown("### Telemetry")
        st.sidebar.json(telemetry)

    # Main Body
    df_eq, df_fo, meta, macro = load_data()

    if df_eq.empty or df_fo.empty:
        st.warning("Database empty. Please run the pipeline first.")
        return

    # Top Banner
    col1, col2, col3, col4 = st.columns(4)
    spot = df_fo['underlying_value'].iloc[0] if (not df_fo.empty and 'underlying_value' in df_fo.columns) else 0
    ind10 = macro[macro['instrument'] == 'India 10Y Yield']['yield_rate'].values
    ind10_val = ind10[0] if len(ind10) > 0 else 0
    
    col1.metric("Nifty Proxy Spot", f"{spot:,.0f}")
    col2.metric("Put-Call Ratio", meta.get('pcr', 0))
    col3.metric("Max Pain Strike", meta.get('max_pain', 0))
    col4.metric("India 10Y Yield", f"{ind10_val}%")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["The Weighted Sector Rotator", "F&O Open Interest Mapper", "3D Volatility Surface", "Cross-Asset Correlation", "Macro Yield Curve"])

    with tab1:
        st.subheader("Market Cap Weighted Sector Performance")
        if not df_eq.empty:
            colA, colB = st.columns([3, 1])
            with colA:
                fig = px.treemap(df_eq, path=[px.Constant("Nifty"), 'sector', 'symbol'], 
                                 values='market_cap', color='pct_change',
                                 color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
                fig.update_layout(margin=dict(t=20, l=10, r=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            with colB:
                st.markdown("### Sector Summary")
                sector_summary = df_eq.groupby('sector').agg(
                    Total_Market_Cap=('market_cap', 'sum'),
                    Avg_Return=('pct_change', 'mean')
                ).reset_index().sort_values('Total_Market_Cap', ascending=False)
                
                # Format for display
                sector_summary['Total_Market_Cap'] = sector_summary['Total_Market_Cap'].apply(lambda x: f"₹{x/1e7:,.2f}Cr")
                sector_summary['Avg_Return'] = sector_summary['Avg_Return'].apply(lambda x: f"{x:+.2f}%")
                st.dataframe(sector_summary, hide_index=True, use_container_width=True)

    with tab2:
        st.subheader("4-Phase F&O Microstructure Heatmap")
        if not df_fo.empty:
            color_map = {
                "Long Buildup": "green", "Short Buildup": "red",
                "Long Unwinding": "orange", "Short Covering": "cyan", "Neutral": "gray"
            }
            fig2 = px.scatter(df_fo, x='strike_price', y='option_type', size='traded_volume',
                              color='market_phase', color_discrete_map=color_map,
                              hover_data=['open_interest', 'change_in_oi'])
            st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Strike-level OI and Change in OI")
            # Filter close to spot for better visual
            lower_bound = spot * 0.95
            upper_bound = spot * 1.05
            df_filtered = df_fo[(df_fo['strike_price'] >= lower_bound) & (df_fo['strike_price'] <= upper_bound)]
            
            # Group by strike safely
            df_grouped = df_filtered.groupby(['strike_price', 'option_type'])[['open_interest', 'change_in_oi']].sum().reset_index()
            
            # Double Bar Visual
            fig3 = px.bar(df_grouped, x='strike_price', y=['open_interest', 'change_in_oi'],
                          barmode='group', facet_col='option_type',
                          labels={'value': 'Contracts', 'variable': 'Metric'},
                          color_discrete_sequence=['#1f77b4', '#ff7f0e'])
            fig3.update_layout(xaxis_title="Strike Price", xaxis=dict(type='category'))
            st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.subheader("3D Implied Volatility Surface")
        if not df_fo.empty:
            # We want to map Strike (X), Expiry (Y), and IV (Z)
            # Filter to Call Options for a clean surface
            df_surface = df_fo[df_fo['option_type'] == 'CE'].copy()
            
            # Create a pivot table: Index=Expiry, Columns=Strike, Values=IV
            df_surface['expiry_date_dt'] = pd.to_datetime(df_surface['expiry_date'])
            df_surface = df_surface.sort_values(['expiry_date_dt', 'strike_price'])
            
            # Pivot
            pivot = df_surface.pivot(index='expiry_date_dt', columns='strike_price', values='implied_volatility')
            
            x_data = pivot.columns.tolist()  # Strikes
            y_data = [d.strftime('%Y-%m-%d') for d in pivot.index]  # Expiries
            z_data = pivot.values  # IV matrix
            
            fig4 = go.Figure(data=[go.Surface(z=z_data, x=x_data, y=y_data, colorscale='Viridis')])
            fig4.update_layout(
                scene=dict(
                    xaxis_title='Strike Price',
                    yaxis_title='Expiry Date',
                    zaxis_title='Implied Volatility (%)',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                margin=dict(l=0, r=0, b=0, t=30),
                height=700
            )
            st.plotly_chart(fig4, use_container_width=True)

    with tab4:
        st.subheader("Cross-Asset Sector & Macro Correlation Matrix")
        corr_data = db.get_latest_document("correlation_matrix")
        if corr_data:
            df_corr = pd.DataFrame(corr_data)
            fig5 = px.imshow(df_corr, text_auto=".2f", aspect="auto",
                             color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            fig5.update_layout(height=600, margin=dict(l=0, r=0, b=0, t=30))
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.warning("Correlation data not available yet. Please run the pipeline.")

    with tab5:
        st.subheader("India Sovereign Yield Curve")
        if not macro.empty:
            # We assume the order is 1M, 3M, 6M, 1Y, 2Y, 5Y, 10Y, 30Y
            fig6 = px.line(macro, x='instrument', y='yield_rate', markers=True,
                           labels={'instrument': 'Tenor', 'yield_rate': 'Yield (%)'})
            fig6.update_traces(line=dict(color='red', width=3), marker=dict(size=10, color='blue'))
            fig6.update_layout(height=500, margin=dict(l=0, r=0, b=0, t=30), yaxis=dict(autorange=False, range=[6.0, 8.0]))
            st.plotly_chart(fig6, use_container_width=True)

if __name__ == "__main__":
    run_dashboard()
