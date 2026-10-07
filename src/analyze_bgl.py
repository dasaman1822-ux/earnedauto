import argparse
from collections import Counter
from pathlib import Path

from log_templates import DrainTemplateMiner


DATA_FILE = Path.home() / "earnedauto-data" / "BGL.log"
DEFAULT_TEMPLATE_SAMPLE = 10_000


def extract_message(line: str) -> str:
    """Return the unstructured BGL message portion after the RAS marker."""
    parts = line.split()
    try:
        ras_index = parts.index("RAS")
    except ValueError:
        # Keep the analysis robust for unexpected/non-standard lines.
        return " ".join(parts[1:])
    return " ".join(parts[ras_index:])


def analyze_bgl(template_sample: int = DEFAULT_TEMPLATE_SAMPLE):
    label_counts = Counter()
    template_miner = DrainTemplateMiner(depth=4, similarity_threshold=0.5)
    template_lines = 0

    with DATA_FILE.open(
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as file:
        for line in file:
            parts = line.split()
            if not parts:
                continue

            label_counts[parts[0]] += 1

            if template_lines < template_sample:
                message = extract_message(line)
                if message:
                    template_miner.add_message(message)
                    template_lines += 1

    total_records = sum(label_counts.values())
    normal_records = label_counts.get("-", 0)
    alert_records = total_records - normal_records

    print(f"Total records: {total_records}")
    print(f"Normal records: {normal_records}")
    print(f"Alert records: {alert_records}")
    print(f"Alert percentage: {alert_records / total_records * 100:.2f}%")
    print(f"Distinct labels: {len(label_counts)}")
    print(f"Template sample records: {template_lines}")
    print(f"Templates mined from sample: {len(template_miner.clusters)}")

    print("\nTop 10 mined templates:")
    for cluster in sorted(template_miner.clusters, key=lambda item: item.size, reverse=True)[:10]:
        print(f"{cluster.size}: {cluster.template}")

    print("\nTop 15 alert labels:")
    alert_labels = [
        (label, count)
        for label, count in label_counts.most_common()
        if label != "-"
    ]

    for label, count in alert_labels[:15]:
        print(f"{label}: {count}")

    return label_counts, template_miner


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze BGL labels and mine log templates.")
    parser.add_argument(
        "--template-sample",
        type=int,
        default=DEFAULT_TEMPLATE_SAMPLE,
        help="Number of initial BGL records used for Drain-style template mining.",
    )
    args = parser.parse_args()
    if args.template_sample < 1:
        parser.error("--template-sample must be at least 1")
    analyze_bgl(template_sample=args.template_sample)
