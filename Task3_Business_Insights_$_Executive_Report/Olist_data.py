import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load all the datasets
customers = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_customers_dataset.csv")
geolocation = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_geolocation_dataset.csv")
order_items = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_order_items_dataset.csv")
payments = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_order_payments_dataset.csv")
reviews = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_order_reviews_dataset.csv")
orders = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_orders_dataset.csv")
products = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_products_dataset.csv")
sellers = pd.read_csv(r"C:\Users\larowolo\Downloads\olist_sellers_dataset.csv")
translation = pd.read_csv(r"C:\Users\larowolo\Downloads\product_category_name_translation.csv")

# --- Start Merging ---
# Merge orders with customers
df = pd.merge(orders, customers, on='customer_id')

# Merge with order_items
df = pd.merge(df, order_items, on='order_id')

# Merge with payments
df = pd.merge(df, payments, on='order_id')

# Merge with reviews
df = pd.merge(df, reviews, on='order_id')

# Merge with products
df = pd.merge(df, products, on='product_id')

# Merge with sellers
df = pd.merge(df, sellers, on='seller_id')

# Merge with category name translation
df = pd.merge(df, translation, on='product_category_name')

# Handling missing values
# 1. Handle NUMERIC missing values (tiny amount — safe to fill)
numeric_cols_to_fill = [
    "product_weight_g", "product_length_cm", 
    "product_height_cm", "product_width_cm"
]

for col in numeric_cols_to_fill:
    df[col] = df.groupby("product_category_name_english")[col].transform(
        lambda x: x.fillna(x.median())
    )

# 2. Handle TEXT missing values (optional fill for reporting but safe to keep NaN)
text_cols_to_fill = ["review_comment_title", "review_comment_message"]

for col in text_cols_to_fill:
    df[col] = df[col].fillna("No Comment")  # If using NLP/visuals; otherwise you can leave NaN

# 3. Keep DELIVERY TIMESTAMPS as NaN, but add helper flags for analysis
df["is_order_approved"] = df["order_approved_at"].notna()
df["is_delivered_to_carrier"] = df["order_delivered_carrier_date"].notna()
df["is_delivered_to_customer"] = df["order_delivered_customer_date"].notna()

# 4. OPTIONAL: Create "delivery_time_days" where possible
df["delivery_time_days"] = (
    pd.to_datetime(df["order_delivered_customer_date"]) -
    pd.to_datetime(df["order_purchase_timestamp"])
).dt.days

# If delivery date is missing (i.e., undelivered), keep delivery_time_days as NaN



# Convert date columns to datetime objects
date_columns = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date',
    'shipping_limit_date'
]
for col in date_columns:
    df[col] = pd.to_datetime(df[col])

# Feature Engineering
# Calculate delivery time
df['delivery_time'] = (df['order_delivered_customer_date'] - df['order_purchase_timestamp']).dt.days

# Extract month, year, and day of week
df['purchase_year'] = df['order_purchase_timestamp'].dt.year
df['purchase_month'] = df['order_purchase_timestamp'].dt.month
df['purchase_dayofweek'] = df['order_purchase_timestamp'].dt.day_name()

# Monthly Sales Trend
monthly_sales = df.groupby(['purchase_year', 'purchase_month'])['payment_value'].sum().reset_index()
monthly_sales['year_month'] = monthly_sales['purchase_year'].astype(str) + '-' + monthly_sales['purchase_month'].astype(str).str.zfill(2)

plt.figure(figsize=(15, 6))
sns.lineplot(x='year_month', y='payment_value', data=monthly_sales.sort_values('year_month'))
plt.title('Total Sales Over Time')
plt.xlabel('Month')
plt.ylabel('Total Sales Value')
plt.xticks(rotation=45)
plt.show()

# Top 10 Product Categories by Sales
top_categories = df.groupby('product_category_name_english')['payment_value'].sum().nlargest(10)

plt.figure(figsize=(12, 8))
sns.barplot(y=top_categories.index, x=top_categories.values, palette='viridis')
plt.title('Top 10 Product Categories by Sales')
plt.xlabel('Total Sales Value')
plt.ylabel('Product Category')
plt.show()

# --- RFM Calculation ---
snapshot_date = df['order_purchase_timestamp'].max() + pd.DateOffset(days=1)

# Calculate Recency, Frequency, and Monetary value
rfm = df.groupby('customer_unique_id').agg({
    'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
    'order_id': 'count',
    'payment_value': 'sum'
}).rename(columns={
    'order_purchase_timestamp': 'Recency',
    'order_id': 'Frequency',
    'payment_value': 'Monetary'
})

