**Customer Segmentation with RFM Analysis**

This project uses the Online Retail Dataset to segment customers based on their purchasing behavior using Recency, Frequency, and Monetary (RFM) analysis. The goal is to help businesses identify high-value customers, re-engage inactive ones, and personalize marketing strategies.

**What I Did**

Using Python, I:

Cleaned and prepared transaction data

Calculated Recency, Frequency, and Monetary values per customer

Scored and grouped customers into segments

Visualized patterns and insights

**Segmentation Method**

**RFM Metrics**

Recency → Days since last purchase

Frequency → Number of transactions

Monetary → Total spend

**Scoring & Segments**
Customers were assigned quantile-based scores (1–5) and grouped into key segments:

Champions

Loyal Customers

At Risk

Hibernating / Lost

New Customers

**Visuals & Insights**

Visuals include:

Segment heatmaps

Bar charts by value and engagement

**Key findings:**

A small segment (Champions) drives most revenue

Many customers are inactive and can be re-engaged

Behavioral patterns support targeted marketing

# Marketing Recommendations by Segment
This recommendation contains the segment, description and suggested actions respectively.

-**Champions** | High spenders, frequent, recent buyers | Reward loyalty, VIP offers |

-**Loyal Customers** | Frequent and consistent | Upsell premium products |

-**At Risk** | Long time since last purchase | Send win-back campaigns |

-**Lost Customers** | Inactive for long periods | Offer strong reactivation discounts |

-**New Customers** | Just started buying | Welcome and retention campaigns |

**Bonus: K-Means Clustering**

K-Means was applied to standardized RFM data to validate segmentation. Using the elbow method, k=5 clusters aligned with the RFM segments.

**Tools**

Python (Pandas, NumPy)

Matplotlib / Seaborn

Scikit-learn

**Conclusion**

RFM analysis delivers actionable customer groups that support smarter retention, reactivation, and growth strategies.
