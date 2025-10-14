# dashboard_app.py 

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import textwrap
from typing import Optional
from io import BytesIO
import gdown


# Page Configuration & Theme

st.set_page_config(page_title="Brazilian E-commerce Dashboard", layout="wide", page_icon="🛒")

st.markdown("""
<style>
.stApp { background-color: #0b0c10; color: #e6eef6; }
.kpi { background: rgba(255,255,255,0.02); padding: 10px; border-radius: 8px; text-align:center;}
.kpi-label { color: #9aaab5; font-size:12px; }
.kpi-value { font-size:20px; font-weight:700; }
.sidebar .stSelectbox, .sidebar .stButton { color: #e6eef6; }
</style>
""", unsafe_allow_html=True)

PRIMARY = "#4f46e5"
BAR_COLOR = PRIMARY
PIE_PALETTE = px.colors.qualitative.Dark24
DATA_DIR = Path(".")


# Helper Functions

ef read_csv_if_exists(fn: str) -> Optional[pd.DataFrame]:
    p = DATA_DIR / fn
    if not p.exists():
        return None
    return pd.read_csv(p, low_memory=False)

def pick_col(df: pd.DataFrame, candidates: list) -> Optional[str]:
    if df is None: return None
    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand is None: continue
        if cand.lower() in lower:
            return lower[cand.lower()]
    for cand in candidates:
        if cand is None: continue
        for c in cols:
            if cand.lower() in c.lower():
                return c
    return None

def fmt_k(n):
    try:
        n = float(n)
    except Exception:
        return "N/A"
    if n != n:
        return "N/A"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,.0f}"

def set_transparent(fig):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

# -----------------------
# Load all datasets
# -----------------------
master = read_csv_if_exists("Olist_Cleaned_Full_Dataset.csv")
sales_month = read_csv_if_exists("Olist_Sales_By_Month.csv")
sales_state = read_csv_if_exists("Olist_Sales_By_State.csv")
sales_category = read_csv_if_exists("Olist_Sales_By_Category.csv")
customers_state = read_csv_if_exists("Olist_Customers_By_State.csv")
payment_methods = read_csv_if_exists("Olist_Payment_Methods.csv")
order_status = read_csv_if_exists("Olist_Order_Status.csv")
delivery_perf = read_csv_if_exists("Olist_Delivery_Performance.csv")
rfm_file = read_csv_if_exists("Olist_RFM_Segments.csv")

if master is None and sales_month is None:
    st.error("Please place 'Olist_Cleaned_Full_Dataset.csv' or at least 'Olist_Sales_By_Month.csv' in this folder.")
    st.stop()

# -----------------------
# Column detection
# -----------------------
PAY_COL = pick_col(master, ["payment_value", "payment_amount", "price", "payment"])
STATE_COL = pick_col(master, ["customer_state", "state", "customer_state_code"])
CITY_COL = pick_col(master, ["customer_city", "city"])
ORDER_DATE_COL = pick_col(master, ["order_purchase_timestamp", "order_date", "purchase_date"])
CUSTOMER_COL = pick_col(master, ["customer_unique_id", "customer_id"])
ORDER_COL = pick_col(master, ["order_id"])
PROD_CAT_COL = pick_col(master, ["product_category_name_english", "product_category_name", "category"])
DELIVERY_TIME_COL = pick_col(master, ["delivery_time", "delivery_time_days", "delivery_time_day"])

# Dates & derived fields
if master is not None and ORDER_DATE_COL and ORDER_DATE_COL in master.columns:
    master[ORDER_DATE_COL] = pd.to_datetime(master[ORDER_DATE_COL], errors="coerce")
    master["year"] = master[ORDER_DATE_COL].dt.year
    master["month_num"] = master[ORDER_DATE_COL].dt.month
    master["month_name"] = master[ORDER_DATE_COL].dt.strftime("%b")
    master["month_label"] = master[ORDER_DATE_COL].dt.strftime("%b %Y")

if master is not None and DELIVERY_TIME_COL is None:
    if "order_delivered_customer_date" in master.columns and ORDER_DATE_COL in master.columns:
        master["order_delivered_customer_date"] = pd.to_datetime(master["order_delivered_customer_date"], errors="coerce")
        master["delivery_time_days"] = (master["order_delivered_customer_date"] - master[ORDER_DATE_COL]).dt.days
        DELIVERY_TIME_COL = "delivery_time_days"

