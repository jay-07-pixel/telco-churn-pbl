# Business Insights & Recommendations

## Problem
Predict which telecom customers are likely to churn so retention teams can act early.

## Key Data Insights
- Overall churn rate: **26.5%**
- Highest-risk contract: Month-to-month (~42.7%)
- Fiber optic internet has elevated churn (~41.9%)
- Electronic check payers churn more (~45.3%)
- New customers (0-12 months) churn most (~47.4%)

## Model Performance (hold-out test)
- Accuracy: 0.807
- Precision: 0.677
- Recall: 0.521
- F1: 0.589
- ROC-AUC: 0.843

## Retention Campaign Sketch (test set)
- Flagged customers: 288
- True churners caught: 195
- Est. customers saved: 68.2
- Est. annual revenue retained: $53,040
- Campaign cost: $7,200
- Est. net annual value: $45,840

## Actionable Recommendations
1. Prioritize retention offers for month-to-month customers in first 12 months.
2. Investigate Fiber optic service quality / pricing friction (high churn segment).
3. Push autopay / card / bank transfer onboarding to reduce electronic-check risk.
4. Bundle security + support add-ons; higher AddonCount correlates with lower churn.
5. Use model scores weekly to feed a ranked outreach list to the CRM team.

## Top Drivers
- Contract_Month-to-month: 0.3645
- tenure: 0.1399
- InternetService_Fiber optic: 0.0833
- TotalCharges: 0.0796
- OnlineSecurity_No: 0.0614
- AvgChargesPerMonth: 0.0536
- MonthlyCharges: 0.0525
- TechSupport_No: 0.0474
- PaymentMethod_Electronic check: 0.0395
- MultipleLines_No: 0.0109