# Create RFM quantiles
r_labels = range(4, 0, -1)
f_labels = range(1, 5)
m_labels = range(1, 5)
rfm['R_score'] = pd.qcut(rfm['Recency'], q=4, labels=r_labels, duplicates='drop')
rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=4, labels=f_labels)
rfm['M_score'] = pd.qcut(rfm['Monetary'], q=4, labels=m_labels)

# Combine scores
rfm['RFM_Score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)

print(rfm.head())

# RFM distribution plot
rfm['Segment'] = rfm['RFM_Score'].apply(
    lambda x: 'Champions' if x.startswith(('44','43')) else
              'Loyal' if x.startswith(('34','33')) else
              'At Risk'
)

segment_counts = rfm['Segment'].value_counts()

plt.figure(figsize=(8,4))
sns.barplot(x=segment_counts.index, y=segment_counts.values)
plt.title("Customer Segmentation")
plt.show()

#Payment Method Breakdown
payment_counts = df['payment_type'].value_counts()

plt.figure(figsize=(8,4))
sns.barplot(x=payment_counts.index, y=payment_counts.values)
plt.title("Payment Methods Used")
plt.show()

#Order Status Distribution
order_status_counts = df['order_status'].value_counts()

plt.figure(figsize=(8,4))
sns.barplot(x=order_status_counts.index, y=order_status_counts.values)
plt.title("Order Status Breakdown")
plt.xticks(rotation=45)
plt.show()

# Delivry Performance
delivery_by_state = df.groupby('customer_state')['delivery_time'].mean().sort_values()

plt.figure(figsize=(12,6))
delivery_by_state.plot(kind='bar')
plt.title("Average Delivery Time by State")
plt.ylabel("Days")
plt.show()


# Export the cleaned dataframe to a CSV file
df.to_csv('olist_cleaned_dataset.csv', index=False)

#  export the RFM analysis results
rfm.to_csv('rfm_analysis.csv', index=False)


# Display the first 5 rows and info of the merged dataframe
print("Merged DataFrame Head:")
print(df.head())
print("\nMerged DataFrame Info:")

df.info()


# -----------------------------
# 1. SALES OVER TIME (Monthly)
# -----------------------------
monthly_sales = df.groupby(['purchase_year', 'purchase_month'])['payment_value'].sum().reset_index()
monthly_sales['year_month'] = monthly_sales['purchase_year'].astype(str) + '-' + monthly_sales['purchase_month'].astype(str).str.zfill(2)
monthly_sales.to_csv('tableau_sales_monthly.csv', index=False)

# -----------------------------
# 2. SALES BY PRODUCT CATEGORY
# -----------------------------
category_sales = df.groupby('product_category_name_english')['payment_value'].sum().reset_index()
category_sales.to_csv('tableau_sales_by_category.csv', index=False)

# -----------------------------
# 3. SALES BY STATE (Geographic Map)
# -----------------------------
state_sales = df.groupby('customer_state')['payment_value'].sum().reset_index()
state_sales.to_csv('tableau_sales_by_state.csv', index=False)

# -----------------------------
# 4. ORDER STATUS BREAKDOWN
# -----------------------------
order_status = df['order_status'].value_counts().reset_index()
order_status.columns = ['order_status', 'count']
order_status.to_csv('tableau_order_status.csv', index=False)

# -----------------------------
# 5. PAYMENT METHOD BREAKDOWN
# -----------------------------
payment_type_counts = df['payment_type'].value_counts().reset_index()
payment_type_counts.columns = ['payment_type', 'count']
payment_type_counts.to_csv('tableau_payment_methods.csv', index=False)

# -----------------------------
# 6. DELIVERY PERFORMANCE (Avg Delivery Time by State)
# -----------------------------
delivery_by_state = df.groupby('customer_state')['delivery_time'].mean().reset_index()
delivery_by_state.columns = ['customer_state', 'avg_delivery_days']
delivery_by_state.to_csv('tableau_delivery_by_state.csv', index=False)

# -----------------------------
# 7. RFM SEGMENT COUNT
# -----------------------------
# If not already segmented:
rfm['Segment'] = rfm['RFM_Score'].apply(
    lambda x: 'Champions' if x.startswith(('44','43')) else
              'Loyal' if x.startswith(('34','33')) else
              'At Risk'
)

rfm_segment_counts = rfm['Segment'].value_counts().reset_index()
rfm_segment_counts.columns = ['Segment', 'count']
rfm_segment_counts.to_csv('tableau_rfm_segment_counts.csv', index=False)

# -----------------------------
# 8. FULL CLEANED DATA (Optional Master Export for Tableau)
# -----------------------------
df.to_csv('tableau_full_cleaned_dataset.csv', index=False)

print("✅ All Tableau export files generated!")
