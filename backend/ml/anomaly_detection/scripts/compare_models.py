import os
import json
import joblib
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_curve, auc, precision_recall_curve, average_precision_score

BASE_DIR = r"C:\Users\lukep\Documents\MVS\backend\ml\anomaly_detection\results\week2\window_sweep_results\window_configs\ws512_st16_thr0p25"
TINYML_DIR = os.path.join(BASE_DIR, "tinyml")
NON_TINYML_DIR = os.path.join(BASE_DIR, "model")
OUT_DIR = os.path.join(BASE_DIR, "model_comparison")

os.makedirs(OUT_DIR, exist_ok=True)

def load_npz(path):
    print("Loading datasets...")
    data = np.load(path)
    return data["x_test"], data["y_test"]

def predict_non_tinyml(x_test):
    print("Evaluating Non-TinyML Model (MLPRegressor)...")
    scaler = joblib.load(os.path.join(NON_TINYML_DIR, "scaler.joblib"))
    model = joblib.load(os.path.join(NON_TINYML_DIR, "autoencoder.joblib"))
    with open(os.path.join(NON_TINYML_DIR, "threshold.json")) as f:
        threshold = json.load(f)["threshold"]
        
    x_test_s = scaler.transform(x_test)
    y_pred = model.predict(x_test_s)
    err = np.mean((x_test_s - y_pred) ** 2, axis=1)
    
    labels = (err > threshold).astype(np.int32)
    return err, labels, threshold

def predict_tinyml(x_test):
    print("Evaluating TinyML Model (Tiny Dense Autoencoder)...")
    model = tf.keras.models.load_model(os.path.join(TINYML_DIR, "tiny_dense_autoencoder.keras"))
    with open(os.path.join(TINYML_DIR, "threshold.json")) as f:
        threshold = json.load(f)["threshold"]
    with open(os.path.join(TINYML_DIR, "scaling.json")) as f:
        scale_data = json.load(f)
        mean = np.array(scale_data["mean"])
        std = np.array(scale_data["std"])
        
    x_test_s = (x_test - mean) / std
    y_pred = model.predict(x_test_s, verbose=0)
    err = np.mean((x_test_s - y_pred) ** 2, axis=1)
    
    labels = (err > threshold).astype(np.int32)
    return err, labels, threshold


def main():
    x_test, y_test = load_npz(os.path.join(TINYML_DIR, "dataset.npz"))
    
    err_nt, labels_nt, thresh_nt = predict_non_tinyml(x_test)
    err_t, labels_t, thresh_t = predict_tinyml(x_test)
    
    # 1. Classification Reports
    report = "=== NON-TINYML MODEL ===\n"
    report += f"Threshold: {thresh_nt:.6f}\n"
    p, r, f, s = precision_recall_fscore_support(y_test, labels_nt, labels=[0, 1])
    report += f"Normal:  P={p[0]:.4f}, R={r[0]:.4f}, F1={f[0]:.4f}, Support={s[0]}\n"
    report += f"Anomaly: P={p[1]:.4f}, R={r[1]:.4f}, F1={f[1]:.4f}, Support={s[1]}\n"
    
    report += "\n=== TINYML MODEL ===\n"
    report += f"Threshold: {thresh_t:.6f}\n"
    p, r, f, s = precision_recall_fscore_support(y_test, labels_t, labels=[0, 1])
    report += f"Normal:  P={p[0]:.4f}, R={r[0]:.4f}, F1={f[0]:.4f}, Support={s[0]}\n"
    report += f"Anomaly: P={p[1]:.4f}, R={r[1]:.4f}, F1={f[1]:.4f}, Support={s[1]}\n"
    
    with open(os.path.join(OUT_DIR, "comparison_report.txt"), "w") as f:
        f.write(report)
    print(report)
    
    # 2. Confusion Matrices Side-by-Side
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    sns.heatmap(confusion_matrix(y_test, labels_nt), annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=['Normal', 'Anomaly'], yticklabels=['Normal', 'Anomaly'], ax=axes[0])
    axes[0].set_title('Non-TinyML Confusion Matrix')
    axes[0].set_xlabel('Predicted')
    axes[0].set_ylabel('True')
    
    sns.heatmap(confusion_matrix(y_test, labels_t), annot=True, fmt='d', cmap='Oranges', cbar=False,
                xticklabels=['Normal', 'Anomaly'], yticklabels=['Normal', 'Anomaly'], ax=axes[1])
    axes[1].set_title('TinyML Confusion Matrix')
    axes[1].set_xlabel('Predicted')
    axes[1].set_ylabel('True')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "confusion_matrices.png"), dpi=300)
    plt.close()
    
    # 3. Overlaid ROC curve
    # Using raw errors as probabilities (the higher error, the more likely it's an anomaly)
    fpr_nt, tpr_nt, _ = roc_curve(y_test, err_nt)
    auc_nt = auc(fpr_nt, tpr_nt)
    
    fpr_t, tpr_t, _ = roc_curve(y_test, err_t)
    auc_t = auc(fpr_t, tpr_t)
    
    plt.figure(figsize=(6, 5))
    plt.plot(fpr_nt, tpr_nt, color='blue', lw=2, label=f'Non-TinyML (AUC = {auc_nt:.2f})')
    plt.plot(fpr_t, tpr_t, color='orange', lw=2, label=f'TinyML (AUC = {auc_t:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=1, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "roc_curve_comparison.png"), dpi=300)
    plt.close()
    
    # 4. Overlaid PR curve
    precision_nt, recall_nt, _ = precision_recall_curve(y_test, err_nt)
    ap_nt = average_precision_score(y_test, err_nt)
    
    precision_t, recall_t, _ = precision_recall_curve(y_test, err_t)
    ap_t = average_precision_score(y_test, err_t)
    
    plt.figure(figsize=(6, 5))
    plt.plot(recall_nt, precision_nt, color='blue', lw=2, label=f'Non-TinyML (AP = {ap_nt:.2f})')
    plt.plot(recall_t, precision_t, color='orange', lw=2, label=f'TinyML (AP = {ap_t:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve (PR)')
    plt.legend(loc="lower left")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "pr_curve_comparison.png"), dpi=300)
    plt.close()
    
    print(f"Comparisons saved to {OUT_DIR}")

if __name__ == "__main__":
    main()
