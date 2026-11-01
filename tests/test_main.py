from types import SimpleNamespace

from main import _extract_usage


def test_extracts_author_and_token_counts():
    event = SimpleNamespace(
        author="retriever",
        usage_metadata=SimpleNamespace(prompt_token_count=120, candidates_token_count=30),
    )
    assert _extract_usage(event) == ("retriever", 120, 30)


def test_missing_usage_metadata_returns_zero_tokens():
    event = SimpleNamespace(author="strategist", usage_metadata=None)
    assert _extract_usage(event) == ("strategist", 0, 0)


def test_none_token_counts_are_treated_as_zero():
    event = SimpleNamespace(
        author="extractor",
        usage_metadata=SimpleNamespace(prompt_token_count=None, candidates_token_count=None),
    )
    assert _extract_usage(event) == ("extractor", 0, 0)


def test_missing_author_is_unknown():
    event = SimpleNamespace(usage_metadata=None)
    assert _extract_usage(event) == ("unknown", 0, 0)
