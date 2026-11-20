"""Generate formal PBL Word report (Times New Roman) with embedded figures."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor, Cm

ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "figures"
OUTPUT = ROOT / "reports" / "Telco_Customer_Churn_PBL_Report.docx"


def set_run_font(run, size=12, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)


def add_para(doc, text, size=12, bold=False, italic=False, align="justify", space_after=8, space_before=0, first_line=True):
    p = doc.add_paragraph()
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if first_line and align == "justify":
        pf.first_line_indent = Cm(0.75)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def add_heading_styled(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        set_run_font(run, size=16 if level == 1 else 14 if level == 2 else 12, bold=True)
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(8)
    return h


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text)
    set_run_font(run, size=11, italic=True)


def add_image(doc, path: Path, width=5.8):
    if not path.exists():
        add_para(doc, f"[Missing figure: {path.name}]", italic=True, align="center", first_line=False)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Inches(width))


def set_cell_shading(cell, hex_color="D9E2F3"):
    tc = cell._tePr if hasattr(cell, "_tePr") else cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def style_table(table):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(2)
                for run in p.runs:
                    set_run_font(run, size=11, bold=(i == 0))
            if i == 0:
                set_cell_shading(cell, "D9E2F3")


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for j, h in enumerate(headers):
        table.rows[0].cells[j].text = h
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            table.rows[i + 1].cells[j].text = str(val)
    style_table(table)
    doc.add_paragraph()
    return table


def set_default_style(doc):
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for i in range(1, 4):
        hs = doc.styles[f"Heading {i}"]
        hs.font.name = "Times New Roman"
        hs.font.color.rgb = RGBColor(0, 0, 0)
        hs._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")


def add_page_number(doc):
    section = doc.sections[0]
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Page ")
    set_run_font(run, size=10)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run2 = p.add_run()
    run2._r.append(fld1)
    run2._r.append(instr)
    run2._r.append(fld2)
    set_run_font(run2, size=10)


def build():
    (ROOT / "reports").mkdir(exist_ok=True)
    doc = Document()
    set_default_style(doc)

    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)
    add_page_number(doc)

    # ===== COVER =====
    for _ in range(3):
        doc.add_paragraph()
    add_para(doc, "PROBLEM-BASED LEARNING (PBL) PROJECT REPORT", size=18, bold=True, align="center", first_line=False, space_after=6)
    add_para(doc, "AIDS Department", size=14, bold=True, align="center", first_line=False, space_after=18)
    add_para(doc, "Customer Churn Prediction for a Telecom Service Provider", size=16, bold=True, align="center", first_line=False, space_after=8)
    add_para(doc, "Using Machine Learning on the IBM Telco Customer Churn Dataset", size=13, italic=True, align="center", first_line=False, space_after=28)
    add_para(doc, "Course: Artificial Intelligence and Data Science (AIDS)", size=12, align="center", first_line=False)
    add_para(doc, "Dataset Source: IBM Telco Customer Churn (open dataset)", size=12, align="center", first_line=False)
    add_para(doc, "Academic Year: 2025–26", size=12, align="center", first_line=False, space_after=28)
    add_para(doc, "Submitted in partial fulfillment of the PBL evaluation rubrics covering the end-to-end Data Science and Machine Learning lifecycle.", size=12, align="center", first_line=False, space_after=12)
    doc.add_page_break()

    # ===== TOC-like outline =====
    add_heading_styled(doc, "Table of Contents", 1)
    toc_items = [
        "1. Problem Definition and Business Understanding",
        "2. Dataset and Data Understanding",
        "3. Data Preprocessing and Cleaning",
        "4. Exploratory Data Analysis (EDA)",
        "5. Feature Engineering and Selection",
        "6. Model Selection and Implementation",
        "7. Model Evaluation and Validation",
        "8. Business Insights and Recommendations",
        "9. Conclusion",
        "10. References / Project Artifacts",
        "Appendix A: Data Dictionary",
    ]
    for item in toc_items:
        add_para(doc, item, align="left", first_line=False, space_after=4)
    doc.add_page_break()

    # ===== 1 =====
    add_heading_styled(doc, "1. Problem Definition and Business Understanding", 1)

    add_heading_styled(doc, "1.1 Real-World Problem Statement", 2)
    add_para(
        doc,
        "Telecom companies operate in a highly competitive market where acquiring a new customer is typically more expensive than retaining an existing one. "
        "When subscribers discontinue service (customer churn), the organization loses recurring monthly revenue and must spend additional marketing budget to replace the lost base. "
        "The business problem addressed in this project is: Can we accurately identify customers who are likely to churn in the near future so that the retention team can intervene with targeted offers before the customer leaves?",
    )

    add_heading_styled(doc, "1.2 Objectives", 2)
    add_para(doc, "The primary objectives of this project are:", first_line=False)
    objectives = [
        "To analyze customer demographic, service, billing, and contract attributes associated with churn.",
        "To clean and prepare a real-world telecom dataset for supervised learning.",
        "To engineer informative features without introducing target leakage.",
        "To train and compare multiple machine learning classifiers for churn prediction.",
        "To evaluate models using appropriate classification and ranking metrics.",
        "To translate analytical findings into actionable retention recommendations and an estimated campaign value.",
    ]
    for i, o in enumerate(objectives, 1):
        add_para(doc, f"{i}. {o}", align="left", first_line=False, space_after=4)

    add_heading_styled(doc, "1.3 Stakeholders", 2)
    add_table(
        doc,
        ["Stakeholder", "Interest / Use of the Solution"],
        [
            ["Retention / CRM Team", "Receive a ranked list of high-risk customers for proactive outreach"],
            ["Product / Network Team", "Identify service segments (e.g., Fiber optic) with elevated churn"],
            ["Finance / Revenue Team", "Estimate ROI of retention campaigns versus do-nothing baseline"],
            ["Customer Experience Team", "Address payment friction and onboarding issues for new customers"],
            ["Data Science Team", "Maintain an auditable ML pipeline with measurable KPIs"],
        ],
    )

    add_heading_styled(doc, "1.4 Business Relevance and KPIs", 2)
    add_para(
        doc,
        "Churn reduction directly protects Annual Recurring Revenue (ARR). Even a modest improvement in retention among high-risk segments can produce meaningful net value after campaign costs. "
        "The project therefore tracks both analytical and business KPIs.",
    )
    add_table(
        doc,
        ["KPI Type", "Metric", "Why it Matters"],
        [
            ["Business", "Overall churn rate", "Baseline health of the subscriber base (26.5% in this dataset)"],
            ["ML Ranking", "ROC-AUC", "Measures ability to rank churners above non-churners"],
            ["Operational", "Recall (Churn class)", "Proportion of actual churners successfully flagged"],
            ["Operational", "Precision (Churn class)", "Avoids wasting retention budget on false alarms"],
            ["Business", "Estimated net annual retention value", "Revenue retained minus campaign cost"],
        ],
    )

    # ===== 2 =====
    add_heading_styled(doc, "2. Dataset and Data Understanding", 1)

    add_heading_styled(doc, "2.1 Dataset Selection and Relevance", 2)
    add_para(
        doc,
        "The IBM Telco Customer Churn dataset was selected because it closely mirrors operational telecom CRM data: demographics, service subscriptions, contract terms, payment methods, and billing amounts, with a clear binary churn label. "
        "It is publicly available, widely used for educational ML projects, and directly aligned with the business problem of subscription retention. "
        "The dataset contains 7,043 customer records and 21 raw attributes.",
    )
    add_table(
        doc,
        ["Property", "Value"],
        [
            ["Dataset name", "IBM Telco Customer Churn"],
            ["Rows", "7,043"],
            ["Raw columns", "21"],
            ["Target variable", "Churn (Yes / No → 1 / 0)"],
            ["Problem type", "Supervised binary classification"],
            ["Class balance", "No Churn: 5,174 (73.5%); Churn: 1,869 (26.5%)"],
        ],
    )

    add_heading_styled(doc, "2.2 Feature Understanding and Data Types", 2)
    add_para(
        doc,
        "Features include categorical service flags (for example OnlineSecurity, TechSupport, Contract, PaymentMethod), binary indicators (SeniorCitizen), and continuous billing variables (tenure, MonthlyCharges, TotalCharges). "
        "The identifier customerID uniquely labels each subscriber and must not be used as a predictive feature. "
        "A complete data dictionary is provided in Appendix A.",
    )

    add_heading_styled(doc, "2.3 Data Quality Overview", 2)
    add_para(
        doc,
        "Initial profiling showed no conventional NaN missing values in most columns. However, TotalCharges was stored as text and contained 11 blank strings corresponding to brand-new customers with tenure = 0. "
        "No duplicate rows were found. The class distribution is moderately imbalanced, which influenced later choices such as class_weight='balanced' for some models and the use of ROC-AUC as a primary ranking metric.",
    )
    add_table(
        doc,
        ["Quality Check", "Result"],
        [
            ["Duplicate rows", "0"],
            ["Blank TotalCharges values fixed", "11"],
            ["Missing values after cleaning", "None"],
            ["Target imbalance", "Churn ≈ 26.5%"],
        ],
    )

    # ===== 3 =====
    add_heading_styled(doc, "3. Data Preprocessing and Cleaning", 1)
    add_para(
        doc,
        "Preprocessing was implemented as a reusable Python module and wrapped inside scikit-learn Pipelines so that train and test folds receive identical transformations without leakage.",
    )

    add_heading_styled(doc, "3.1 Missing Values and Type Correction", 2)
    add_para(
        doc,
        "TotalCharges was converted to numeric using coercion. Blank values were imputed as 0.0 because they correspond to customers with zero tenure who have not yet accumulated charges. "
        "This is domain-consistent imputation rather than mean/median substitution.",
    )

    add_heading_styled(doc, "3.2 Duplicates", 2)
    add_para(
        doc,
        "Exact duplicate detection was applied. No duplicate customer rows were present in the raw file, so no rows were removed for duplication.",
    )

    add_heading_styled(doc, "3.3 Outlier Analysis", 2)
    add_para(
        doc,
        "Outliers for tenure, MonthlyCharges, TotalCharges, and AvgChargesPerMonth were assessed using the IQR rule (1.5 × IQR). "
        "No points fell outside the computed fences for these fields; therefore no aggressive outlier removal was performed. "
        "Boxplots were retained for visual confirmation.",
    )
    add_image(doc, FIGURES / "08_boxplots_outliers.png", width=5.9)
    add_caption(doc, "Figure 1. Boxplots of key numeric variables by churn status (outlier inspection).")

    add_heading_styled(doc, "3.4 Encoding, Scaling, and Transformations", 2)
    add_para(
        doc,
        "Categorical variables were one-hot encoded with handle_unknown='ignore' to support unseen categories at inference time. "
        "Numeric features were median-imputed (defensive) and standardized with StandardScaler. "
        "The binary target was mapped as Yes → 1 and No → 0. "
        "customerID was dropped prior to modeling to prevent identifier leakage.",
    )
    add_table(
        doc,
        ["Step", "Technique", "Justification"],
        [
            ["Missing TotalCharges", "Coerce + fill 0", "Matches tenure=0 business reality"],
            ["Categorical encoding", "One-Hot Encoding", "Nominal categories; no false ordinality"],
            ["Numeric scaling", "StandardScaler", "Improves LR convergence; harmless for trees"],
            ["ID handling", "Drop customerID", "Prevents leakage / memorization"],
            ["Imbalance handling", "class_weight / ranking metrics", "Churn is minority class (~26.5%)"],
        ],
    )

    # ===== 4 =====
    add_heading_styled(doc, "4. Exploratory Data Analysis (EDA)", 1)
    add_para(
        doc,
        "EDA combined descriptive statistics with visualizations to uncover patterns that later guided feature engineering and business recommendations.",
    )

    add_heading_styled(doc, "4.1 Target Distribution", 2)
    add_para(
        doc,
        "Approximately 26.5% of customers churned. This imbalance is material but not extreme; models must still prioritize recall on the churn class for operational usefulness.",
    )
    add_image(doc, FIGURES / "01_churn_distribution.png", width=5.0)
    add_caption(doc, "Figure 2. Distribution of churn vs non-churn customers.")

    add_heading_styled(doc, "4.2 Numeric Patterns by Churn", 2)
    add_para(
        doc,
        "Density plots show that churners tend to have shorter tenure and somewhat higher monthly charges. TotalCharges is typically lower for churners because they leave before accumulating long-term billing history. "
        "Mean tenure is about 32.4 months; mean MonthlyCharges is about $64.76.",
    )
    add_image(doc, FIGURES / "02_numeric_by_churn.png", width=5.9)
    add_caption(doc, "Figure 3. Distributions of tenure, MonthlyCharges, and TotalCharges by churn.")

    add_heading_styled(doc, "4.3 Segment-Level Churn Rates", 2)
    add_para(
        doc,
        "Contract type is a dominant business signal: month-to-month customers churn at about 42.7%, versus 11.3% for one-year and only 2.8% for two-year contracts. "
        "Fiber optic internet users churn at about 41.9%, much higher than DSL (19.0%) or no internet (7.4%). "
        "Electronic check payers churn at about 45.3%, substantially above automatic payment methods.",
    )
    add_image(doc, FIGURES / "03_churn_by_contract.png", width=5.2)
    add_caption(doc, "Figure 4. Churn rate by contract type.")
    add_image(doc, FIGURES / "04_churn_by_internet.png", width=5.2)
    add_caption(doc, "Figure 5. Churn rate by internet service.")
    add_image(doc, FIGURES / "05_churn_by_payment.png", width=5.4)
    add_caption(doc, "Figure 6. Churn rate by payment method.")

    add_heading_styled(doc, "4.4 Tenure Risk Window", 2)
    add_para(
        doc,
        "Customers in the first 12 months show the highest churn rate (~47.4%). Risk declines steadily with tenure, falling to about 9.5% for customers with 49–72 months of relationship. "
        "This identifies early tenure as a critical retention window.",
    )
    add_image(doc, FIGURES / "07_churn_by_tenure_group.png", width=5.2)
    add_caption(doc, "Figure 7. Churn rate by tenure group.")

    add_heading_styled(doc, "4.5 Correlations and Statistical Insight", 2)
    add_para(
        doc,
        "Among numeric/engineered features, tenure shows the strongest negative correlation with churn (≈ −0.35), followed by autopay status and TotalCharges. "
        "MonthlyCharges and average charges per month are positively associated with churn. "
        "These relationships support both tree-based models and linear classifiers with one-hot encoded contract/service terms.",
    )
    add_image(doc, FIGURES / "06_correlation_heatmap.png", width=5.4)
    add_caption(doc, "Figure 8. Correlation heatmap of numeric and engineered features with churn.")

    # ===== 5 =====
    add_heading_styled(doc, "5. Feature Engineering and Selection", 1)

    add_heading_styled(doc, "5.1 Engineered Features", 2)
    add_para(
        doc,
        "Domain-driven features were created only from information that would be known before churn occurs, avoiding leakage from the target or from post-churn outcomes.",
    )
    add_table(
        doc,
        ["Feature", "Definition", "Rationale"],
        [
            ["AvgChargesPerMonth", "TotalCharges / tenure (or MonthlyCharges if tenure=0)", "Captures effective spend intensity"],
            ["TenureGroup", "Bins: 0–12, 13–24, 25–48, 49–72", "Models non-linear early-tenure risk"],
            ["HasStreamingBundle", "Both StreamingTV and StreamingMovies = Yes", "Proxy for entertainment engagement"],
            ["AddonCount", "Count of security/support add-ons", "Protection services often reduce churn"],
            ["IsAutoPay", "Bank transfer or credit card automatic", "Lower friction / sticky billing"],
        ],
    )

    add_heading_styled(doc, "5.2 Feature Selection and Leakage Control", 2)
    add_para(
        doc,
        "customerID was excluded from all model inputs. The target label was never used to construct predictors. "
        "Feature usefulness was further assessed via model-based importance from the best Gradient Boosting model. "
        "The strongest drivers were Contract_Month-to-month, tenure, InternetService_Fiber optic, TotalCharges, and lack of OnlineSecurity — consistent with EDA. "
        "This agreement between exploratory analysis and model importance increases confidence that the model is learning genuine business structure rather than noise.",
    )
    add_image(doc, FIGURES / "09_feature_importance.png", width=5.5)
    add_caption(doc, "Figure 9. Top feature importances from the best Gradient Boosting model.")

    # ===== 6 =====
    add_heading_styled(doc, "6. Model Selection and Implementation", 1)

    add_heading_styled(doc, "6.1 Methodology", 2)
    add_para(
        doc,
        "A stratified 80/20 train–test split preserved class proportions. Within the training set, 5-fold stratified cross-validation on ROC-AUC was used to compare algorithms fairly. "
        "All preprocessing steps were placed inside a Pipeline with the estimator to prevent information leakage from scalers/encoders into validation folds.",
    )

    add_heading_styled(doc, "6.2 Algorithms and Justification", 2)
    add_table(
        doc,
        ["Algorithm", "Why Selected"],
        [
            ["Logistic Regression", "Strong, interpretable linear baseline; coefficients aid explanation; class_weight='balanced'"],
            ["Random Forest", "Handles non-linear interactions and mixed feature types; robust to scaling"],
            ["Gradient Boosting", "Often strongest tabular classifier; sequential residual fitting improves ranking quality"],
        ],
    )
    add_para(
        doc,
        "These three algorithms represent a principled progression from interpretable linear models to bagged and boosted ensembles, which is appropriate for a structured tabular churn problem.",
    )

    add_heading_styled(doc, "6.3 Implementation Summary", 2)
    add_para(
        doc,
        "Implementation used Python with pandas, scikit-learn, matplotlib, and seaborn. "
        "Reusable modules under src/ handle preprocessing, training, and evaluation. "
        "The full lifecycle can be reproduced with python run_pipeline.py. "
        "Trained pipelines were serialized to models/*.joblib for reuse.",
    )

    # ===== 7 =====
    add_heading_styled(doc, "7. Model Evaluation and Validation", 1)

    add_heading_styled(doc, "7.1 Metrics and Validation Strategy", 2)
    add_para(
        doc,
        "Because churn is a minority class and ranking quality matters for CRM prioritization, ROC-AUC was used as the primary model-selection metric. "
        "Accuracy, precision, recall, and F1 on the hold-out test set were reported for operational interpretation. "
        "Confusion matrices show true positives (caught churners), false negatives (missed churners), and false positives (unnecessary outreach).",
    )

    add_heading_styled(doc, "7.2 Comparative Results", 2)
    add_table(
        doc,
        ["Model", "CV ROC-AUC", "Test ROC-AUC", "Accuracy", "Precision", "Recall", "F1"],
        [
            ["Logistic Regression", "0.846", "0.842", "0.738", "0.504", "0.789", "0.615"],
            ["Random Forest", "0.846", "0.841", "0.757", "0.529", "0.783", "0.631"],
            ["Gradient Boosting", "0.846", "0.843", "0.807", "0.677", "0.521", "0.589"],
        ],
    )
    add_para(
        doc,
        "Gradient Boosting achieved the best cross-validated and test ROC-AUC and the highest overall accuracy/precision. "
        "Logistic Regression and Random Forest delivered higher recall, which can be preferable if the business prioritizes catching as many churners as possible. "
        "For this report, Gradient Boosting is selected as the best overall ranking model (CV ROC-AUC ≈ 0.846; test ROC-AUC ≈ 0.843).",
    )
    add_image(doc, FIGURES / "10_model_comparison_auc.png", width=5.2)
    add_caption(doc, "Figure 10. Test ROC-AUC comparison across models.")

    add_heading_styled(doc, "7.3 Confusion Matrices and ROC Curves", 2)
    add_para(
        doc,
        "For Gradient Boosting on the test set (1,409 customers), the confusion matrix is [[942, 93], [179, 195]]: "
        "942 true negatives, 93 false positives, 179 false negatives, and 195 true positives. "
        "This corresponds to precision ≈ 0.677 and recall ≈ 0.521 for the churn class.",
    )
    add_image(doc, FIGURES / "cm_gradient_boosting.png", width=4.2)
    add_caption(doc, "Figure 11. Confusion matrix — Gradient Boosting (best model).")
    add_image(doc, FIGURES / "roc_gradient_boosting.png", width=4.4)
    add_caption(doc, "Figure 12. ROC curve — Gradient Boosting.")

    add_para(doc, "Additional model diagnostics for completeness:", first_line=False)
    add_image(doc, FIGURES / "cm_logistic_regression.png", width=4.0)
    add_caption(doc, "Figure 13. Confusion matrix — Logistic Regression.")
    add_image(doc, FIGURES / "cm_random_forest.png", width=4.0)
    add_caption(doc, "Figure 14. Confusion matrix — Random Forest.")
    add_image(doc, FIGURES / "roc_logistic_regression.png", width=4.2)
    add_caption(doc, "Figure 15. ROC curve — Logistic Regression.")
    add_image(doc, FIGURES / "roc_random_forest.png", width=4.2)
    add_caption(doc, "Figure 16. ROC curve — Random Forest.")

    add_heading_styled(doc, "7.4 Interpretation", 2)
    add_para(
        doc,
        "All three models achieve ROC-AUC above 0.84, indicating strong discriminative ability. "
        "The chosen Gradient Boosting model is more conservative (higher precision, lower recall), which reduces wasted retention spend. "
        "If leadership prefers maximizing coverage of churners, the operating threshold can be lowered or the Random Forest / Logistic Regression models can be used for outreach ranking. "
        "This threshold flexibility is an important practical advantage of probabilistic classifiers.",
    )

    # ===== 8 =====
    add_heading_styled(doc, "8. Business Insights and Recommendations", 1)

    add_heading_styled(doc, "8.1 Key Analytical Insights", 2)
    insights = [
        "Overall churn rate is 26.5%, indicating a material retention challenge.",
        "Month-to-month contracts are the highest-risk segment (~42.7% churn).",
        "Fiber optic subscribers churn at ~41.9%, suggesting service quality or price-value issues.",
        "Electronic check payment is associated with ~45.3% churn — far above autopay methods.",
        "Customers in months 0–12 are the most fragile cohort (~47.4% churn).",
        "Model importances align with EDA: contract, tenure, fiber, security add-ons, and payment method dominate.",
    ]
    for i, t in enumerate(insights, 1):
        add_para(doc, f"{i}. {t}", align="left", first_line=False, space_after=4)

    add_heading_styled(doc, "8.2 Retention Campaign Value Sketch", 2)
    add_para(
        doc,
        "Using the Gradient Boosting scores on the hold-out set with a 0.5 probability threshold, 288 customers were flagged. "
        "Of these, 195 were true churners. Assuming a $25 retention offer cost, 35% offer success rate, and average monthly revenue equal to the dataset mean (~$64.76), "
        "the simplified annualized estimate is approximately $53,040 revenue retained against $7,200 campaign cost, for a net value near $45,840 on the test slice alone. "
        "These figures are illustrative assumptions for decision support, not audited financial forecasts.",
    )
    add_table(
        doc,
        ["Campaign Metric (Test Set)", "Value"],
        [
            ["Customers flagged", "288"],
            ["True churners caught", "195"],
            ["False alarms", "93"],
            ["Est. customers saved (35% success)", "68.3"],
            ["Est. annual revenue retained", "$53,040"],
            ["Campaign cost", "$7,200"],
            ["Est. net annual value", "$45,840"],
        ],
    )

    add_heading_styled(doc, "8.3 Actionable Recommendations", 2)
    recs = [
        "Prioritize retention offers for month-to-month customers within their first 12 months.",
        "Investigate Fiber optic dissatisfaction drivers (speed reliability, pricing, competitor offers) and create a dedicated save desk for that segment.",
        "Migrate electronic-check users to autopay (credit card / bank transfer) during onboarding and billing reminders.",
        "Promote security and tech-support add-on bundles; customers with more protection services show lower churn association.",
        "Operationalize weekly model scoring in CRM: push a ranked high-risk list to agents with scripted offers.",
        "Tune the decision threshold with business owners — lower threshold for higher recall campaigns, higher threshold for cost-efficient campaigns.",
    ]
    for i, r in enumerate(recs, 1):
        add_para(doc, f"{i}. {r}", align="left", first_line=False, space_after=4)

    # ===== 9 =====
    add_heading_styled(doc, "9. Conclusion", 1)
    add_para(
        doc,
        "This PBL project completed the full data science and machine learning lifecycle required by the AIDS evaluation rubrics: problem framing, data understanding, cleaning, EDA, feature engineering, multi-model implementation, rigorous validation, and business-facing recommendations. "
        "The best-performing model, Gradient Boosting, achieved a test ROC-AUC of approximately 0.843 and provides actionable churn risk scores. "
        "The strongest business levers identified are contract structure, early-tenure care, Fiber optic experience, payment method migration, and protection add-on attachment. "
        "Future work may include cost-sensitive threshold optimization, survival modeling for time-to-churn, and a lightweight deployment API for CRM integration.",
    )

    # ===== 10 =====
    add_heading_styled(doc, "10. References / Project Artifacts", 1)
    refs = [
        "IBM Telco Customer Churn Dataset — https://github.com/IBM/telco-customer-churn-on-icp4d",
        "Pedregosa et al., Scikit-learn: Machine Learning in Python, JMLR, 2011.",
        "Project code modules: src/preprocess.py, src/train.py, src/evaluate.py",
        "Reproducible runner: run_pipeline.py",
        "Interactive notebook: notebooks/telco_churn_ml_pipeline.ipynb",
        "Saved models: models/best_model.joblib (and individual algorithm pipelines)",
        "Metrics and insights: outputs/model_comparison.json, outputs/business_insights.md",
    ]
    for r in refs:
        add_para(doc, f"• {r}", align="left", first_line=False, space_after=4)

    # ===== Appendix =====
    doc.add_page_break()
    add_heading_styled(doc, "Appendix A: Data Dictionary", 1)
    add_para(
        doc,
        "The following dictionary describes raw and engineered fields used in the project.",
        first_line=False,
    )
    add_table(
        doc,
        ["Column", "Type", "Description"],
        [
            ["customerID", "ID", "Unique customer identifier (dropped before modeling)"],
            ["gender", "categorical", "Customer gender"],
            ["SeniorCitizen", "binary", "1 if senior citizen, else 0"],
            ["Partner", "categorical", "Whether the customer has a partner"],
            ["Dependents", "categorical", "Whether the customer has dependents"],
            ["tenure", "numeric", "Number of months with the company"],
            ["PhoneService", "categorical", "Has phone service"],
            ["MultipleLines", "categorical", "Multiple phone lines status"],
            ["InternetService", "categorical", "DSL / Fiber optic / No"],
            ["OnlineSecurity", "categorical", "Online security add-on"],
            ["OnlineBackup", "categorical", "Online backup add-on"],
            ["DeviceProtection", "categorical", "Device protection add-on"],
            ["TechSupport", "categorical", "Tech support add-on"],
            ["StreamingTV", "categorical", "Streaming TV add-on"],
            ["StreamingMovies", "categorical", "Streaming movies add-on"],
            ["Contract", "categorical", "Month-to-month / One year / Two year"],
            ["PaperlessBilling", "categorical", "Paperless billing flag"],
            ["PaymentMethod", "categorical", "Customer payment method"],
            ["MonthlyCharges", "numeric", "Current monthly bill amount"],
            ["TotalCharges", "numeric", "Total amount charged to date"],
            ["Churn", "target", "1 = churned, 0 = retained"],
            ["AvgChargesPerMonth", "engineered", "TotalCharges / tenure"],
            ["TenureGroup", "engineered", "Binned tenure groups"],
            ["HasStreamingBundle", "engineered", "Both streaming TV and movies"],
            ["AddonCount", "engineered", "Count of security/support add-ons"],
            ["IsAutoPay", "engineered", "Automatic payment method flag"],
        ],
    )

    add_para(
        doc,
        "— End of Report —",
        align="center",
        bold=True,
        first_line=False,
        space_before=18,
    )

    doc.save(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    build()
