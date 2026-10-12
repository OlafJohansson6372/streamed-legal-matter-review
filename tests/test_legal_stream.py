from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from src.legal_stream import FollowUp, MatterIntake, follow_up_for, stream_matter_review


def test_unsigned_document_takes_priority_over_deadline_escalation() -> None:
    matter = MatterIntake(
        matter_id="MAT-1",
        client_name="Acme",
        signed_document=False,
        deadline=date(2026, 9, 11),
        question="What is next?",
    )

    decision = follow_up_for(matter, date(2026, 9, 10))

    assert decision.status == "chase_signature"
    assert decision.message == "Send the signed-document request."


def test_stream_skips_empty_choices() -> None:
    matter = MatterIntake(
        matter_id="MAT-1",
        client_name="Acme",
        signed_document=True,
        deadline=date(2026, 9, 11),
        question="What is next?",
    )
    chunks = [
        SimpleNamespace(choices=[]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Review ready."))]),
    ]
    with patch("src.legal_stream.OpenAI") as client, patch.dict(
        "os.environ", {"INFRAI_API_KEY": "test-key"}
    ):
        client.return_value.chat.completions.create.return_value = chunks
        result = list(stream_matter_review(matter, FollowUp(status="ready", message="Ready.")))

    assert result == ["Review ready."]
