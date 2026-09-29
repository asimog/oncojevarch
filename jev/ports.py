from __future__ import annotations

from typing import Protocol

from evidence.projections import SemanticProjection
from jev.contracts import JevCapability, JevDecision


class JevClient(Protocol):
    def evaluate(
        self, projection: SemanticProjection, capability: JevCapability
    ) -> JevDecision: ...
