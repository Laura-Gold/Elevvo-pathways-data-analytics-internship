import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import textwrap
from typing import Optional


# Theme

st.set_page_config(page_title="Brazilian E-commerce Performance Dashboard",
                   layout="wide", page_icon="🛒")

# Minimal CSS for KPI boxes & dark background
st.markdown(
    """
    <style>
    .stApp { background-color: #0b0c10; color: #e6eef6; }
    .kpi { background: rgba(255,255,255,0.02); padding: 10px; border-radius: 8px; text-align:center;}
    .kpi-label { color: #9aaab5; font-size:12px; }
    .kpi-value { font-size:20px; font-weight:700; }
    .sidebar .stSelectbox, .sidebar .stButton { color: #e6eef6; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Colors & config
PRIMARY = "#4f46e5"
BAR_COLOR = PRIMARY
PIE_PALETTE = px.colors.qualitative.Dark24
DATA_DIR = Path(".")

# Small city coords (expand as needed)
CITY_COORDS = {
    "sao paulo": (-23.55052, -46.633308),
    "rio de janeiro": (-22.906847, -43.172896),
    "belo horizonte": (-19.920682, -43.937088),
    "salvador": (-12.974722, -38.476389),
    "curitiba": (-25.427778, -49.273056),
    "recife": (-8.047562, -34.876964),
    "porto alegre": (-30.034647, -51.217658),
    "brasilia": (-15.793889, -47.882778),
    "fortaleza": (-3.71722, -38.54306),
    "manaus": (-3.10194, -60.025),
    "belem": (-1.455833, -48.504444),
    "goiania": (-16.686891, -49.264788),
    "campinas": (-22.90556, -47.06083),
    "niteroi": (-22.8833, -43.1033),
    "joao pessoa": (-7.119495, -34.845011),
    "maceio": (-9.66599, -35.735),
    "florianopolis": (-27.5954, -48.5480),
    "cuiaba": (-15.5989, -56.0949),
    "vitoria": (-20.3155, -40.3128),
}

STATE_CENTROIDS = {
    "AC": (-8.77, -70.55), "AL": (-9.62, -36.40), "AM": (-3.07, -61.66), "AP": (1.41, -51.77),
    "BA": (-12.96, -38.51), "CE": (-5.20, -39.53), "DF": (-15.83, -47.86), "ES": (-19.19, -40.34),
    "GO": (-15.42, -49.27), "MA": (-5.54, -45.27), "MG": (-18.10, -44.38), "MS": (-20.51, -54.54),
    "MT": (-12.64, -55.42), "PA": (-5.53, -52.29), "PB": (-7.06, -35.55), "PE": (-8.28, -36.57),
    "PI": (-7.71, -42.73), "PR": (-24.89, -51.55), "RJ": (-22.81, -42.99), "RN": (-5.22, -36.52),
    "RO": (-11.22, -62.80), "RR": (1.89, -61.22), "RS": (-30.03, -51.23), "SC": (-27.33, -49.44),
    "SE": (-10.57, -37.45), "SP": (-23.55, -46.63), "TO": (-10.25, -48.25)
}


# Helpers Function

def read_csv_if_exists(fn: str) -> Optional[pd.DataFrame]:
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
    # contains fallback
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


# Load datasets

master = read_csv_if_exists("Olist_Cleaned_Full_Dataset.csv")     # Unable to upload on GitHub due to the size but can be accessed through the link in the requirements file.
sales_month = read_csv_if_exists("Olist_Sales_By_Month.csv")
sales_state = read_csv_if_exists("Olist_Sales_By_State.csv")
sales_category = read_csv_if_exists("Olist_Sales_By_Category.csv")
customers_state = read_csv_if_exists("Olist_Customers_By_State.csv")
payment_methods = read_csv_if_exists("Olist_Payment_Methods.csv")
order_status = read_csv_if_exists("Olist_Order_Status.csv")
delivery_perf = read_csv_if_exists("Olist_Delivery_Performance.csv")
rfm_file = read_csv_if_exists("Olist_RFM_Segments.csv")

if master is None and sales_month is None:
    st.error("Place 'Olist_Cleaned_Full_Dataset.csv' (preferred) or 'Olist_Sales_By_Month.csv' in this folder.")
    st.stop()

# Robust column detection in master
PAY_COL = pick_col(master, ["payment_value", "payment_amount", "price", "payment"])
STATE_COL = pick_col(master, ["customer_state", "state", "customer_state_code"])
CITY_COL = pick_col(master, ["customer_city", "city"])
ORDER_DATE_COL = pick_col(master, ["order_purchase_timestamp", "order_date", "purchase_date"])
CUSTOMER_COL = pick_col(master, ["customer_unique_id", "customer_id"])
ORDER_COL = pick_col(master, ["order_id"])
PROD_CAT_COL = pick_col(master, ["product_category_name_english", "product_category_name", "product_category", "category"])
DELIVERY_TIME_COL = pick_col(master, ["delivery_time", "delivery_time_days", "delivery_time_day"])

# normalize master dates & derived fields if available
if master is not None and ORDER_DATE_COL and ORDER_DATE_COL in master.columns:
    master[ORDER_DATE_COL] = pd.to_datetime(master[ORDER_DATE_COL], errors="coerce")
    master["year"] = master[ORDER_DATE_COL].dt.year
    master["month_num"] = master[ORDER_DATE_COL].dt.month
    master["month_name"] = master[ORDER_DATE_COL].dt.strftime("%b")
    master["month_label"] = master[ORDER_DATE_COL].dt.strftime("%b %Y")

# If delivery_time missing but delivered / purchase timestamps exist, compute
if master is not None and DELIVERY_TIME_COL is None:
    if "order_delivered_customer_date" in master.columns and ORDER_DATE_COL in master.columns:
        master["order_delivered_customer_date"] = pd.to_datetime(master["order_delivered_customer_date"], errors="coerce")
        master["delivery_time_days"] = (master["order_delivered_customer_date"] - master[ORDER_DATE_COL]).dt.days
        DELIVERY_TIME_COL = "delivery_time_days"


# Sidebar filters (Olist label + icon)

with st.sidebar:
    st.markdown("<div style='text-align:center;font-size:18px'>🛒 <strong>Olist</strong></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#9aaab5;margin-bottom:6px'>⬇️</div>", unsafe_allow_html=True)
    st.markdown("---")

    years = ["All"]
    if master is not None and "year" in master.columns:
        years += sorted(master["year"].dropna().unique().astype(int).tolist())
    selected_year = st.selectbox("Year", years, index=0)

    states = ["All"]
    if customers_state is not None and "customer_state" in customers_state.columns:
        states += sorted(customers_state["customer_state"].dropna().unique().tolist())
    elif master is not None and STATE_COL:
        states += sorted(master[STATE_COL].dropna().unique().tolist())
    selected_state = st.selectbox("State", states, index=0)

    prodcats = ["All"]
    if sales_category is not None:
        pcol = pick_col(sales_category, ["product_category_name_english", "Category", "product_category_name"])
        if pcol:
            prodcats += sorted(list(sales_category[pcol].dropna().unique()))
    elif PROD_CAT_COL and master is not None:
        prodcats += sorted(list(master[PROD_CAT_COL].dropna().unique()))
    selected_product = st.selectbox("Product Category", prodcats, index=0)

    st.markdown("---")
    st.markdown("<div style='color:#9aaab5;font-size:12px'>Tip: Monthly axis shows Jan–Dec. Use Year to filter months.</div>", unsafe_allow_html=True)


# Apply filters helper
) -> Optional[pd.DataFrame]:
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


# Tabs

tab1, tab2, tab3 = st.tabs(["Dashboard Page 1", "Dashboard Page 2", "Executive Report"])


# Page 1 (4 charts): Order: 3,4,1,2

with tab1:
    st.title("🛒 Brazilian E-commerce Performance Dashboard")
    st.markdown("Maps & trends. Use the sidebar to filter.")

    # KPI row
    k1, k2, k3, k4, k5 = st.columns([1.6,1,1,1,1])
    total_sales = None
    if source_df is not None and PAY_COL and PAY_COL in source_df.columns:
        total_sales = source_df[PAY_COL].sum(min_count=1)

    total_orders = None
    if source_df is not None and ORDER_COL and ORDER_COL in source_df.columns:
        total_orders = source_df[ORDER_COL].nunique()

    unique_customers = None
    if source_df is not None and CUSTOMER_COL and CUSTOMER_COL in source_df.columns:
        unique_customers = source_df[CUSTOMER_COL].nunique()

    aov = (total_sales / total_orders) if total_sales and total_orders else None

    delivery_success = None
    if master is not None and "is_delivered_to_customer" in master.columns:
        try:
            delivery_success = master["is_delivered_to_customer"].astype(bool).mean() * 100
        except Exception:
            delivery_success = None

    k1.markdown(f"<div class='kpi'><div class='kpi-label'>Total Sales</div><div class='kpi-value'>{fmt_k(total_sales)}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><div class='kpi-label'>Total Orders</div><div class='kpi-value'>{fmt_k(total_orders)}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi'><div class='kpi-label'>Unique Customers</div><div class='kpi-value'>{fmt_k(unique_customers)}</div></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='kpi'><div class='kpi-label'>Avg Order Value</div><div class='kpi-value'>{fmt_k(aov) if aov else 'N/A'}</div></div>", unsafe_allow_html=True)
    k5.markdown(f"<div class='kpi'><div class='kpi-label'>Delivery Success %</div><div class='kpi-value'>{f'{delivery_success:.1f}%' if delivery_success is not None else 'N/A'}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # layout 2x2
    r1c1, r1c2 = st.columns(2, gap="large")
    r2c1, r2c2 = st.columns(2, gap="large")

    # Sales by State (map)
    with r1c1:
        st.subheader("Sales by State")
        s_df = None
        if filtered is not None and STATE_COL in filtered.columns and PAY_COL in filtered.columns:
            s_df = filtered.groupby(STATE_COL)[PAY_COL].sum().reset_index().rename(columns={STATE_COL:"State", PAY_COL:"Sales"})
        elif sales_state is not None:
            s_df = sales_state.copy()
            if len(s_df.columns) >= 2:
                s_df.columns = ["State","Sales"]
        if s_df is None or s_df.empty:
            st.info("Sales-by-state data not available.")
        else:
            s_df["code"] = s_df["State"].astype(str).str.upper().str.strip()
            s_df["lat"] = s_df["code"].apply(lambda c: STATE_CENTROIDS.get(c, (None,None))[0])
            s_df["lon"] = s_df["code"].apply(lambda c: STATE_CENTROIDS.get(c, (None,None))[1])
            s_map = s_df.dropna(subset=["lat","lon"]).copy()
            if not s_map.empty:
                s_map["size"] = (s_map["Sales"] / (s_map["Sales"].max()+1)) * 60 + 6
                fig = px.scatter_map(
                    s_map, lat="lat", lon="lon", size="size", hover_name="State",
                    hover_data={"Sales":":,.0f"}, color_discrete_sequence=[BAR_COLOR],
                    zoom=3.2, center={"lat": -14.2, "lon": -51.9}, map_style="carto-darkmatter"
                )
                fig = set_transparent(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                tmp = s_df.sort_values("Sales", ascending=False).head(20)
                fig = px.bar(tmp, x="Sales", y="State", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
                fig = set_transparent(fig)
                st.plotly_chart(fig, use_container_width=True)

    # Customers by City (map)
    with r1c2:
        st.subheader("Customers by City")
        if master is None or CITY_COL is None or CITY_COL not in master.columns:
            st.info("Customer city column not found.")
        else:
            src = filtered if filtered is not None else master
            if CUSTOMER_COL and CUSTOMER_COL in src.columns:
                city_counts = src.groupby(src[CITY_COL].astype(str).str.strip().str.lower())[CUSTOMER_COL].nunique().reset_index()
                city_counts.columns = ["city_key","Customers"]
            else:
                city_counts = src.groupby(src[CITY_COL].astype(str).str.strip().str.lower()).size().reset_index(name="Customers")
                city_counts.columns = ["city_key","Customers"]

            city_counts["lat"] = city_counts["city_key"].apply(lambda x: CITY_COORDS.get(x, (None,None))[0])
            city_counts["lon"] = city_counts["city_key"].apply(lambda x: CITY_COORDS.get(x, (None,None))[1])
            city_map = city_counts.dropna(subset=["lat","lon"]).copy()
            if not city_map.empty:
                city_map["size"] = (city_map["Customers"] / (city_map["Customers"].max()+1)) * 60 + 6
                fig = px.scatter_map(
                    city_map, lat="lat", lon="lon", size="size", hover_name="city_key",
                    hover_data={"Customers":True}, color_discrete_sequence=[BAR_COLOR],
                    zoom=3.2, center={"lat": -14.2, "lon": -51.9}, map_style="carto-darkmatter"
                )
                fig = set_transparent(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                top_cities = city_counts.sort_values("Customers", ascending=False).head(20)
                if not top_cities.empty:
                    fig = px.bar(top_cities, x="Customers", y="city_key", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
                    fig = set_transparent(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No city-level data available.")

    # Monthly Trend (Jan-Dec)
    with r2c1:
        st.subheader("Monthly Sales Trend")
        src = filtered if filtered is not None else master
        if src is not None and ORDER_DATE_COL in src.columns and PAY_COL in src.columns:
            tmp = src.copy()
            tmp["month_num"] = tmp[ORDER_DATE_COL].dt.month
            monthly = tmp.groupby("month_num")[PAY_COL].sum().reindex(range(1,13), fill_value=0).reset_index().rename(columns={PAY_COL:"Sales", "month_num":"Month"})
            monthly["MonthName"] = monthly["Month"].apply(lambda m: pd.Timestamp(2000, m, 1).strftime("%b"))
            fig = px.line(monthly, x="MonthName", y="Sales", markers=True, template="plotly_dark")
            fig.update_traces(line=dict(color=BAR_COLOR))
            fig = set_transparent(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Monthly series not available.")

    # Yearly Trend
    with r2c2:
        st.subheader("Yearly Sales Trend")
        src = filtered if filtered is not None else master
        if src is not None and "year" in src.columns and PAY_COL in src.columns:
            yearly = src.groupby("year")[PAY_COL].sum().reset_index().rename(columns={PAY_COL:"Sales"})
            fig = px.line(yearly.sort_values("year"), x="year", y="Sales", markers=True, template="plotly_dark")
            fig.update_traces(line=dict(color=BAR_COLOR))
            fig = set_transparent(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Yearly series not available.")


# Page 2: product/payment/rfm/delivery + orderstatus full row

with tab2:
    st.header("Sales & Product Insights")

    col1, col2 = st.columns(2)
    # Top 10 Product Categories
    with col1:
        st.subheader("Top 10 Product Categories by Sales")
        plotted = False
        if sales_category is not None:
            prod_col = pick_col(sales_category, ["product_category_name_english", "product_category_name", "Category"])
            val_col = pick_col(sales_category, ["payment_value", "Sales", "payment"])
            if prod_col and val_col:
                tmp = sales_category.groupby(prod_col)[val_col].sum().reset_index().sort_values(val_col, ascending=False).head(10)
                fig = px.bar(tmp, x=val_col, y=prod_col, orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
                fig = set_transparent(fig)
                st.plotly_chart(fig, use_container_width=True)
                plotted = True
        if not plotted:
            if master is not None and PROD_CAT_COL in master.columns and PAY_COL in master.columns:
                tmp = master.groupby(PROD_CAT_COL)[PAY_COL].sum().reset_index().sort_values(PAY_COL, ascending=False).head(10)
                tmp = tmp.rename(columns={PROD_CAT_COL:"Category", PAY_COL:"Sales"})
                fig = px.bar(tmp, x="Sales", y="Category", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
                fig = set_transparent(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Top product data not available.")

    # Payment methods pie
    with col2:
        st.subheader("Payment Methods")
        if payment_methods is not None and len(payment_methods.columns) >= 2:
            pm_cat = payment_methods.columns[0]
            pm_val = payment_methods.columns[1]
            pm_df = payment_methods.copy()
            pm_df[pm_cat] = pm_df[pm_cat].fillna("Not defined")
            pm_agg = pm_df.groupby(pm_cat)[pm_val].sum().reset_index().sort_values(pm_val, ascending=False)
            fig = px.pie(pm_agg, names=pm_cat, values=pm_val, hole=0.35, color_discrete_sequence=PIE_PALETTE)
            fig = set_transparent(fig)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            pay_col = pick_col(master, ["payment_type", "payment_method", "payment"])
            if filtered is not None and pay_col and pay_col in filtered.columns:
                tmp = filtered[pay_col].fillna("Not defined").value_counts().reset_index().rename(columns={"index":"method", pay_col:"count"})
                tmp = tmp.sort_values("count", ascending=False)
                fig = px.pie(tmp, names="method", values="count", hole=0.35, color_discrete_sequence=PIE_PALETTE)
                fig = set_transparent(fig)
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Payment methods not available.")

    st.markdown("---")

    # RFM pie + Delivery top10 side-by-side
    dl, dr = st.columns(2)
    with dl:
        st.subheader("RFM Segments")
        plotted_rfm = False
        if rfm_file is not None:
            seg_col = pick_col(rfm_file, ["segment", "Segment", "rfm_segment"])
            val_col = pick_col(rfm_file, ["count", "customers", "value"])
            if seg_col and val_col:
                rf_agg = rfm_file.groupby(seg_col)[val_col].sum().reset_index().sort_values(val_col, ascending=False)
                rf_agg.columns = ["Segment","Count"]
                fig = px.pie(rf_agg, names="Segment", values="Count", hole=0.35, color_discrete_sequence=PIE_PALETTE)
                fig = set_transparent(fig)
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                plotted_rfm = True
        if not plotted_rfm:
            # fallback compute approximate RFM if possible
            if master is not None and CUSTOMER_COL in master.columns and ORDER_COL in master.columns:
                try:
                    # compute recency, frequency, monetary
                    last_date = pd.to_datetime(master[ORDER_DATE_COL]).max() if ORDER_DATE_COL in master.columns else None
                    rfm_df = master.groupby(CUSTOMER_COL).agg({
                        ORDER_DATE_COL: lambda d: (pd.to_datetime(last_date) - pd.to_datetime(d.max())).days if last_date is not None else 9999,
                        ORDER_COL: 'count',
                        PAY_COL: 'sum' if PAY_COL and PAY_COL in master.columns else (lambda s: 0)
                    }).reset_index().rename(columns={ORDER_DATE_COL:"Recency", ORDER_COL:"Frequency", PAY_COL:"Monetary"})
                    # create quartiles
                    rfm_df["R_score"] = pd.qcut(rfm_df["Recency"].rank(method='first'), 4, labels=[4,3,2,1])
                    rfm_df["F_score"] = pd.qcut(rfm_df["Frequency"].rank(method='first'), 4, labels=[1,2,3,4])
                    rfm_df["M_score"] = pd.qcut(rfm_df["Monetary"].rank(method='first'), 4, labels=[1,2,3,4])
                    rfm_df["RFM_Score"] = rfm_df["R_score"].astype(str) + rfm_df["F_score"].astype(str) + rfm_df["M_score"].astype(str)
                    def rfm_label(s):
                        s = str(s)
                        if s.startswith(("44","43")): return "Champions"
                        if s.startswith(("34","33")): return "Loyal"
                        if s.startswith(("24","23")): return "Potential"
                        return "At Risk"
                    rfm_df["Segment"] = rfm_df["RFM_Score"].apply(rfm_label)
                    seg_counts = rfm_df["Segment"].value_counts().reset_index().rename(columns={"index":"Segment","Segment":"Count"})
                    seg_counts.columns = ["Segment","Count"]
                    fig = px.pie(seg_counts, names="Segment", values="Count", hole=0.35, color_discrete_sequence=PIE_PALETTE)
                    fig = set_transparent(fig)
                    fig.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.info("Unable to compute RFM segments.")
            else:
                st.info("RFM data not available.")

    with dr:
        st.subheader("Top 10 Delivery Performance (avg days)")
        if delivery_perf is not None and "customer_state" in delivery_perf.columns and "avg_delivery_days" in delivery_perf.columns:
            dp = delivery_perf.sort_values("avg_delivery_days", ascending=False).head(10)
            fig = px.bar(dp, x="avg_delivery_days", y="customer_state", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
            fig = set_transparent(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            dcol = DELIVERY_TIME_COL
            if filtered is not None and dcol and STATE_COL in filtered.columns:
                tmp = filtered.groupby(STATE_COL)[dcol].mean().reset_index().rename(columns={STATE_COL:"customer_state", dcol:"avg_delivery_days"}).sort_values("avg_delivery_days", ascending=False).head(10)
                fig = px.bar(tmp, x="avg_delivery_days", y="customer_state", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
                fig = set_transparent(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Delivery performance data not available.")

    st.markdown("---")
    st.subheader("Order Status Breakdown (All)")
    # prefer external order_status file else master
    if order_status is not None and len(order_status.columns) >= 2:
        cat = order_status.columns[0]; val = order_status.columns[1]
        os_df = order_status.groupby(cat)[val].sum().reset_index().sort_values(val, ascending=False)
        os_df = os_df.rename(columns={cat:"order_status", val:"count"})
        fig = px.bar(os_df, x="count", y="order_status", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
        fig = set_transparent(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        status_col = pick_col(master, ["order_status", "status"])
        if master is not None and status_col and status_col in master.columns:
            tmp = master[status_col].fillna("Unknown").value_counts().reset_index()
            tmp.columns = ["order_status","count"]
            tmp = tmp.sort_values("count", ascending=False)
            fig = px.bar(tmp, x="count", y="order_status", orientation="h", template="plotly_dark", color_discrete_sequence=[BAR_COLOR])
            fig = set_transparent(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Order status data not available.")


# Page 3: Executive Report 

with tab3:
    st.header("Business Insights & Executive Report for the Olist e-commerce dataset.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Sales", fmt_k(total_sales) if total_sales is not None else "N/A")
    m2.metric("Unique Customers", fmt_k(unique_customers) if unique_customers is not None else "N/A")
    m3.metric("Avg Order Value", fmt_k(aov) if aov is not None else "N/A")

    st.markdown("---")
    st.markdown("### Executive summary")
    st.markdown(textwrap.dedent("""
    This report provides a comprehensive analysis of Olist e-commerce performance across sales, customers, products, and delivery.
    It surfaces geographic concentration, temporal patterns, product-level revenue concentration, payment behaviour, and customer segments.
    """))

    st.markdown("---")
    st.markdown("### Objective")
    st.markdown(textwrap.dedent("""
    Deliver decision-ready insights into sales, customer value, product performance and logistics using the Olist dataset.

    """))

    st.markdown("### Dataset")
    st.markdown(textwrap.dedent("""
    - Brazilian E-Commerce Public Dataset by Olist (Kaggle). Key tables used: orders, customers, order_items, payments, products, sellers, reviews.
    - Key KPIs:
- **Total Sales:** $20.3M
- **Total Orders:** 99.4K
- **Unique Customers:** 96.1K
- **Avg Order Value (AOV):** $204
- **Delivery Success Rate:** 97.1%

                                
                                """))

    st.markdown("### Top Insights")
    st.markdown(textwrap.dedent("""
1. **Revenue concentration:** Top product categories contribute the majority of revenue, prioritize inventory for these.
2. **Customer value:** RFM segmentation shows Champions and a notable At-Risk pool, run targeted reactivation.
3. **Geography & logistics:** Sales concentrated in large metro areas; certain states have high average delivery times, optimize carriers/fulfillment.
4. **Seasonality:** Monthly peaks suggest best windows for promotions.
    """))

    st.markdown("### Recommendations")
    st.markdown(textwrap.dedent("""
    - Improve logistics in slow states; pilot regional fulfillment.
    - Prioritize retention for Champions & Loyal segments; reactivation campaigns for At-Risk.
    - Invest in inventory for top-performing categories; test bundles for mid-performing ones.
    - Optimize checkout for dominant payment methods; test incentives for preferred methods.
    - Operationalize the dashboard for weekly KPI monitoring and test improvements.
                                
    """))

    

    st.markdown("---")
    


   
       
