🧩 Customer Segmentation Using RFM Analysis

This project applies RFM (Recency, Frequency, Monetary) analysis to segment customers based on their purchasing behavior using the Online Retail Dataset.
The goal is to help businesses understand customer value, improve retention strategies, and design targeted marketing campaigns.

📊 Project Overview

RFM analysis is a proven customer segmentation technique that evaluates how recently and how often customers purchase, and how much they spend.

In this project, I used Python to:

-Analyze customer transactions.

-Compute Recency, Frequency, and Monetary scores.

-Assign customers into meaningful segments.

-Visualize the results to identify behavioral patterns.

🧠 Methodology

1. Data Preparation

-Loaded and cleaned the Online Retail Dataset containing:
InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country.

-Removed missing CustomerID values and cancelled transactions.

-Created a TotalPrice column (Quantity × UnitPrice).

2. RFM Metric Calculation

For each customer:

-Recency: Days since last purchase

-Frequency: Number of transactions made

-Monetary: Total amount spent

3. Scoring and Segmentation

-Assigned scores (1–5) for each RFM metric using quantiles.

-Combined scores into an overall RFM score.

-Grouped customers into segments such as:

~Champions

~Loyal Customers

~At Risk

~Hibernating

~Lost Customers

4. Visualization

Used Matplotlib and Seaborn to create:

-RFM heatmaps showing segment distribution.

-Bar charts comparing customer groups by value and engagement.

🧰 Tools & Libraries

-Python 3

-Pandas – data manipulation

-NumPy – numerical computation

-Matplotlib / Seaborn – visualization

-Scikit-learn – clustering and scaling

💡 Key Insights

-High-value customers (Champions) drive the majority of revenue.

-A significant portion of customers are inactive or hibernating, indicating potential re-engagement opportunities.

-Frequency and Recency patterns show clear potential for personalized marketing.

🎯 Marketing Recommendations

## 💡 Step 7: Marketing Recommendations by Segment
This recommendation contains the segment, description and suggested actions respectively.

-**Champions** | High spenders, frequent, recent buyers | Reward loyalty, VIP offers |
-**Loyal Customers** | Frequent and consistent | Upsell premium products |
-**At Risk** | Long time since last purchase | Send win-back campaigns |
-**Lost Customers** | Inactive for long periods | Offer strong reactivation discounts |
-**New Customers** | Just started buying | Welcome and retention campaigns |


🏁 Conclusion

This project demonstrates how data-driven customer segmentation can support smarter marketing strategies and customer relationship management.
By applying RFM analysis, businesses can identify loyal customers, re-engage inactive ones, and focus marketing resources where they’ll have the highest impact.
