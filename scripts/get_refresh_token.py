#!/usr/bin/env python3
"""
Generate a Google OAuth2 REFRESH TOKEN for the Google Ads API.

What you need first:
  1) An OAuth 2.0 Client ID + Secret from Google Cloud Console
     (APIs & Services → Credentials → Create credentials → OAuth client ID → Desktop app)
  2) Your OAuth Client ID must be allow-listed in Google Ads:
     Google Ads (MCC) → Tools & settings → API Center → OAuth2.0 client IDs → Add

This script opens a browser, you log in with the Google Ads user (has MCC access),
and it prints the refresh token. It can also optionally append it to your .env.

Usage:
  poetry run python scripts/get_refresh_token.py
"""
import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

SCOPE = ["https://www.googleapis.com/auth/adwords"]

def ask(prompt: str, default: str | None = None) -> str:
    s = f"{prompt}"
    if default:
        s += f" [{default}]"
    s += ": "
    val = input(s).strip()
    return val or (default or "")

def main() -> int:
    load_dotenv()  # so we can prefill from .env if present

    print("\n=== Google Ads OAuth Refresh Token Generator ===\n")

    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID") or ask("Enter OAuth Client ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET") or ask("Enter OAuth Client Secret")

    if not client_id or not client_secret:
        print("Client ID/Secret are required. Create them in Google Cloud Console (Desktop App).")
        return 1

    # Build a minimal client config in-memory
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }

    print("\nOpening your browser for Google login/consent...")
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPE)

    # Run a local server on a free port and wait for the OAuth redirect.
    creds = flow.run_local_server(open_browser=True, prompt="consent", authorization_prompt_message="")

    refresh = getattr(creds, "refresh_token", None)
    access = getattr(creds, "token", None)

    if not refresh:
        print("\nERROR: No refresh_token returned.")
        print("Tips:")
        print(" - Make sure your OAuth Client ID is added in Google Ads → API Center → OAuth2.0 client IDs.")
        print(" - If your consent screen is in TESTING, add your Google user as a Test user.")
        print(" - Ensure scope is exactly: https://www.googleapis.com/auth/adwords")
        return 2

    print("\n✅ Success!")
    print(f"Refresh token:\n{refresh}\n")
    print(f"(FYI access token (short-lived): {access[:20]}...)\n" if access else "")

    # Offer to append to .env
    root = Path.cwd()
    env_path = root / ".env"
    write = ask(f"Append refresh token to {env_path}? (y/N)", default="N").lower()
    if write == "y":
        # Preserve file, update/append key
        content = ""
        if env_path.exists():
            content = env_path.read_text()

        lines = []
        found = False
        for line in content.splitlines():
            if line.startswith("GOOGLE_ADS_REFRESH_TOKEN="):
                lines.append(f"GOOGLE_ADS_REFRESH_TOKEN={refresh}")
                found = True
            else:
                lines.append(line)
        if not found:
            lines.append(f"GOOGLE_ADS_REFRESH_TOKEN={refresh}")

        env_path.write_text("\n".join(lines).strip() + "\n")
        print(f"🔐 Wrote GOOGLE_ADS_REFRESH_TOKEN to {env_path}")

    print("\nNext steps:")
    print("  - Ensure these are set in your .env as well:")
    print("      GOOGLE_ADS_DEVELOPER_TOKEN=...")
    print("      GOOGLE_ADS_CLIENT_ID=" + client_id)
    print("      GOOGLE_ADS_CLIENT_SECRET=" + ("*" * min(6, len(client_secret))) + "...")
    print("      GOOGLE_ADS_LOGIN_CUSTOMER_ID=<your_MCC_digits_only>")
    print("  - Then run:  poetry run python -m src.cli accounts\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
