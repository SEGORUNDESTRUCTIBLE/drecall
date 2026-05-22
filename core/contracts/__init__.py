"""Contracts package for architecture-stabilizing interfaces.

This package contains typed Protocols, dataclasses, and simple
exception types that define the ingestion/processing contracts
for Phase 7A. The modules are intentionally lightweight and
implementation-free — they define boundaries, inputs/outputs,
and failure semantics only.
"""

__all__ = [
    "provider_contracts",
    "ingestion_contracts",
    "persistence_contracts",
    "revision_contracts",
    "duplicate_contracts",
]
