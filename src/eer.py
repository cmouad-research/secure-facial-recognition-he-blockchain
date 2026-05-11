import sys
import pandas as pd
import numpy as np

def compute_eer(csv_path: str):
    df = pd.read_csv(csv_path)
    df["score"] = df["score"].astype(float)

    genuine = df[df["case"] == "genuine"]["score"].to_numpy()
    impostor = df[df["case"] == "impostor"]["score"].to_numpy()

    thresholds = np.sort(df["score"].unique())

    best_tau = None
    best_far = None
    best_frr = None
    best_gap = float("inf")

    for tau in thresholds:
        far = np.mean(impostor >= tau)
        frr = np.mean(genuine < tau)
        gap = abs(far - frr)

        if gap < best_gap:
            best_gap = gap
            best_tau = tau
            best_far = far
            best_frr = frr

    eer = (best_far + best_frr) / 2.0

    print("EER/CER results")
    print(f"threshold: {best_tau}")
    print(f"FAR at EER: {best_far}")
    print(f"FRR at EER: {best_frr}")
    print(f"EER: {eer}")
    print(f"gap: {best_gap}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.eer <csv_path>")
        raise SystemExit(1)
    compute_eer(sys.argv[1])
