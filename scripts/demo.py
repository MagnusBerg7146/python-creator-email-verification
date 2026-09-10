import os
import sys
from pathlib import Path

# Make the repository root importable when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.verification_service import InfraiEmailClient, SignupRequest, diagnose, send_verification


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise SystemExit("DEMO_EMAIL_TO is required")
    result = send_verification(SignupRequest(recipient, "Mina"), InfraiEmailClient())
    print(diagnose(result))


if __name__ == "__main__":
    main()
