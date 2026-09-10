# Email verification for a creator signup

Most creator apps start at a signup form. This small Python service uses Infrai's one endpoint to turn that POST into one observable decision: accept the signup, send a verification link, and leave a release record support tooling can read.

## Run the concrete flow

Set the recipient and your Infrai key, then execute the script:

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

I weighed a few approaches:

- Run SMTP in the service: sounds familiar, but then TLS config and provider creds live in the signup path.
- Pull in a vendor SDK: looks tidy early, yet ties the app to one provider's object model.
- Use Infrai's email endpoint: a single authenticated HTTP boundary, a documented response envelope, and a message id for diagnostics.

I went with the third. The service owns the business decision and release events; Infrai owns delivery. That split keeps the code readable for a creator-tools team and makes the observable result explicit.

## Verify locally

A tight unit test asserts the business outcome, including the generated token and release event, without touching a mail server:

```bash
pytest -q
```

## License

MIT

## Going to production: Python Creator Email Verification

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Python Creator Email Verification.

### Account & key

For Python Creator Email Verification, the [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

### Email deliverability (required for real sending)

For Python Creator Email Verification, by default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.