from collections import Counter
from pathlib import Path


DATA_FILE = Path.home() / "earnedauto-data" / "BGL.log"


def analyze_bgl():
    label_counts = Counter()

    with DATA_FILE.open(
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as file:
        for line in file:
            parts = line.split()

            if parts:
                label_counts[parts[0]] += 1

    total_records = sum(label_counts.values())
    normal_records = label_counts.get("-", 0)
    alert_records = total_records - normal_records

    print(f"Total records: {total_records}")
    print(f"Normal records: {normal_records}")
    print(f"Alert records: {alert_records}")
    print(f"Alert percentage: {alert_records / total_records * 100:.2f}%")
    print(f"Distinct labels: {len(label_counts)}")

    print("\nTop 15 alert labels:")

    alert_labels = [
        (label, count)
        for label, count in label_counts.most_common()
        if label != "-"
    ]

    for label, count in alert_labels[:15]:
        print(f"{label}: {count}")


if __name__ == "__main__":
    analyze_bgl()