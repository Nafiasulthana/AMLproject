import os
import sys
import json
from datetime import datetime
import numpy as np
import pandas as pd
import xgboost as xgboost
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix, classification_report,
    brier_score_loss, log_loss, roc_curve, precision_recall_curve
)
from sklearn.preprocessing import StandardScaler

# Optional imports for model comparison & imbalance handling
try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False

try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    import catboost as cb
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

# Ensure root and database directories are on sys.path
file_dir = os.path.dirname(__file__)
database_dir = os.path.abspath(os.path.join(file_dir, ".."))
root_dir = os.path.abspath(os.path.join(database_dir, ".."))
if database_dir not in sys.path:
    sys.path.insert(0, database_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ml.synthetic_generator import generate_synthetic_aml_dataset

RANDOM_SEED = 42

RAW_FEATURE_COLS = [
    "amount", "z_score_amount", "degree_centrality", "betweenness_centrality",
    "money_retention_ratio", "hop_count"
]

ALL_RAW_COLS = [
    "amount", "z_score_amount", "degree_centrality", "betweenness_centrality",
    "money_retention_ratio", "hop_count", "structuring_flag", "layering_flag",
    "round_trip_flag", "dormant_flag", "smurfing_flag"
]

ENGINEERED_FEATURE_COLS = [
    "amount", "z_score_amount", "degree_centrality", "betweenness_centrality",
    "money_retention_ratio", "hop_count", "structuring_flag", "layering_flag",
    "round_trip_flag", "dormant_flag", "smurfing_flag", "high_risk_flag_count",
    "risk_flag_any", "z_score_retention_ratio", "unretained_amount",
    "graph_activity_score", "velocity_pass_through"
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Applies domain-specific feature engineering to raw AML transaction records."""
    df_feat = df.copy()
    
    flag_cols = ["structuring_flag", "layering_flag", "round_trip_flag", "dormant_flag", "smurfing_flag"]
    for c in flag_cols:
        if c not in df_feat.columns:
            df_feat[c] = 0
            
    df_feat["high_risk_flag_count"] = df_feat[flag_cols].sum(axis=1)
    df_feat["risk_flag_any"] = (df_feat["high_risk_flag_count"] > 0).astype(int)
    
    # 1. Ratio of z_score to retention ratio (high z-score + low retention ratio = rapid layering)
    df_feat["z_score_retention_ratio"] = df_feat["z_score_amount"] / (df_feat["money_retention_ratio"] + 0.01)
    
    # 2. Unretained dollar amount passed through account
    df_feat["unretained_amount"] = df_feat["amount"] * (1.0 - df_feat["money_retention_ratio"])
    
    # 3. Graph activity interaction score (degree centrality * betweenness centrality)
    df_feat["graph_activity_score"] = df_feat["degree_centrality"] * df_feat["betweenness_centrality"]
    
    # 4. Multihop pass-through velocity score
    df_feat["velocity_pass_through"] = (df_feat["betweenness_centrality"] * df_feat["z_score_amount"]) / (df_feat["hop_count"] + 1.0)
    
    return df_feat


def inspect_dataset(df: pd.DataFrame):
    """TASK 1: Pipeline Inspection & Diagnostics"""
    print("\n=======================================================")
    print("      TASK 1: AML DATASET & PIPELINE INSPECTION        ")
    print("=======================================================")
    print(f"  Total Dataset Records : {len(df)}")
    print(f"  Total Raw Columns     : {len(df.columns)}")
    print(f"  Target Column Name    : 'is_aml_suspicious'")
    
    class_dist = df["is_aml_suspicious"].value_counts().to_dict()
    normal_cnt = class_dist.get(0, 0)
    susp_cnt = class_dist.get(1, 0)
    print(f"  Class Distribution    : Normal(0) = {normal_cnt} ({normal_cnt/len(df)*100:.1f}%), Suspicious(1) = {susp_cnt} ({susp_cnt/len(df)*100:.1f}%)")
    print(f"  Imbalance Ratio       : 1:{normal_cnt/max(susp_cnt, 1):.2f}")
    print(f"  Missing Values Count  : {df.isnull().sum().sum()}")
    print(f"  Duplicate Rows Count  : {df.duplicated().sum()}")
    print("=======================================================\n")


def tune_xgboost_hyperparameters(X_train: pd.DataFrame, y_train: pd.Series, base_scale_pos_weight: float) -> tuple:
    """TASK 4: Hyperparameter Optimization using 5-Fold Stratified CV optimizing F1 & PR-AUC."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    param_grid = [
        {
            "n_estimators": n,
            "max_depth": d,
            "learning_rate": lr,
            "min_child_weight": mcw,
            "subsample": sub,
            "colsample_bytree": col,
            "reg_alpha": alpha,
            "reg_lambda": reg_lam,
            "scale_pos_weight": spw
        }
        for n in (80, 120, 160)
        for d in (3, 4, 5)
        for lr in (0.03, 0.05, 0.1)
        for mcw in (2, 3, 5)
        for sub in (0.8,)
        for col in (0.8,)
        for alpha in (0.0, 0.1, 1.0)
        for reg_lam in (0.5, 1.0)
        for spw in (base_scale_pos_weight, base_scale_pos_weight * 1.25)
    ]
    
    print(f"Searching {len(param_grid)} hyperparameter combinations via 5-Fold Stratified CV...")
    
    best_params = None
    best_f1 = -1.0
    best_cv_metrics = None
    
    scoring = {"f1": "f1", "roc_auc": "roc_auc", "precision": "precision", "recall": "recall", "pr_auc": "average_precision"}
    
    # Efficient evaluation of grid
    for params in param_grid:
        model = XGBClassifier(
            **params,
            random_state=RANDOM_SEED,
            eval_metric="logloss"
        )
        cv_res = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
        mean_f1 = float(np.mean(cv_res["test_f1"]))
        mean_pr_auc = float(np.mean(cv_res["test_pr_auc"]))
        
        # Optimize combined score (F1 primary)
        score = 0.7 * mean_f1 + 0.3 * mean_pr_auc
        
        if score > best_f1:
            best_f1 = score
            best_params = params
            best_cv_metrics = {
                metric: {
                    "mean": round(float(np.mean(cv_res[f"test_{metric}"])), 4),
                    "std": round(float(np.std(cv_res[f"test_{metric}"])), 4)
                }
                for metric in scoring
            }
            
    print(f"Winning Hyperparameters: {best_params}")
    return best_params, best_cv_metrics


def optimize_classification_threshold(model, X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """TASK 5: Out-of-fold probability threshold tuning across candidate values [0.15 .. 0.50]."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    oof_probs = cross_val_predict(model, X_train, y_train, cv=cv, method="predict_proba")[:, 1]
    
    thresholds = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    threshold_results = []
    
    best_t = 0.50
    best_score = -1.0
    
    for t in thresholds:
        y_pred = (oof_probs >= t).astype(int)
        acc = accuracy_score(y_train, y_pred)
        prec = precision_score(y_train, y_pred, zero_division=0)
        rec = recall_score(y_train, y_pred, zero_division=0)
        f1 = f1_score(y_train, y_pred, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y_train, y_pred).ravel()
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        res = {
            "threshold": t,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "specificity": round(spec, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
        }
        threshold_results.append(res)
        
        # AML objective: heavily prioritize Suspicious Recall & F1 to eliminate False Negatives (FN)
        # Score formula: Recall * 0.6 + F1 * 0.4 - FPR penalty above 0.30
        score = (rec * 0.6) + (f1 * 0.4) - (max(0, fpr - 0.30) * 0.5)
        if score > best_score:
            best_score = score
            best_t = t
            
    print(f"Optimal Classification Threshold Selected: {best_t:.2f}")
    return {"optimal_threshold": best_t, "threshold_grid": threshold_results}


def generate_and_save_visualizations(
    fig_dir: str,
    y_test: np.ndarray,
    y_prob: np.ndarray,
    y_pred_opt: np.ndarray,
    feature_names: list,
    feature_importances: np.ndarray,
    threshold_grid: list,
    optimal_threshold: float
):
    """TASK 11: Update Visualizations (7 high-res plots)."""
    os.makedirs(fig_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
    
    # 1. Confusion Matrix
    plt.figure(figsize=(6, 5), dpi=300)
    cm = confusion_matrix(y_test, y_pred_opt)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Normal (0)", "Suspicious (1)"],
                yticklabels=["Normal (0)", "Suspicious (1)"])
    plt.title(f"Optimized XGBoost Confusion Matrix (Threshold={optimal_threshold:.2f})", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted Class")
    plt.ylabel("Actual Class")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "confusion_matrix.png"))
    plt.close()
    
    # 2. ROC Curve
    plt.figure(figsize=(7, 5), dpi=300)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    auc_val = roc_auc_score(y_test, y_prob)
    plt.plot(fpr, tpr, color="#2563EB", lw=2.5, label=f"XGBoost ROC (AUC = {auc_val:.4f})")
    plt.plot([0, 1], [0, 1], color="gray", linestyle="--", lw=1.5)
    plt.title("Receiver Operating Characteristic (ROC) Curve", fontsize=12, fontweight="bold")
    plt.xlabel("False Positive Rate (1 - Specificity)")
    plt.ylabel("True Positive Rate (Recall)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "roc_curve.png"))
    plt.close()
    
    # 3. Precision-Recall Curve
    plt.figure(figsize=(7, 5), dpi=300)
    prec_vals, rec_vals, _ = precision_recall_curve(y_test, y_prob)
    pr_auc_val = average_precision_score(y_test, y_prob)
    plt.plot(rec_vals, prec_vals, color="#059669", lw=2.5, label=f"XGBoost PR Curve (PR-AUC = {pr_auc_val:.4f})")
    plt.title("Precision-Recall Curve", fontsize=12, fontweight="bold")
    plt.xlabel("Recall (Sensitivity)")
    plt.ylabel("Precision")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "precision_recall_curve.png"))
    plt.close()
    
    # 4. Feature Importance Plot
    plt.figure(figsize=(9, 6), dpi=300)
    sorted_idx = np.argsort(feature_importances)
    plt.barh(np.array(feature_names)[sorted_idx], feature_importances[sorted_idx], color="#4F46E5")
    plt.title("XGBoost Gain-Based Feature Importance", fontsize=12, fontweight="bold")
    plt.xlabel("Relative Importance Score (Gain)")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "feature_importance.png"))
    plt.close()
    
    # Threshold sweep plots
    df_t = pd.DataFrame(threshold_grid)
    
    # 5. Threshold vs Recall
    plt.figure(figsize=(7, 5), dpi=300)
    plt.plot(df_t["threshold"], df_t["recall"], marker="o", color="#DC2626", lw=2.0)
    plt.axvline(optimal_threshold, color="black", linestyle="--", label=f"Selected Threshold ({optimal_threshold:.2f})")
    plt.title("Classification Threshold vs. Suspicious Class Recall", fontsize=12, fontweight="bold")
    plt.xlabel("Decision Threshold")
    plt.ylabel("Recall")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "threshold_vs_recall.png"))
    plt.close()
    
    # 6. Threshold vs Precision
    plt.figure(figsize=(7, 5), dpi=300)
    plt.plot(df_t["threshold"], df_t["precision"], marker="s", color="#2563EB", lw=2.0)
    plt.axvline(optimal_threshold, color="black", linestyle="--", label=f"Selected Threshold ({optimal_threshold:.2f})")
    plt.title("Classification Threshold vs. Suspicious Class Precision", fontsize=12, fontweight="bold")
    plt.xlabel("Decision Threshold")
    plt.ylabel("Precision")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "threshold_vs_precision.png"))
    plt.close()
    
    # 7. Threshold vs F1
    plt.figure(figsize=(7, 5), dpi=300)
    plt.plot(df_t["threshold"], df_t["f1_score"], marker="^", color="#7C3AED", lw=2.0)
    plt.axvline(optimal_threshold, color="black", linestyle="--", label=f"Selected Threshold ({optimal_threshold:.2f})")
    plt.title("Classification Threshold vs. Suspicious Class F1-Score", fontsize=12, fontweight="bold")
    plt.xlabel("Decision Threshold")
    plt.ylabel("F1-Score")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "threshold_vs_f1.png"))
    plt.close()
    
    print(f"Saved 7 visualization figures to: {fig_dir}")


def train_and_save_model(model_dir: str = None, data_dir: str = None, force_rebuild_dataset: bool = False):
    if model_dir is None:
        model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
    if data_dir is None:
        data_dir = os.path.abspath(os.path.join(root_dir, "data"))
        
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    dataset_path = os.path.join(data_dir, "phase1_aml_dataset.csv")

    if os.path.exists(dataset_path) and not force_rebuild_dataset:
        print(f"Loading existing Phase 1 dataset from: {dataset_path}")
        df_raw = pd.read_csv(dataset_path)
    else:
        print(f"Generating Phase 1 synthetic AML dataset (seed={RANDOM_SEED})...")
        df_raw = generate_synthetic_aml_dataset(n_samples=2000, seed=RANDOM_SEED)
        df_raw.to_csv(dataset_path, index=False)

    # TASK 1: Inspection
    inspect_dataset(df_raw)

    # TASK 2: Feature Engineering
    df_engineered = engineer_features(df_raw)
    
    X = df_engineered[ENGINEERED_FEATURE_COLS]
    y = df_engineered["is_aml_suspicious"]

    # Fixed Train/Test split matching original seed 42 (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    base_scale_pos_weight = float((y_train == 0).sum()) / max(float((y_train == 1).sum()), 1.0)
    print(f"Training set class imbalance: {int((y_train==0).sum())} Normal / {int((y_train==1).sum())} Suspicious (scale_pos_weight={base_scale_pos_weight:.4f})")

    # TASK 3: Evaluate Imbalance Handling Strategies (Weighted vs SMOTE)
    imbalance_comp = {}
    if HAS_SMOTE:
        print("\nTesting SMOTE + XGBoost vs Weighted XGBoost on Training Folds...")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
        
        # 1. Weighted XGBoost
        xgb_w = XGBClassifier(scale_pos_weight=base_scale_pos_weight, random_state=RANDOM_SEED, eval_metric="logloss")
        cv_w = cross_validate(xgb_w, X_train, y_train, cv=cv, scoring={"f1": "f1", "recall": "recall", "pr_auc": "average_precision"})
        imbalance_comp["weighted_xgboost"] = {
            "mean_f1": round(float(np.mean(cv_w["test_f1"])), 4),
            "mean_recall": round(float(np.mean(cv_w["test_recall"])), 4),
            "mean_pr_auc": round(float(np.mean(cv_w["test_pr_auc"])), 4)
        }
        
        # 2. SMOTE + XGBoost (SMOTE applied ONLY to train folds)
        smote_f1s, smote_recs, smote_praucs = [], [], []
        for train_idx, val_idx in cv.split(X_train, y_train):
            X_tr_f, y_tr_f = X_train.iloc[train_idx], y_train.iloc[train_idx]
            X_val_f, y_val_f = X_train.iloc[val_idx], y_train.iloc[val_idx]
            
            smote = SMOTE(random_state=RANDOM_SEED)
            X_tr_res, y_tr_res = smote.fit_resample(X_tr_f, y_tr_f)
            
            xgb_smote = XGBClassifier(random_state=RANDOM_SEED, eval_metric="logloss")
            xgb_smote.fit(X_tr_res, y_tr_res)
            
            y_val_prob = xgb_smote.predict_proba(X_val_f)[:, 1]
            y_val_pred = xgb_smote.predict(X_val_f)
            
            smote_f1s.append(f1_score(y_val_f, y_val_pred, zero_division=0))
            smote_recs.append(recall_score(y_val_f, y_val_pred, zero_division=0))
            smote_praucs.append(average_precision_score(y_val_f, y_val_prob))
            
        imbalance_comp["smote_xgboost"] = {
            "mean_f1": round(float(np.mean(smote_f1s)), 4),
            "mean_recall": round(float(np.mean(smote_recs)), 4),
            "mean_pr_auc": round(float(np.mean(smote_praucs)), 4)
        }
        print(f"  Weighted XGBoost CV  : F1={imbalance_comp['weighted_xgboost']['mean_f1']}, Recall={imbalance_comp['weighted_xgboost']['mean_recall']}, PR-AUC={imbalance_comp['weighted_xgboost']['mean_pr_auc']}")
        print(f"  SMOTE + XGBoost CV   : F1={imbalance_comp['smote_xgboost']['mean_f1']}, Recall={imbalance_comp['smote_xgboost']['mean_recall']}, PR-AUC={imbalance_comp['smote_xgboost']['mean_pr_auc']}")

    # TASK 4: Hyperparameter Optimization
    best_params, cv_metrics = tune_xgboost_hyperparameters(X_train, y_train, base_scale_pos_weight)

    # Train final tuned XGBoost model
    model = XGBClassifier(
        **best_params,
        random_state=RANDOM_SEED,
        eval_metric="logloss"
    )
    model.fit(X_train, y_train)

    # TASK 5: Threshold Optimization
    threshold_info = optimize_classification_threshold(model, X_train, y_train)
    optimal_threshold = threshold_info["optimal_threshold"]

    # Train IsolationForest model for unsupervised anomaly layer
    iso_model = IsolationForest(
        n_estimators=200,
        contamination=0.15,
        random_state=RANDOM_SEED
    )
    iso_model.fit(X_train)
    train_dec_scores = iso_model.decision_function(X_train)
    iso_min = float(np.min(train_dec_scores))
    iso_max = float(np.max(train_dec_scores))

    # TASK 6 & 7: Model Evaluation on Held-Out Test Set (Using Optimal Threshold)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred_opt = (y_prob >= optimal_threshold).astype(int)

    acc = accuracy_score(y_test, y_pred_opt)
    prec = precision_score(y_test, y_pred_opt, zero_division=0)
    rec = recall_score(y_test, y_pred_opt, zero_division=0)
    f1 = f1_score(y_test, y_pred_opt, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    brier = brier_score_loss(y_test, y_prob)
    logloss = log_loss(y_test, y_prob)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_opt).ravel()

    # TASK 8: Model Comparisons on Held-Out Test Set
    model_comparisons = {}
    
    # 1. Baseline Logistic Regression (scaled)
    scaler = StandardScaler()
    X_tr_sc = scaler.fit_transform(X_train)
    X_te_sc = scaler.transform(X_test)
    lr = LogisticRegression(class_weight="balanced", random_state=RANDOM_SEED, max_iter=1000)
    lr.fit(X_tr_sc, y_train)
    lr_prob = lr.predict_proba(X_te_sc)[:, 1]
    lr_pred = (lr_prob >= 0.5).astype(int)
    model_comparisons["Logistic Regression"] = {
        "accuracy": round(accuracy_score(y_test, lr_pred), 4),
        "precision": round(precision_score(y_test, lr_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, lr_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, lr_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, lr_prob), 4),
        "pr_auc": round(average_precision_score(y_test, lr_prob), 4)
    }

    # 2. Random Forest
    rf = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=RANDOM_SEED)
    rf.fit(X_train, y_train)
    rf_prob = rf.predict_proba(X_test)[:, 1]
    rf_pred = (rf_prob >= 0.5).astype(int)
    model_comparisons["Random Forest"] = {
        "accuracy": round(accuracy_score(y_test, rf_pred), 4),
        "precision": round(precision_score(y_test, rf_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, rf_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, rf_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, rf_prob), 4),
        "pr_auc": round(average_precision_score(y_test, rf_prob), 4)
    }

    # 3. LightGBM (if installed)
    if HAS_LGBM:
        lgbm = lgb.LGBMClassifier(scale_pos_weight=base_scale_pos_weight, random_state=RANDOM_SEED, verbosity=-1)
        lgbm.fit(X_train, y_train)
        lgb_prob = lgbm.predict_proba(X_test)[:, 1]
        lgb_pred = (lgb_prob >= 0.5).astype(int)
        model_comparisons["LightGBM"] = {
            "accuracy": round(accuracy_score(y_test, lgb_pred), 4),
            "precision": round(precision_score(y_test, lgb_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, lgb_pred, zero_division=0), 4),
            "f1": round(f1_score(y_test, lgb_pred, zero_division=0), 4),
            "roc_auc": round(roc_auc_score(y_test, lgb_prob), 4),
            "pr_auc": round(average_precision_score(y_test, lgb_prob), 4)
        }

    # 4. CatBoost (if installed)
    if HAS_CATBOOST:
        cb_mod = cb.CatBoostClassifier(scale_pos_weight=base_scale_pos_weight, random_seed=RANDOM_SEED, verbose=0)
        cb_mod.fit(X_train, y_train)
        cb_prob = cb_mod.predict_proba(X_test)[:, 1]
        cb_pred = (cb_prob >= 0.5).astype(int)
        model_comparisons["CatBoost"] = {
            "accuracy": round(accuracy_score(y_test, cb_pred), 4),
            "precision": round(precision_score(y_test, cb_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, cb_pred, zero_division=0), 4),
            "f1": round(f1_score(y_test, cb_pred, zero_division=0), 4),
            "roc_auc": round(roc_auc_score(y_test, cb_prob), 4),
            "pr_auc": round(average_precision_score(y_test, cb_prob), 4)
        }

    # 5. Baseline XGBoost (Original 6 Features, default T=0.5)
    X_train_raw = X_train[RAW_FEATURE_COLS]
    X_test_raw = X_test[RAW_FEATURE_COLS]
    xgb_base = XGBClassifier(max_depth=4, learning_rate=0.1, n_estimators=120, scale_pos_weight=base_scale_pos_weight, random_state=RANDOM_SEED, eval_metric="logloss")
    xgb_base.fit(X_train_raw, y_train)
    b_prob = xgb_base.predict_proba(X_test_raw)[:, 1]
    b_pred = (b_prob >= 0.5).astype(int)
    btn, bfp, bfn, btp = confusion_matrix(y_test, b_pred).ravel()
    
    before_metrics = {
        "accuracy": round(accuracy_score(y_test, b_pred), 4),
        "precision": round(precision_score(y_test, b_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, b_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, b_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, b_prob), 4),
        "pr_auc": round(average_precision_score(y_test, b_prob), 4),
        "tn": int(btn), "fp": int(bfp), "fn": int(bfn), "tp": int(btp)
    }

    # 6. Improved XGBoost (17 Features, Tuned Parameters, Optimal Threshold)
    improved_metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "log_loss": round(logloss, 4),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
    }
    
    model_comparisons["Baseline XGBoost (Old)"] = {
        "accuracy": before_metrics["accuracy"], "precision": before_metrics["precision"],
        "recall": before_metrics["recall"], "f1": before_metrics["f1_score"],
        "roc_auc": before_metrics["roc_auc"], "pr_auc": before_metrics["pr_auc"]
    }
    
    model_comparisons["Improved Tuned XGBoost (New)"] = {
        "accuracy": improved_metrics["accuracy"], "precision": improved_metrics["precision"],
        "recall": improved_metrics["recall"], "f1": improved_metrics["f1_score"],
        "roc_auc": improved_metrics["roc_auc"], "pr_auc": improved_metrics["pr_auc"]
    }

    fn_reduction = before_metrics["fn"] - improved_metrics["fn"]
    fp_change = improved_metrics["fp"] - before_metrics["fp"]

    # Feature Importance
    feature_importance = {
        feat: round(float(imp), 4)
        for feat, imp in zip(ENGINEERED_FEATURE_COLS, model.feature_importances_)
    }

    # Print Evaluation Report
    print("\n=======================================================")
    print("   OPTIMIZED REAL-TIME AML MODEL EVALUATION REPORT     ")
    print("=======================================================")
    print(f"  Optimal Decision Threshold : {optimal_threshold:.2f}")
    print(f"  Accuracy                  : {acc * 100:.2f}% (Before: {before_metrics['accuracy']*100:.2f}%)")
    print(f"  Precision (Suspicious)    : {prec * 100:.2f}% (Before: {before_metrics['precision']*100:.2f}%)")
    print(f"  Recall (Sensitivity)      : {rec * 100:.2f}% (Before: {before_metrics['recall']*100:.2f}%)")
    print(f"  F1-Score                  : {f1:.4f} (Before: {before_metrics['f1_score']:.4f})")
    print(f"  ROC-AUC Score             : {roc_auc:.4f} (Before: {before_metrics['roc_auc']:.4f})")
    print(f"  PR-AUC Score              : {pr_auc:.4f} (Before: {before_metrics['pr_auc']:.4f})")
    print("-------------------------------------------------------")
    print("  CONFUSION MATRIX COMPARISON:")
    print(f"    - True Negatives (Normal Correct)    : New={tn:<3} | Old={btn:<3}")
    print(f"    - False Positives (Normal Flagged)   : New={fp:<3} | Old={bfp:<3} (Change: {fp_change:+d})")
    print(f"    - False Negatives (Missed AML)       : New={fn:<3} | Old={bfn:<3} (Reduction: {fn_reduction:+d})")
    print(f"    - True Positives (Detected AML)      : New={tp:<3} | Old={btp:<3}")
    print("=======================================================\n")

    # TASK 11: Save Visualizations
    fig_dir = os.path.abspath(os.path.join(root_dir, "reports", "figures"))
    generate_and_save_visualizations(
        fig_dir=fig_dir,
        y_test=y_test.values,
        y_prob=y_prob,
        y_pred_opt=y_pred_opt,
        feature_names=ENGINEERED_FEATURE_COLS,
        feature_importances=model.feature_importances_,
        threshold_grid=threshold_info["threshold_grid"],
        optimal_threshold=optimal_threshold
    )

    # Save trained XGBoost model and IsolationForest model
    model_path = os.path.join(model_dir, "xgboost_aml.json")
    model.save_model(model_path)

    iso_model_path = os.path.join(model_dir, "isolation_forest.pkl")
    joblib.dump(iso_model, iso_model_path)

    metadata = {
        "model_version": "phase3_xgboost_optimized_v2",
        "training_seed": RANDOM_SEED,
        "dataset": os.path.relpath(dataset_path, root_dir),
        "features": ENGINEERED_FEATURE_COLS,
        "feature_names": ENGINEERED_FEATURE_COLS,
        "raw_features": RAW_FEATURE_COLS,
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "xgboost_version": xgboost.__version__,
        "optimal_threshold": float(optimal_threshold),
        "anomaly_score_range": {"min": iso_min, "max": iso_max},
        "hyperparameters": {**best_params},
        "cv_metrics": cv_metrics,
        "before_vs_after": {
            "before": before_metrics,
            "improved": improved_metrics,
            "false_negative_reduction": int(fn_reduction),
            "false_positive_change": int(fp_change)
        },
        "model_comparisons": model_comparisons,
        "threshold_evaluation": threshold_info,
        "feature_importance": feature_importance,
        "metrics": improved_metrics
    }

    meta_path = os.path.join(model_dir, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    feat_meta_path = os.path.join(model_dir, "feature_metadata.json")
    with open(feat_meta_path, "w") as f:
        json.dump({
            "feature_names": ENGINEERED_FEATURE_COLS,
            "optimal_threshold": float(optimal_threshold),
            "metrics": improved_metrics
        }, f, indent=2)

    print(f"Saved trained XGBoost model to {model_path}")
    print(f"Saved complete metadata to {meta_path}\n")
    return model, ENGINEERED_FEATURE_COLS, improved_metrics


if __name__ == "__main__":
    train_and_save_model()
