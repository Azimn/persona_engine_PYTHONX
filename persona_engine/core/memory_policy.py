"""Evidence-backed resident-memory policy for the Wayfarer reference runtime.

Residency is semantic. A memory stays resident when a demonstrated live consumer
needs its causal metadata, or when the first-person experience cannot yet be
safely reconstructed from canonical history. No global resident-memory count is
part of this contract.
"""

from __future__ import annotations

from collections import Counter

from .memory import KnowledgeSource, MemoryStore


POLICY_VERSION = "semantic-residency-v1"

# These reasons are deliberately conservative. USER_TOLD has a demonstrated
# cold-biography path plus current consumer-role retention. The remaining
# production/autobiographical families stay resident until their own
# reconstruction contracts are demonstrated.
SOURCE_RESIDENCY = {
    KnowledgeSource.USER_TOLD: "conditional_consumer_role_plus_cold_recoverability",
    KnowledgeSource.OBSERVED: "resident_not_safely_reconstructable",
    KnowledgeSource.REFLECTION: "resident_not_safely_reconstructable",
    KnowledgeSource.INFERRED: "resident_fail_closed_if_introduced",
    KnowledgeSource.CORE_IDENTITY: "resident_fail_closed_identity_owned_elsewhere",
}


def apply_resident_memory_policy(memory: MemoryStore, relationship) -> dict:
    """Apply the current semantic residency policy and return an audit report.

    USER_TOLD compaction is the only eviction path currently earned by evidence.
    Every other source is intentionally untouched. This wrapper turns that
    constraint into an explicit production contract so future work cannot
    silently reinterpret the current behavior as a numeric memory budget.
    """

    before = Counter(item.source.value for item in memory.memories)
    user_report = memory.compact_user_told_working_set(relationship)
    after = Counter(item.source.value for item in memory.memories)

    pinned_counts = {
        source.value: after.get(source.value, 0)
        for source in KnowledgeSource
        if source is not KnowledgeSource.USER_TOLD and after.get(source.value, 0)
    }
    return {
        "policy": POLICY_VERSION,
        "numeric_capacity": None,
        "source_reasons": {source.value: reason for source, reason in SOURCE_RESIDENCY.items()},
        "before_by_source": dict(sorted(before.items())),
        "after_by_source": dict(sorted(after.items())),
        "pinned_non_user_told": dict(sorted(pinned_counts.items())),
        "user_told": user_report,
    }
