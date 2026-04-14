import os
import json
import numpy as np
import matplotlib.pyplot as plt

EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
NUM_CLASSES = len(EMOTIONS)
DATA_DIR = "YOLO_format"
OUTPUT_DIR = os.path.join("plots", "figures")


def load_class_counts(split_root: str):
    lbl_dir = os.path.join(split_root, "labels")
    counts = np.zeros(NUM_CLASSES, dtype=np.int64)
    invalid = 0

    if not os.path.isdir(lbl_dir):
        raise FileNotFoundError(f"Label directory not found: {lbl_dir}")

    for file_name in os.listdir(lbl_dir):
        if not file_name.endswith(".txt"):
            continue

        path = os.path.join(lbl_dir, file_name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip().split()
            if not first_line:
                invalid += 1
                continue
            class_id = int(float(first_line[0]))
        except Exception:
            invalid += 1
            continue

        if class_id == 7:
            continue
        if 0 <= class_id < NUM_CLASSES:
            counts[class_id] += 1
        else:
            invalid += 1

    return counts, invalid


def make_plot(counts_train, counts_valid, counts_all):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    x = np.arange(NUM_CLASSES)
    width = 0.26

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width, counts_train, width=width, label="Train", color="#1f77b4")
    ax.bar(x, counts_valid, width=width, label="Valid", color="#ff7f0e")
    ax.bar(x + width, counts_all, width=width, label="Combined", color="#2ca02c", alpha=0.75)

    ax.set_xticks(x)
    ax.set_xticklabels(EMOTIONS, rotation=20)
    ax.set_ylabel("Sample Count")
    ax.set_title("AffectNet YOLO Class Distribution")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)

    for i, v in enumerate(counts_all):
        ax.text(i + width, v + max(10, int(0.005 * counts_all.max())), str(int(v)), ha="center", fontsize=8)

    plt.tight_layout()
    fig_path = os.path.join(OUTPUT_DIR, "dataset_class_distribution.png")
    plt.savefig(fig_path, dpi=220)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 8))
    total = counts_all.sum()
    labels = [f"{emo} ({(c / total) * 100:.1f}%)" for emo, c in zip(EMOTIONS, counts_all)]
    ax2.pie(counts_all, labels=labels, autopct="%1.1f%%", startangle=120)
    ax2.set_title("Combined Split Class Share")
    plt.tight_layout()
    pie_path = os.path.join(OUTPUT_DIR, "dataset_class_share_pie.png")
    plt.savefig(pie_path, dpi=220)
    plt.close(fig2)

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ideal = total / NUM_CLASSES
    ratio = counts_all / ideal
    ax3.bar(EMOTIONS, ratio, color="#9467bd")
    ax3.axhline(1.0, color="black", linestyle="--", linewidth=1)
    ax3.set_ylabel("Observed / Ideal")
    ax3.set_title("Imbalance Ratio by Class (Combined)")
    ax3.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=20)
    plt.tight_layout()
    ratio_path = os.path.join(OUTPUT_DIR, "dataset_imbalance_ratio.png")
    plt.savefig(ratio_path, dpi=220)
    plt.close(fig3)

    return fig_path, pie_path, ratio_path


def summarize(counts_train, counts_valid, invalid_train, invalid_valid):
    counts_all = counts_train + counts_valid
    total = int(counts_all.sum())

    min_count = int(counts_all.min())
    max_count = int(counts_all.max())
    minority = EMOTIONS[int(np.argmin(counts_all))]
    majority = EMOTIONS[int(np.argmax(counts_all))]

    imbalance_ratio = (max_count / min_count) if min_count > 0 else float("inf")

    summary = {
        "train_counts": {emo: int(c) for emo, c in zip(EMOTIONS, counts_train)},
        "valid_counts": {emo: int(c) for emo, c in zip(EMOTIONS, counts_valid)},
        "combined_counts": {emo: int(c) for emo, c in zip(EMOTIONS, counts_all)},
        "total_samples": total,
        "invalid_labels_train": int(invalid_train),
        "invalid_labels_valid": int(invalid_valid),
        "majority_class": majority,
        "minority_class": minority,
        "majority_minority_ratio": round(float(imbalance_ratio), 4),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_json = os.path.join(OUTPUT_DIR, "dataset_imbalance_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary, out_json


def main():
    train_root = os.path.join(DATA_DIR, "train")
    valid_root = os.path.join(DATA_DIR, "valid")

    counts_train, invalid_train = load_class_counts(train_root)
    counts_valid, invalid_valid = load_class_counts(valid_root)
    counts_all = counts_train + counts_valid

    fig_path, pie_path, ratio_path = make_plot(counts_train, counts_valid, counts_all)
    summary, summary_path = summarize(counts_train, counts_valid, invalid_train, invalid_valid)

    print("=== Dataset Imbalance Check ===")
    print(f"Total samples: {summary['total_samples']}")
    print(f"Majority class: {summary['majority_class']}")
    print(f"Minority class: {summary['minority_class']}")
    print(f"Majority/Minority ratio: {summary['majority_minority_ratio']}")
    print(f"Invalid labels (train): {summary['invalid_labels_train']}")
    print(f"Invalid labels (valid): {summary['invalid_labels_valid']}")
    print(f"Summary JSON: {summary_path}")
    print(f"Plot 1: {fig_path}")
    print(f"Plot 2: {pie_path}")
    print(f"Plot 3: {ratio_path}")


if __name__ == "__main__":
    main()
