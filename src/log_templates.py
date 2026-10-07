"""Lightweight Drain-style log template extraction.

The Project Guide asks for an existing log-template extraction approach rather
than a full custom log parser.  This module implements the core idea from
Drain (He et al., 2017): a fixed-depth prefix tree narrows candidate template
clusters, followed by token-level similarity and wildcard generalisation.
It intentionally exposes only the small surface needed by the BGL analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


WILDCARD = "<*>"


@dataclass
class TemplateCluster:
    """A mined log template and its number of assigned messages."""

    cluster_id: int
    tokens: list[str]
    size: int = 1

    @property
    def template(self) -> str:
        return " ".join(self.tokens)


@dataclass
class _Node:
    children: dict[str, "_Node"] = field(default_factory=dict)
    clusters: list[TemplateCluster] = field(default_factory=list)


class DrainTemplateMiner:
    """Small, deterministic implementation of the core Drain workflow."""

    def __init__(self, depth: int = 4, similarity_threshold: float = 0.5) -> None:
        if depth < 2:
            raise ValueError("depth must be at least 2")
        if not 0 < similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be in (0, 1]")
        self.depth = depth
        self.similarity_threshold = similarity_threshold
        self.root = _Node()
        self._next_cluster_id = 1

    def add_message(self, message: str) -> TemplateCluster:
        tokens = message.split()
        if not tokens:
            raise ValueError("message must contain at least one token")

        node = self.root.children.setdefault(str(len(tokens)), _Node())
        prefix_width = min(self.depth - 1, len(tokens))
        for token in tokens[:prefix_width]:
            key = token if token != WILDCARD else WILDCARD
            node = node.children.setdefault(key, _Node())

        candidates = node.clusters
        best: TemplateCluster | None = None
        best_similarity = -1.0
        for cluster in candidates:
            similarity = self._similarity(cluster.tokens, tokens)
            if similarity >= self.similarity_threshold and similarity > best_similarity:
                best = cluster
                best_similarity = similarity

        if best is None:
            best = TemplateCluster(self._next_cluster_id, list(tokens))
            self._next_cluster_id += 1
            candidates.append(best)
        else:
            best.tokens = self._merge(best.tokens, tokens)
            best.size += 1
        return best

    def add_messages(self, messages: Iterable[str]) -> None:
        for message in messages:
            if message.strip():
                self.add_message(message)

    @property
    def clusters(self) -> list[TemplateCluster]:
        clusters: list[TemplateCluster] = []

        def walk(node: _Node) -> None:
            clusters.extend(node.clusters)
            for child in node.children.values():
                walk(child)

        walk(self.root)
        return clusters

    @staticmethod
    def _similarity(template: list[str], tokens: list[str]) -> float:
        if len(template) != len(tokens):
            return 0.0
        comparable = 0
        matches = 0
        for left, right in zip(template, tokens):
            if left == WILDCARD:
                continue
            comparable += 1
            matches += left == right
        if comparable == 0:
            return 1.0
        return matches / comparable

    @staticmethod
    def _merge(template: list[str], tokens: list[str]) -> list[str]:
        return [left if left == right else WILDCARD for left, right in zip(template, tokens)]
