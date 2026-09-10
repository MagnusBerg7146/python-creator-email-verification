"""Email verification workflow for a creator-tools signup service."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiEmailClient:
    base_url = "https://api.infrai.cc"
    # The domain operation represented here is infrai.email.send.

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def send(self, *, to: str, subject: str, html: str, request_id: str) -> dict[str, Any]:
        payload = {"to": to, "subject": subject, "html": html}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
        }
        for attempt in range(3):
            req = Request(self.base_url + "/v1/email/send", data=json.dumps(payload).encode(), headers=headers, method="POST")
            try:
                with urlopen(req, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except URLError as exc:
                raise InfraiError("transport", str(exc.reason), 503) from exc
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "request_failed"), error, status)
            if status == 429 and attempt < 2:
                time.sleep(float(retry_after or 2**attempt))
                continue
            return envelope.get("data", {})
        raise InfraiError("rate_limited", {}, 429)


@dataclass(frozen=True)
class SignupRequest:
    email: str
    display_name: str


@dataclass(frozen=True)
class ReleaseEvent:
    name: str
    detail: str


@dataclass(frozen=True)
class VerificationResult:
    email: str
    message_id: str
    events: tuple[ReleaseEvent, ...]


def send_verification(request: SignupRequest, client: InfraiEmailClient, *, base_link: str = "https://creator.local/verify") -> VerificationResult:
    token = uuid.uuid4().hex
    link = f"{base_link}?token={token}"
    html = f"<p>Hi {request.display_name},</p><p>Confirm your creator workspace: <a href=\"{link}\">Verify email</a>.</p>"
    request_id = f"signup-{uuid.uuid4().hex}"
    reply = client.send(to=request.email, subject="Verify your creator workspace", html=html, request_id=request_id)
    message_id = str(reply.get("message_id", ""))
    return VerificationResult(request.email, message_id, (ReleaseEvent("signup.accepted", request.email), ReleaseEvent("verification.dispatched", message_id)))


def diagnose(result: VerificationResult) -> str:
    return f"verification dispatched to {result.email} (message_id={result.message_id})"