# -----------------------
# Sidebar filters
# -----------------------
with st.sidebar:
    st.markdown("<div style='text-align:center;font-size:18px'>🛒 <strong>Olist</strong></div>", unsafe_allow_html=True)
    st.markdown("---")

    years = ["All"] + sorted(master["year"].dropna().unique().astype(int).tolist()) if master is not None else ["All"]
    selected_year = st.selectbox("Year", years, index=0)

    states = ["All"] + sorted(customers_state["customer_state"].dropna().unique().tolist()) if customers_state is not None else ["All"]
    selected_state = st.selectbox("State", states, index=0)

    prodcats = ["All"]
    if sales_category is not None:
        pcol = pick_col(sales_category, ["product_category_name_english", "Category", "product_category_name"])
        if pcol:
            prodcats += sorted(list(sales_category[pcol].dropna().unique()))
    selected_product = st.selectbox("Product Category", prodcats, index=0)

# -----------------------
# Filter helper
# -----------------------
def apply_filters(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    if df is None:
        return None
    tmp = df.copy()
    if selected_year != "All" and "year" in tmp.columns:
        tmp = tmp[tmp["year"] == int(selected_year)]
    if selected_state != "All" and STATE_COL and STATE_COL in tmp.columns:
        tmp = tmp[tmp[STATE_COL] == selected_state]
    if selected_product != "All" and PROD_CAT_COL and PROD_CAT_COL in tmp.columns:
        tmp = tmp[tmp[PROD_CAT_COL] == selected_product]
    return tmp

filtered = apply_filters(master) if master is not None else None
source_df = filtered if filtered is not None else master

# ---------------------------
# Tabs: Dashboard Pages & Executive Report
# ---------------------------
tab1, tab2, tab3 = st.tabs(["Dashboard Page 1", "Dashboard Page 2", "Executive Report"])

# ---------------------------
# Page 1: Dashboard Page 1
# ---------------------------
with tab1:
    st.title("🛒 Brazilian E-commerce Dashboard - Page 1")

    # -------------------
    # KPI Row
    # -------------------
    k1, k2, k3, k4, k5 = st.columns(5)
    total_sales = filtered["payment_value"].sum() if "payment_value" in filtered.columns else 0
    total_orders = filtered["order_id"].nunique() if "order_id" in filtered.columns else 0
    unique_customers = filtered["customer_unique_id"].nunique() if "customer_unique_id" in filtered.columns else 0
    aov = total_sales / total_orders if total_orders else 0
    delivery_success = (filtered["order_status"]=="delivered").mean()*100 if "order_status" in filtered.columns else None

    k1.metric("Total Sales", fmt_k(total_sales))
    k2.metric("Total Orders", fmt_k(total_orders))
    k3.metric("Unique Customers", fmt_k(unique_customers))
    k4.metric("Avg Order Value", fmt_k(aov))
    k5.metric("Delivery Success %", f"{delivery_success:.1f}%" if delivery_success else "N/A")

    st.markdown("---")

    # -------------------
    # Layout 2x2 charts
    # -------------------
    r1c1, r1c2 = st.columns(2, gap="large")
    r2c1, r2c2 = st.columns(2, gap="large")

    # Sales by State (Geo Map)
    with r1c1:
        st.subheader("Sales by State")
        if "customer_state" in filtered.columns and "payment_value" in filtered.columns:
            s_df = filtered.groupby("customer_state")["payment_value"].sum().reset_index().rename(columns={"payment_value":"Sales"})
            STATE_CENTROIDS = {
                "AC": (-8.77, -70.55), "AL": (-9.62, -36.40), "AM": (-3.07, -61.66),
                "AP": (1.41, -51.77), "BA": (-12.96, -38.51), "CE": (-5.20, -39.53),
                "DF": (-15.83, -47.86), "ES": (-19.19, -40.34), "GO": (-15.42, -49.27),
                "MA": (-5.54, -45.27), "MG": (-18.10, -44.38), "MS": (-20.51, -54.54),
                "MT": (-12.64, -55.42), "PA": (-5.53, -52.29), "PB": (-7.06, -35.55),
                "PE": (-8.28, -36.57), "PI": (-7.71, -42.73), "PR": (-24.89, -51.55),
                "RJ": (-22.81, -42.99), "RN": (-5.22, -36.52), "RO": (-11.22, -62.80),
                "RR": (1.89, -61.22), "RS": (-30.03, -51.23), "SC": (-27.33, -49.44),
                "SE": (-10.57, -37.45), "SP": (-23.55, -46.63), "TO": (-10.25, -48.25)
            }
            s_df["lat"] = s_df["customer_state"].map(lambda c: STATE_CENTROIDS.get(c, (None,None))[0])
            s_df["lon"] = s_df["customer_state"].map(lambda c: STATE_CENTROIDS.get(c, (None,None))[1])
            s_map = s_df.dropna(subset=["lat","lon"])
            s_map["size"] = (s_map["Sales"]/s_map["Sales"].max())*60 + 6
            fig_state = px.scatter_mapbox(
                s_map, lat="lat", lon="lon", size="size", hover_name="customer_state",
                hover_data={"Sales":":,.0f"}, zoom=3.2, mapbox_style="carto-darkmatter", color_discrete_sequence=[BAR_COLOR]
            )
            st.plotly_chart(fig_state, use_container_width=True)

    # Customers by City (Geo Map)
    with r1c2:
        st.subheader("Customers by City")
        if "customer_city" in filtered.columns and "customer_unique_id" in filtered.columns:
            city_counts = filtered.groupby("customer_city")["customer_unique_id"].nunique().reset_index().rename(columns={"customer_unique_id":"Customers"})
            CITY_COORDS = {
                "sao paulo": (-23.55052, -46.633308), "rio de janeiro": (-22.906847, -43.172896),
                "belo horizonte": (-19.920682, -43.937088), "salvador": (-12.974722, -38.476389),
                "curitiba": (-25.427778, -49.273056), "recife": (-8.047562, -34.876964),
                "porto alegre": (-30.034647, -51.217658), "brasilia": (-15.793889, -47.882778),
                "fortaleza": (-3.71722, -38.54306), "manaus": (-3.10194, -60.025)
            }
            city_counts["lat"] = city_counts["customer_city"].str.lower().map(lambda x: CITY_COORDS.get(x, (None,None))[0])
            city_counts["lon"] = city_counts["customer_city"].str.lower().map(lambda x: CITY_COORDS.get(x, (None,None))[1])
            city_map = city_counts.dropna(subset=["lat","lon"])
            city_map["size"] = (city_map["Customers"]/city_map["Customers"].max())*60 + 6
            fig_city = px.scatter_mapbox(
                city_map, lat="lat", lon="lon", size="size", hover_name="customer_city",
                hover_data={"Customers":True}, zoom=3.2, mapbox_style="carto-darkmatter", color_discrete_sequence=[BAR_COLOR]
            )
            st.plotly_chart(fig_city, use_container_width=True)

    # Monthly Sales Trend
    with r2c1:
        st.subheader("Monthly Sales Trend")
        if "payment_value" in filtered.columns and "order_purchase_timestamp" in filtered.columns:
            monthly = filtered.groupby(filtered["order_purchase_timestamp"].dt.month)["payment_value"].sum().reindex(range(1,13), fill_value=0).reset_index()
            monthly["MonthName"] = monthly["index"].apply(lambda m: pd.Timestamp(2000,m,1).strftime("%b"))
            fig_month = px.line(monthly, x="MonthName", y="payment_value", markers=True, template="plotly_dark", line_shape="spline")
            fig_month.update_traces(line=dict(color=BAR_COLOR))
            st.plotly_chart(fig_month, use_container_width=True)

    # Yearly Sales Trend
    with r2c2:
        st.subheader("Yearly Sales Trend")
        if "payment_value" in filtered.columns and "year" in filtered.columns:
            yearly = filtered.groupby("year")["payment_value"].sum().reset_index()
            fig_year = px.line(yearly, x="year", y="payment_value", markers=True, template="plotly_dark")
            fig_year.update_traces(line=dict(color=BAR_COLOR))
            st.plotly_chart(fig_year, use_container_width=True)



# Page 2: Dashboard Page 2

with tab2:
    st.header("Sales & Product Insights")
    col1, col2 = st.columns(2)

    # Top 10 Product Categories
    with col1:
        st.subheader("Top 10 Product Categories by Sales")
        if PROD_CAT_COL in filtered.columns and "payment_value" in filtered.columns:
            tmp = filtered.groupby(PROD_CAT_COL)["payment_value"].sum().reset_index().sort_values("payment_value", ascending=False).head(10)
            fig_prod = px.bar(tmp, x="payment_value", y=PROD_CAT_COL, orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
            st.plotly_chart(fig_prod, use_container_width=True)

    # Payment Methods Pie
    with col2:
        st.subheader("Payment Methods")
        if "payment_type" in filtered.columns and "payment_value" in filtered.columns:
            tmp = filtered.groupby("payment_type")["payment_value"].sum().reset_index()
            fig_pay = px.pie(tmp, names="payment_type", values="payment_value", hole=0.35, color_discrete_sequence=PIE_PALETTE)
            st.plotly_chart(fig_pay, use_container_width=True)

    st.markdown("---")
    dl, dr = st.columns(2)

    # RFM Segments Pie
    with dl:
        st.subheader("RFM Segments")
        if rfm_file is not None and "segment" in rfm_file.columns and "count" in rfm_file.columns:
            tmp = rfm_file.groupby("segment")["count"].sum().reset_index()
            fig_rfm = px.pie(tmp, names="segment", values="count", hole=0.35, color_discrete_sequence=PIE_PALETTE)
            st.plotly_chart(fig_rfm, use_container_width=True)

    # Top 10 Delivery Performance
    with dr:
        st.subheader("Top 10 Delivery Performance (avg days)")
        if "delivery_time_days" in filtered.columns and "customer_state" in filtered.columns:
            tmp = filtered.groupby("customer_state")["delivery_time_days"].mean().reset_index().sort_values("delivery_time_days", ascending=False).head(10)
            fig_del = px.bar(tmp, x="delivery_time_days", y="customer_state", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
            st.plotly_chart(fig_del, use_container_width=True)

    # Order Status Breakdown
    st.markdown("---")
    st.subheader("Order Status Breakdown")
    if "order_status" in filtered.columns:
        tmp = filtered["order_status"].value_counts().reset_index().rename(columns={"index":"order_status", "order_status":"count"})
        fig_status = px.bar(tmp, x="count", y="order_status", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
        st.plotly_chart(fig_status, use_container_width=True)


# Page 3: Executive Report

with tab3:
    st.header("Executive Summary & Insights")

    # -------------------
    # Dataset Info & KPIs
    # -------------------
    st.markdown("### Dataset:")
    st.markdown("""
    Brazilian E-Commerce Public Dataset by Olist (Kaggle).  
    Key tables used: **orders, customers, order_items, payments, products, sellers, reviews**.
    """)

    st.markdown("### Key KPIs:")
    st.markdown(f"""
    - **Total Sales:** {fmt_k(total_sales)}
    - **Total Orders:** {fmt_k(total_orders)}
    - **Unique Customers:** {fmt_k(unique_customers)}
    - **Avg Order Value (AOV):** {fmt_k(aov)}
    - **Delivery Success Rate:** {f'{delivery_success:.1f}%' if delivery_success else 'N/A'}
    """)

    st.markdown("---")

   
    # Executive Summary
   
    st.markdown("### Executive Summary & Insights")
    st.markdown(textwrap.dedent(f"""
    This comprehensive report analyzes the Olist Brazilian e-commerce dataset to provide actionable insights across revenue, customer behavior, product performance, payment methods, and delivery operations.

    **Key Highlights:**
    - **Revenue:** Top 10 product categories contribute the majority of total sales. Seasonal peaks are observed, particularly during high-demand months, suggesting strong promotional opportunities.
    - **Customer Segmentation:** RFM analysis identifies high-value 'Champions', average-value 'Loyal', and at-risk 'At-Risk' customers. Retention campaigns should focus on the latter to maximize revenue and loyalty.
    - **Payment Methods:** The majority of transactions are conducted via credit card and boleto, highlighting opportunities to incentivize preferred payment methods for higher conversion.
    - **Delivery Performance:** Certain states consistently exhibit longer delivery times, affecting customer satisfaction. Regional fulfillment centers or logistics optimizations may improve performance.
    - **Geographic Insights:** Sales and customers are concentrated in metro areas such as São Paulo, Rio de Janeiro, and Belo Horizonte. Expansion strategies should consider underserved regions.

    **Recommendations:**
    1. Optimize inventory and promotional campaigns around top-performing categories to boost revenue.
    2. Target 'At-Risk' and 'Loyal' segments with personalized campaigns to improve retention and lifetime value.
    3. Monitor delivery KPIs weekly and implement improvements in slow-performing states.
    4. Incentivize preferred payment methods to increase transaction efficiency and conversion.
    5. Use the dashboard as a real-time monitoring tool to track KPIs and adjust strategy dynamically.

    The insights provided here aim to guide leadership decision-making and drive both operational efficiency and revenue growth across all channels.
    """))

    st.markdown("---")
    st.markdown("💡 **Tip:** Use the camera icon in your browser or Streamlit's screenshot tool to capture this page as a PNG for reports or LinkedIn posts.")

