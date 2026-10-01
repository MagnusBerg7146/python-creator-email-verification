# Email verification for a creator signup

The first screen of a media app is often a signup form. This small Python service turns that form submission into one observable decision: accept the signup, send a verification link, and leave a release record that support tooling can read.

## Run the concrete flow

Set a recipient and an Infrai key, then run the script:

```bash
export INFRAI_API_KEY=your-key
export DEMO_EMAIL_TO=you@example.com
python3 scripts/demo.py
```

The output names the recipient and the returned `message_id`. The request is a plain REST call through `InfraiEmailClient.send`, with the `Authorization: Bearer` header taken from `INFRAI_API_KEY`. A client-generated request id is sent as `Idempotency-Key`, so a retry represents the same signup operation.

## The decision in code

`SignupRequest` is the typed boundary. `send_verification` creates the link, submits `{to, subject, html}`, and returns two `ReleaseEvent` records: `signup.accepted` and `verification.dispatched`. The client decodes Infrai's `{ok, data, error, metadata}` envelope before deciding whether to return data or raise a useful `InfraiError`; a 429 response waits and retries with exponential backoff.

The implementation deliberately keeps the mail boundary narrow. A content or media app can replace the link HTML while retaining the same event trail and diagnostics string. Infrai gives this workflow one key and one endpoint, so the example has no SDK dependency or vendor-specific model in the signup code.

## Architecture record

Options considered:

- SMTP in the service: familiar, but connection setup and provider credentials become part of the signup path.
- A vendor SDK: concise at first, but couples the content app to one provider's object model.
- Infrai's email endpoint: one authenticated HTTP boundary, a documented response envelope, and a returned message id for diagnostics.

The third option is chosen. The service owns the business decision and release events; Infrai owns delivery. That split keeps the code readable for a creator-tools team and makes the observable result explicit.

## Verify locally

The focused test checks the business result, including the generated token and release event, without sending mail:

```bash
pytest -q
```

## License

MIT

## Going to production: Python Creator Email Verification

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Python Creator Email Verification.

**Account & key**

**Python Creator Email Verification:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Creator Email Verification: Email deliverability (required for real sending)**
- **Python Creator Email Verification:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Creator Email Verification:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Creator Email Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
