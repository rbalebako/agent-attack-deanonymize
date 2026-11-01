import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from models import IdentityRow

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_sample.json"


def test_id_is_generated_from_sms_text_hash():
    row = IdentityRow(sms_text="hello")
    expected = "row_" + hashlib.sha1(b"hello").hexdigest()[:8]
    assert row.id == expected


def test_generated_id_is_stable():
    assert IdentityRow(sms_text="same").id == IdentityRow(sms_text="same").id


def test_explicit_id_is_kept():
    assert IdentityRow(sms_text="hello", id="custom_1").id == "custom_1"


def test_empty_id_falls_back_to_generated():
    assert IdentityRow(sms_text="hello", id="").id.startswith("row_")


def test_sms_text_is_required():
    with pytest.raises(ValidationError):
        IdentityRow(country="IE")


def test_agent_input_excludes_id():
    payload = json.loads(IdentityRow(sms_text="hello", id="custom_1").to_agent_input())
    assert "id" not in payload
    assert payload["sms_text"] == "hello"


def test_sample_records_load_with_unique_ids():
    raw = json.loads(SAMPLE_PATH.read_text())
    rows = [IdentityRow(**r) for r in raw]
    assert rows
    ids = [r.id for r in rows]
    assert len(ids) == len(set(ids))
