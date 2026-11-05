import json
import os
import urllib.error
import urllib.parse
import urllib.request

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SEEN_FILE = os.environ.get("SEEN_FILE", "seen.json")


def telegram_send(message: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    request = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram HTTP {e.code}: {body}") from e

    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def load_seen() -> set:
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen(seen: set) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False)


def check_vox_availability() -> list[dict]:
    """
    TODO: Implement official VOX showtime/seat availability checking.

    Return a list of confirmed matches, for example:
      [
        {
          "branch": "City Centre Almaza",
          "showtime": "7:30 PM",
          "adjacent_seats": True,
          "booking_url": "https://..."
        }
      ]

    Do not report seats as available unless the official booking flow
    confirms two adjacent seats.
    """
    return []


def main() -> None:
    # Optional connectivity test: run with SEND_TEST=1
    if os.environ.get("SEND_TEST") == "1":
        telegram_send(
            "✅ Doomsday Ticket Alert is connected!\n"
            "Next step: connect the official VOX availability checker."
        )
        print("Telegram test message sent successfully.")

    matches = check_vox_availability()
    if not matches:
        print("No confirmed matches (or VOX checker not configured yet).")
        return

    seen = load_seen()

    for match in matches:
        if match.get("adjacent_seats") is not True:
            continue

        key = f"{match.get('branch', '?')}|{match.get('showtime', '?')}"
        if key in seen:
            continue

        try:
            telegram_send(
                "🎟️ Avengers: Doomsday ticket alert!\n"
                f"Branch: {match.get('branch', 'Unknown')}\n"
                f"Showtime: {match.get('showtime', 'Unknown')}\n"
                "Two adjacent seats: confirmed\n"
                f"Booking: {match.get('booking_url', 'Open VOX website')}"
            )
            seen.add(key)
            save_seen(seen)
        except Exception as e:
            print(f"Failed to send alert for {key}: {e}")


if __name__ == "__main__":
    main()
