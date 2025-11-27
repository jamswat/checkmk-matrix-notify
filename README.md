# CheckMK Matrix Notification Script

A Python notification script for [CheckMK](https://checkmk.com/) that sends alerts to [Matrix](https://matrix.org/) chat rooms.

Inspired by [Hagbear's Checkmk Matrix script](https://github.com/Hagbear/checkmk-matrix-notify) but rewritten in Python.


![checkmk](https://github.com/user-attachments/assets/bf70eb95-7805-4c33-8158-780fea57d1df)

## Overview

This script enables CheckMK to send host and service notifications directly to Matrix rooms using the Matrix Client-Server API. It supports both plain text and HTML-formatted messages with emoji indicators for different alert states.


## Requirements

- Python 3.6+
- CheckMK (tested with Raw 2.4.0p16)
- A Matrix account with an access token

## Installation

### 1. Install the Script

Copy the script to your CheckMK notification plugins directory:

```bash
# Switch to your OMD site user
su - mysite

#Enter the notification directory
~/local/share/check_mk/notifications/

#wget the script
wget https://github.com/jamswat/checkmk-matrix-notify/raw/refs/heads/main/checkmk-matrix-notify.py

# Make it executable
chmod +x ~/local/share/check_mk/notifications/checkmk-matrix-notify.py
```

> **Note**: Custom notification scripts should be saved in `~/local/share/check_mk/notifications`. They will be automatically found and made available for selection in notification rules ([CheckMK Documentation](https://docs.checkmk.com/latest/en/notifications.html)).


### 2. Create a Matrix Bot Account

You'll need a Matrix account to send notifications. There are several ways to obtain an access token:

#### Option A: Using Element

1. Create a new account for your bot on your Matrix homeserver
2. Log in using Element (web or desktop)
3. Go to **Settings → Help & About → Advanced**
4. Click to reveal and copy the **Access Token**

> ⚠️ **Important**: Do not log out of this session, or the access token will be invalidated.

#### Option B: Using the API

```bash
curl -X POST \
  --header 'Content-Type: application/json' \
  -d '{
    "identifier": { "type": "m.id.user", "user": "YOUR_BOT_USERNAME" },
    "password": "YOUR_BOT_PASSWORD",
    "type": "m.login.password"
  }' \
  'https://YOUR_HOMESERVER/_matrix/client/v3/login'
```

The response will contain your `access_token`.

### 3. Get the Room ID

1. In Element, open the room where you want notifications sent
2. Go to **Room Settings → Advanced**
3. Copy the **Internal room ID** (format: `!abc123:matrix.example.org`)

> **Note**: Make sure your bot user has been invited to and joined the room before sending notifications.

## CheckMK Configuration

### 1. Create a Notification Rule

1. Navigate to **Setup → Events → Notifications**
2. Click **Add rule**
3. Configure the notification method:
   - **Notification Method**: Select `Push Notification (using Matrix - Python)`
   - **Parameter 1**: Matrix homeserver (e.g., `matrix.example.org`)
   - **Parameter 2**: Bot access token
   - **Parameter 3**: Room ID (e.g., `!abc123:matrix.example.org`)

4. Configure conditions as needed (hosts, services, time periods, etc.)
5. Save and activate changes

### 2. Test the Notification

You can test your notification setup:

1. Go to **Setup → Events → Notifications**
2. Click **Test notifications**
3. Select a host and optionally a service
4. Click **Test notification**

## How It Works

### Matrix API Integration

The script uses the Matrix Client-Server API to send messages. It sends a `PUT` request to the room message endpoint:

```
PUT /_matrix/client/v3/rooms/{roomId}/send/m.room.message/{txnId}
```

Each message includes both plain text and HTML-formatted content using the `org.matrix.custom.html` format, ensuring compatibility with all Matrix clients ([Matrix Client-Server API Specification](https://spec.matrix.org/latest/client-server-api/)).

### Transaction IDs

The script generates a unique transaction ID (UUID) for each message. This allows the Matrix server to deduplicate messages if a request is retried, preventing duplicate notifications.

### CheckMK Environment Variables

CheckMK passes notification data through environment variables prefixed with `NOTIFY_`. The script reads:

| Variable | Description |
|----------|-------------|
| `NOTIFY_WHAT` | Type of notification (HOST or SERVICE) |
| `NOTIFY_NOTIFICATIONTYPE` | e.g., PROBLEM, RECOVERY |
| `NOTIFY_HOSTNAME` | Name of the affected host |
| `NOTIFY_SERVICEDESC` | Service description (service alerts only) |
| `NOTIFY_HOSTSHORTSTATE` | Host state (UP, DOWN, etc.) |
| `NOTIFY_SERVICESHORTSTATE` | Service state (OK, WARN, CRIT, etc.) |
| `NOTIFY_HOSTOUTPUT` / `NOTIFY_SERVICEOUTPUT` | Check output |
| `OMD_SITE` | CheckMK site name |
| `NOTIFY_PARAMETER_1/2/3` | Custom parameters (homeserver, token, room) |

### Exit Codes

The script uses CheckMK's standard exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success - notification sent |
| `1` | Retry - temporary failure, CheckMK will retry |
| `2` | Failed - permanent failure, no retry |


## Troubleshooting

### Check the Notification Log

```bash
tail -f ~/var/log/notify.log
```

## License

BSD 3-Clause "New" or "Revised" License

## References

- [CheckMK Notification Documentation](https://docs.checkmk.com/latest/en/notifications.html)
- [Matrix Client-Server API Specification](https://spec.matrix.org/latest/client-server-api/)
