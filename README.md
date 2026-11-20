# Telco Customer Churn — AIDS PBL Capstone

**Dataset:** IBM Telco Customer Churn  
**Problem:** Predict which customers will churn so retention teams can intervene early.  
**Type:** Supervised binary classification

> Formal academic report is intentionally not included yet.

## Project layout

```
SPSS_Capstone/
├── data/                  # raw + cleaned data + data dictionary
├── figures/               # EDA + evaluation plots
├── models/                # saved sklearn pipelines (.joblib)
├── notebooks/             # exploratory notebook
├── outputs/               # metrics, insights, comparisons
├── src/                   # reusable preprocessing / train / evaluate code
├── run_pipeline.py        # one-command full lifecycle run
└── requirements.txt
```

## Quick start

```bash
pip install -r requirements.txt
python run_pipeline.py
```

Or open `notebooks/telco_churn_ml_pipeline.ipynb` and run all cells.

## ML lifecycle covered

1. Problem definition & KPIs (churn rate, recall, ROC-AUC, retention ROI)
2. Dataset understanding + data dictionary
3. Cleaning (TotalCharges blanks, duplicates, typing)
4. EDA (distributions, segment churn rates, correlations)
5. Feature engineering (tenure groups, add-on count, autopay, avg charges)
6. Models: Logistic Regression, Random Forest, Gradient Boosting
7. Evaluation: stratified split, 5-fold CV ROC-AUC, confusion matrix, classification metrics
8. Business recommendations in `outputs/business_insights.md`

## Stakeholders & KPIs

| Stakeholder | Interest |
|---|---|
| Retention / CRM | Ranked high-risk customers |
| Product / Network | Fiber & service-quality churn drivers |
| Finance | Net value of retention campaigns |

**Primary ML KPI:** ROC-AUC (ranking quality)  
**Operational KPI:** Recall on churners (catch at-risk customers)  
**Business KPI:** Estimated net annual retention value
