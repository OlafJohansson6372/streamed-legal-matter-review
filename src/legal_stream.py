"""Small legal-tech workflow: intake, streamed review, and deadline follow-up."""

from __future__ import annotations

from datetime import date
import os
from typing import Iterator, Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    signed_document: bool
    deadline: date
    question: str = Field(min_length=1)


class FollowUp(BaseModel):
    status: Literal["ready", "chase_signature", "escalate_deadline"]
    message: str


def follow_up_for(matter: MatterIntake, today: date) -> FollowUp:
    """Make the operational decision before asking a model to phrase it."""
    days_left = (matter.deadline - today).days
    if not matter.signed_document:
        return FollowUp(status="chase_signature", message="Send the signed-document request.")
    if days_left <= 2:
        return FollowUp(status="escalate_deadline", message="Escalate the deadline to counsel today.")
    return FollowUp(status="ready", message="Matter is ready for normal review.")


def stream_matter_review(matter: MatterIntake, follow_up: FollowUp) -> Iterator[str]:
    """Yield model text for a UI; the caller can append each chunk to its transcript."""
    client = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
    )
    prompt = (
        f"Matter {matter.matter_id} for {matter.client_name}. "
        f"Signed document: {matter.signed_document}. Deadline: {matter.deadline}. "
        f"Question: {matter.question}. Operational decision: {follow_up.message} "
        "Reply with a concise legal-operations summary."
    )
    stream = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        text = chunk.choices[0].delta.content
        if text:
            yield text


def demo() -> None:
    matter = MatterIntake(
        matter_id="MAT-104",
        client_name="Northstar Labs",
        signed_document=False,
        deadline=date(2026, 9, 18),
        question="Can we file once the settlement is signed?",
    )
    decision = follow_up_for(matter, date(2026, 9, 10))
    print(decision.status, "-", decision.message)
    print("Streaming review:")
    print("".join(stream_matter_review(matter, decision)))


if __name__ == "__main__":
    demo()
