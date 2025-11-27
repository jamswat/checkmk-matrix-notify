#!/usr/bin/env python3
# Push Notification (using Matrix - Python)
#
# Script Name   : checkmk-matrix-notify.py
# Description   : Send checkmk notifications by Matrix (Python)
# Author        : James Wait 
# License       : BSD 3-Clause "New" or "Revised" License
# ======================================================================================

import os
import sys
import uuid

import requests


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

REQUEST_TIMEOUT = 15  # seconds

# Exit codes that CheckMK understands
EXIT_SUCCESS = 0
EXIT_RETRY = 1      # CheckMK will retry the notification
EXIT_FAILED = 2     # CheckMK will not retry

# Emoji indicators for each state
STATE_EMOJIS = {
    "OK": "✅",
    "UP": "✅",
    "WARN": "⚠️ ",
    "CRIT": "🚨",
    "DOWN": "🚨",
    "UNKNOWN": "❔",
}


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_env(name, default=""):
    """Get an environment variable, returning a default if not set."""
    return os.environ.get(name, default)


def get_required_env(name):
    """Get a required environment variable, exiting if not set."""
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(EXIT_FAILED)
    return value


def get_emoji(state):
    """Get the emoji for a given state, defaulting to ℹ️  if unknown."""
    return STATE_EMOJIS.get(state, "ℹ️ ")


# ------------------------------------------------------------------------------
# Message Building
# ------------------------------------------------------------------------------

def build_message():
    """
    Build the notification message from CheckMK environment variables.

    CheckMK sets NOTIFY_* environment variables containing all the
    information about the alert.

    Returns a tuple of (plain_text, html) message bodies.
    """
    # Determine if this is a host or service notification
    what = get_env("NOTIFY_WHAT", "HOST").upper()
    is_service = (what == "SERVICE")

    # Get common fields
    notification_type = get_env("NOTIFY_NOTIFICATIONTYPE")
    hostname = get_env("NOTIFY_HOSTNAME")
    site = get_env("OMD_SITE")
    timestamp = get_env("NOTIFY_SHORTDATETIME")

    # Get state-specific fields (different env vars for host vs service)
    if is_service:
        state = get_env("NOTIFY_SERVICESHORTSTATE")
        previous_state = get_env("NOTIFY_PREVIOUSSERVICEHARDSHORTSTATE")
        output = get_env("NOTIFY_SERVICEOUTPUT")
        service_name = get_env("NOTIFY_SERVICEDESC")
    else:
        state = get_env("NOTIFY_HOSTSHORTSTATE")
        previous_state = get_env("NOTIFY_PREVIOUSHOSTHARDSHORTSTATE")
        output = get_env("NOTIFY_HOSTOUTPUT")
        service_name = ""

    emoji = get_emoji(state)

    # Build plain text message (fallback for clients without HTML support)
    plain_lines = [
        f"{emoji} {what} {notification_type}: {hostname}",
    ]
    if is_service:
        plain_lines.append(f"Service: {service_name}")
    plain_lines.append(f"State: {previous_state} → {state}")
    plain_lines.append(f"Output: {output}")

    plain_text = "\n".join(plain_lines)

    # Build HTML message
    html_lines = [
        f"<p><b>{emoji} {what} {notification_type}</b></p>",
        f"<b>Host:</b> {hostname}",
    ]
    if is_service:
        html_lines.append(f"<b>Service:</b> {service_name}")
    html_lines.append(f"<b>State:</b> {previous_state} &rarr; <b>{state}</b>")
    html_lines.append(f"<b>Output:</b> <code>{output}</code>")
    html_lines.append(f"<p><small>Site: {site} | {timestamp}</small></p>")

    html_text = "<br>".join(html

def send_to_matrix(homeserver, access_token, room_id, plain_text, html_text):
    """
    Send a message to a Matrix room.

    Args:
        homeserver: Matrix server hostname (e.g., "matrix.example.org")
        access_token: Bot user's access token
        room_id: Target room ID (e.g., "!abc123:matrix.example.org")
        plain_text: Plain text version of the message
        html_text: HTML version of the message

    Returns:
        True on success, False on failure
    """
    # Generate a unique transaction ID (Matrix uses this to prevent duplicates)
    txn_id = str(uuid.uuid4())

    # Build the API URL
    # We need to URL-encode the room ID since it contains special characters
    encoded_room_id = requests.utils.quote(room_id, safe="")
    url = f"https://{homeserver}/_matrix/client/v3/rooms/{encoded_room_id}/send/m.room.message/{txn_id}"

    # Set up the request headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    # Build the message payload
    payload = {
        "msgtype": "m.text",
        "body": plain_text,
        "format": "org.matrix.custom.html",
        "formatted_body": html_text,
    }

    # Send the request
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        print(f"OK: Message sent successfully")
        return True

    except requests.exceptions.Timeout:
        print("ERROR: Request timed out", file=sys.stderr)
        return False

    except requests.exceptions.ConnectionError as err:
        print(f"ERROR: Could not connect to server: {err}", file=sys.stderr)
        return False

    except requests.exceptions.HTTPError as err:
        print(f"ERROR: HTTP error: {err}", file=sys.stderr)
        return False

    except requests.exceptions.RequestException as err:
        print(f"ERROR: Request failed: {err}", file=sys.stderr)
        return False


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def main():
    """Main entry point."""
    # Load configuration from environment variables
    homeserver = get_required_env("NOTIFY_PARAMETER_1")
    access_token = get_required_env("NOTIFY_PARAMETER_2")
    room_id = get_required_env("NOTIFY_PARAMETER_3")

    # Build the notification message
    plain_text, html_text = build_message()

    # Send to Matrix
    success = send_to_matrix(homeserver, access_token, room_id, plain_text, html_text)

    # Exit with appropriate code
    if success:
        sys.exit(EXIT_SUCCESS)
    else:
        sys.exit(EXIT_RETRY)


if __name__ == "__main__":
    main()
