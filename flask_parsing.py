import os
import sys
import requests  # Third-party HTTP client library for Python

FLASK_API_URL = os.environ.get(
    "ANALYZER_URL", "http://localhost:5000/analyze"
)
BATCH_SIZE = 3


def parse_log_line(line: str) -> dict:
    """Parses standard log format: TIMESTAMP SEVERITY [SERVICE] MESSAGE."""
    parts = line.strip().split(" ", 4)
    if len(parts) < 5:
        return None
    return {
        "severity": parts[2],
        "service": parts[3].strip("[]"),
        "message": parts[4],
        "raw_line": line.strip(),
    }


def send_batch_to_flask(batch_logs: list):
    """Combines batched logs and sends them over HTTP POST to the Flask service."""
    combined_text = "\n".join(batch_logs)

    payload = {"content": combined_text}

    try:
        print(
            f"📡 Sending batch of {len(batch_logs)} error logs to Flask API..."
        )
        response = requests.post(
            FLASK_API_URL, json=payload, timeout=10
        )  # 10s timeout guard

        # Check if HTTP status code is 200 OK
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Gemini AI Analysis Received:")
            print(result.get("analysis"))
        else:
            print(
                f"❌ Flask API Error [{response.status_code}]: {response.text}"
            )

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Is Flask running at '{FLASK_API_URL}'?")
    except requests.exceptions.Timeout:
        print("❌ Request Timed Out: Flask/Gemini took too long to respond.")


def main():
    log_file = os.environ.get("LOG_FILE", "server.log")

    if not os.path.exists(log_file):
        print(f"❌ Error: File '{log_file}' not found.")
        sys.exit(1)

    error_batch = []

    print(f"🔍 Monitoring '{log_file}' for incident batching...\n")

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed and parsed["severity"] in ("ERROR", "CRITICAL"):
                error_batch.append(parsed["raw_line"])

                # If batch reaches limit, flush it to the API
                if len(error_batch) >= BATCH_SIZE:
                    send_batch_to_flask(error_batch)
                    error_batch.clear()  # Empty the buffer for the next batch

    # Flush remaining logs in buffer if any exist
    if error_batch:
        print("\n🧹 Flushing remaining logs in batch buffer...")
        send_batch_to_flask(error_batch)


if __name__ == "__main__":
    main()