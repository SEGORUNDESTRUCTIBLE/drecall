"""Registry for revision algorithms and scheduler selection."""

from __future__ import annotations

from typing import Dict

from .revision_algorithms import AdaptiveRevisionAlgorithm, RevisionAlgorithm, SimpleRevisionAlgorithm


class RevisionRegistry:
    """Registry mapping algorithm names to revision algorithm implementations."""

    _algorithms: Dict[str, RevisionAlgorithm] = {
        "simple": SimpleRevisionAlgorithm(),
        "adaptive": AdaptiveRevisionAlgorithm(),
    }

    @classmethod
    def get_algorithm(cls, name: str) -> RevisionAlgorithm:
        return cls._algorithms.get(name.lower(), cls._algorithms["adaptive"])

    @classmethod
    def available_algorithms(cls) -> Dict[str, RevisionAlgorithm]:
        return dict(cls._algorithms)

    @classmethod
    def register_algorithm(cls, name: str, algorithm: RevisionAlgorithm) -> None:
        cls._algorithms[name.lower()] = algorithm
