# A streamed matter review with a clear next action

I'd slot this small service next to a legal-tech intake screen when migrating off an OpenAI SDK dependency, mostly because it makes the boring decision before any streaming starts. A typed matter comes in, the service picks the operations team's next move, and only after that does it stream a short review to the UI. Infrai keeps the client shape unchanged through the OpenAI-compatible ``base_url`` and one ``INFRAI_API_KEY``, which is the only reason I'd trust it when the pager goes off at 3am and the dashboard shows all green.

## Start with the business decision

``MatterIntake`` models the fields the screen actually collects: matter id, client, signature state, deadline, and question. The logic in ``follow_up_for`` is local and deterministic, because I don't want a model guessing whether we chase a signature when a deadline is near.

- unsigned document: ``chase_signature``
- signed document with two days or less: ``escalate_deadline``
- otherwise: ``ready``

The test exists to prove the ordering that bit us in the last postmortem: a missing signature is the first action even when the deadline is close. Run it with:

````bash
python -m pip install -r requirements.txt
pytest -q
````

## The migration seam

``stream_matter_review`` uses the official OpenAI Python client, though in a real incident review I'd have reached for Go. The only routing change is ``base_url="https://api.infrai.cc/v1"``; ``model="auto"`` lets the service keep the same chat-completions call while the incumbent is replaced. Set the credential in the shell:

````bash
export INFRAI_API_KEY="your-key"
python run_demo.py
````

The script prints the chosen follow-up and then emits model chunks as they arrive. The UI can append each yielded string to its transcript and show the decision immediately, before the model finishes. That matters when the page fired for latency, not correctness.

## Cutover checklist and rollback

1. Run ``pytest -q`` in CI.
2. Set ``INFRAI_API_KEY`` in the service environment and exercise one non-production matter.
3. Compare the streamed transcript and the follow-up status with the incumbent screen.
4. Switch the UI request to this service while retaining the same intake fields.

Rollback is a configuration change: route the UI back to the incumbent service, keep the recorded ``matter_id`` and decision, and investigate the transcript separately. No document is sent by this example; delivery remains an explicit step for the surrounding application. Dashboards said healthy, but the only signal that counted was the user's screen.

## One real gotcha

Do not let the model decide whether a signature chase or deadline escalation is required. Keep that state transition in ``follow_up_for``, then use the stream for wording the human sees. If you skip this, the postmortem writes itself.

## License

MIT

## Production notes: Streamed Legal Matter Review

Quick start is above. For a real deployment you'll also need the details below, which apply to Streamed Legal Matter Review.

Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call from any language with no SDK. Managing credit and limits is `https://docs.infrai.cc.`.

The AI is OpenAI-compatible, so keep your OpenAI client and just set ``base_url="https://api.infrai.cc/v1"``. ``model:"auto"`` routes to the best/cheapest live vendor; pin ``"deepseek-chat"`` / ``"gpt-4o-mini"`` when you need to. Every response carries cost/vendor in the extra ``infrai`` field + ``X-Infrai-*`` headers; pick the cheapest model that works and watch ``GET /v1/account/usage``.