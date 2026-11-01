import pytest

from cost_tracker import CostTracker


def test_starts_empty():
    tracker = CostTracker()
    assert tracker.total_tokens == 0
    assert tracker.total_agent_calls == 0
    assert tracker.estimated_cost_usd == 0


def test_accumulates_tokens_and_calls_per_agent():
    tracker = CostTracker()
    tracker.record_usage("strategist", 100, 20)
    tracker.record_usage("retriever", 50, 10)
    tracker.record_usage("strategist", 30, 5)

    assert tracker.input_tokens == 180
    assert tracker.output_tokens == 35
    assert tracker.total_tokens == 215
    assert tracker.agent_calls == {"strategist": 2, "retriever": 1}
    assert tracker.total_agent_calls == 3


def test_cost_uses_per_million_pricing():
    tracker = CostTracker()
    tracker.record_usage("strategist", 1_000_000, 1_000_000)
    expected = tracker.INPUT_COST_PER_M_USD + tracker.OUTPUT_COST_PER_M_USD
    assert tracker.estimated_cost_usd == pytest.approx(expected)


def test_trackers_do_not_share_agent_calls():
    a, b = CostTracker(), CostTracker()
    a.record_usage("strategist", 1, 1)
    assert b.agent_calls == {}
