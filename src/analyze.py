import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


LATENCY_COLUMNS = [
    "embed_ms",
    "ipfs_cat_ms",
    "he_eval_ms",
    "decrypt_ms",
    "end_to_end_ms",
    "chain_request_ms",
    "chain_decide_ms",
    "chain_total_ms",
]
control_metrics = ["chain_request_ms", "chain_decide_ms", "chain_total_ms"]

def _safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def _latency_stats(df, col):
    if col not in df.columns:
        return None
    values = _safe_numeric(df[col]).dropna().to_numpy()
    if values.size == 0:
        return None
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
    }


def _accuracy_stats(df):
    required = {"case", "decision"}
    if not required.issubset(df.columns):
        return None

    case = df["case"].astype(str)
    decision = df["decision"].astype(str)

    is_genuine = case == "genuine"
    is_impostor = case == "impostor"
    is_accept = decision == "accept"
    is_reject = decision == "reject"

    genuine_total = int(is_genuine.sum())
    impostor_total = int(is_impostor.sum())

    false_reject = int((is_genuine & is_reject).sum())
    false_accept = int((is_impostor & is_accept).sum())

    total = int((is_genuine | is_impostor).sum())
    correct = int((is_genuine & is_accept).sum() + (is_impostor & is_reject).sum())

    far = (false_accept / impostor_total) if impostor_total else None
    frr = (false_reject / genuine_total) if genuine_total else None
    acc = (correct / total) if total else None

    return {
        "far": far,
        "frr": frr,
        "accuracy": acc,
        "genuine_total": genuine_total,
        "impostor_total": impostor_total,
    }


def _roc_points(df):
    required = {"case", "score"}
    if not required.issubset(df.columns):
        return None

    scores = _safe_numeric(df["score"]).to_numpy()
    case = df["case"].astype(str).to_numpy()

    valid = ~np.isnan(scores) & np.isin(case, ["genuine", "impostor"])
    scores = scores[valid]
    case = case[valid]
    if scores.size == 0:
        return None

    thresholds = np.unique(scores)
    thresholds = np.concatenate([thresholds, [thresholds.max() + 1e-9]])

    tprs = []
    fprs = []
    for thr in thresholds:
        accept = scores >= thr
        is_genuine = case == "genuine"
        is_impostor = case == "impostor"

        tp = np.sum(accept & is_genuine)
        fp = np.sum(accept & is_impostor)
        fn = np.sum((~accept) & is_genuine)
        tn = np.sum((~accept) & is_impostor)

        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0

        tprs.append(tpr)
        fprs.append(fpr)

    order = np.argsort(fprs)
    return np.array(fprs)[order], np.array(tprs)[order]


def main():
    raw_dir = Path("results/raw")
    out_dir = Path("results")
    tables_dir = out_dir / "tables"
    figures_dir = out_dir / "figures"

    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(raw_dir.glob("*.csv"))
    summaries = {}

    latency_rows = []
    accuracy_rows = []

    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue

        file_key = csv_path.name
        summary = {
            "file": file_key,
            "latency": {},
            "accuracy": None,
        }

        for metric in LATENCY_COLUMNS:
            stats = _latency_stats(df, metric)
            summary["latency"][metric] = stats
            if stats is not None:
                latency_rows.append(
                    {
                        "file": file_key,
                        "metric": metric,
                        "mean_ms": stats["mean"],
                        "median_ms": stats["median"],
                        "p95_ms": stats["p95"],
                    }
                )

        acc = _accuracy_stats(df)
        summary["accuracy"] = acc
        if acc is not None:
            accuracy_rows.append(
                {
                    "file": file_key,
                    "far": acc["far"],
                    "frr": acc["frr"],
                    "accuracy": acc["accuracy"],
                }
            )

        summaries[file_key] = summary

    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    if latency_rows:
        latency_df = pd.DataFrame(latency_rows)
        latency_df.to_latex(tables_dir / "latency_table.tex", index=False)
    else:
        (tables_dir / "latency_table.tex").write_text("", encoding="utf-8")

    if accuracy_rows:
        accuracy_df = pd.DataFrame(accuracy_rows)
        accuracy_df.to_latex(tables_dir / "accuracy_table.tex", index=False)
    else:
        (tables_dir / "accuracy_table.tex").write_text("", encoding="utf-8")

    if latency_rows:
        latency_df = pd.DataFrame(latency_rows)
        p95_df = latency_df[latency_df["metric"] == "end_to_end_ms"]
        if not p95_df.empty:
            plt.figure(figsize=(8, 4))
            plt.bar(p95_df["file"], p95_df["p95_ms"])
            plt.ylabel("p95 end_to_end_ms")
            plt.xlabel("file")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(figures_dir / "latency_p95.png")
            plt.close()
        else:
            plt.figure(figsize=(4, 3))
            plt.text(0.5, 0.5, "No end_to_end_ms", ha="center")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(figures_dir / "latency_p95.png")
            plt.close()
    else:
        plt.figure(figsize=(4, 3))
        plt.text(0.5, 0.5, "No latency data", ha="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(figures_dir / "latency_p95.png")
        plt.close()

    plt.figure(figsize=(5, 5))
    plotted = False
    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue
        roc = _roc_points(df)
        if roc is None:
            continue
        fprs, tprs = roc
        plt.plot(fprs, tprs, label=csv_path.name)
        plotted = True

    if plotted:
        plt.plot([0, 1], [0, 1], "k--", linewidth=1)
        plt.xlabel("FPR")
        plt.ylabel("TPR")
        plt.legend(fontsize=8)
    else:
        plt.text(0.5, 0.5, "No ROC data", ha="center")
        plt.axis("off")

    plt.tight_layout()
    plt.savefig(figures_dir / "roc.png")
    plt.close()

    if latency_rows:
        latency_df = pd.DataFrame(latency_rows)
    else:
        latency_df = pd.DataFrame(columns=["file", "metric", "mean_ms", "median_ms", "p95_ms"])
    if accuracy_rows:
        accuracy_df = pd.DataFrame(accuracy_rows)
    else:
        accuracy_df = pd.DataFrame(columns=["file", "far", "frr", "accuracy"])

    print("Latency Summary")
    if latency_df.empty:
        print("(no latency data)")
    else:
        print(latency_df.to_string(index=False))

    print("\nAccuracy Summary")
    if accuracy_df.empty:
        print("(no accuracy data)")
    else:
        print(accuracy_df.to_string(index=False))


if __name__ == "__main__":
    main()
