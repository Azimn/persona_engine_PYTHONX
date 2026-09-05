import time

from persona_engine.duck.services import ParallelServiceRegistry, ServiceContext
from persona_engine.duck.types import CognitiveItem


class Service:
    def __init__(self, name, delay=0.0, canonical=False):
        self.service_name = name
        self.delay = delay
        self.canonical = canonical
    def propose(self, context):
        time.sleep(self.delay)
        return [CognitiveItem(
            item_id=f"{self.service_name}-item",
            tick=context.tick,
            kind="hypothesis",
            source_module="specialist",
            subject_id=context.subject_id,
            payload={},
            canonical=self.canonical,
        )]


def test_parallel_registry_collates_results_deterministically_by_service_name():
    registry = ParallelServiceRegistry([Service("z", 0.01), Service("a", 0.02)], timeout_seconds=1.0)
    items, errors = registry.proposals(ServiceContext(0, "s", "p", {}))
    assert errors == []
    assert [item.item_id for item in items] == ["a-item", "z-item"]


def test_parallel_registry_localizes_timeout_and_illegal_canonical_output():
    registry = ParallelServiceRegistry([Service("slow", 0.2), Service("bad", canonical=True)], timeout_seconds=0.03)
    items, errors = registry.proposals(ServiceContext(0, "s", "p", {}))
    assert items == []
    assert any(error.startswith("bad:ValueError") for error in errors)
    assert any(error.startswith("slow:TimeoutError") for error in errors)
