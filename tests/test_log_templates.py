from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from log_templates import DrainTemplateMiner
from analyze_bgl import extract_message


def test_drain_style_miner_groups_variable_tokens():
    miner = DrainTemplateMiner(depth=4, similarity_threshold=0.5)
    miner.add_message("RAS KERNEL FATAL data TLB error 123")
    miner.add_message("RAS KERNEL FATAL data TLB error 456")

    assert len(miner.clusters) == 1
    assert miner.clusters[0].size == 2
    assert miner.clusters[0].template.endswith("<*>")


def test_extract_message_uses_bgl_ras_boundary():
    line = "KERNDTLB 1117985502 2005.06.05 R36-M0-NC-C:J05-U01 RAS KERNEL FATAL data TLB error interrupt"
    assert extract_message(line) == "RAS KERNEL FATAL data TLB error interrupt"
