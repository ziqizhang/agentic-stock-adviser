"""E2E test for the API — starts the server, sends messages, verifies SSE events.

Run with: poetry run python scripts/e2e_api_test.py
Requires OPENAI env vars to be set (calls the real LLM).
"""

import json
import threading
import time

import httpx
import uvicorn

from stock_adviser.api.app import create_app


def start_server(app, port: int) -> threading.Thread:
    """Start uvicorn in a background thread."""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1)  # Wait for server to start
    return thread


def test_health(base_url: str) -> None:
    print("Test: GET /health")
    r = httpx.get(f"{base_url}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print("  PASS")


def test_chat_and_stream(base_url: str) -> None:
    print("Test: POST /chat + GET /stream (specific price request)")
    session_id = "e2e-test-1"

    # Collect SSE events in background
    events: list[dict] = []
    stop = threading.Event()

    def collect_events():
        with httpx.stream("GET", f"{base_url}/stream/{session_id}", timeout=60) as r:
            for line in r.iter_lines():
                if stop.is_set():
                    break
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        events.append(data)
                        print(f"  SSE: {data['type']}")
                    except json.JSONDecodeError:
                        pass

    collector = threading.Thread(target=collect_events, daemon=True)
    collector.start()
    time.sleep(0.5)

    # Send a specific request that should trigger tools
    r = httpx.post(f"{base_url}/chat", json={"session_id": session_id, "message": "What is the price of AAPL?"})
    assert r.status_code == 202
    print(f"  POST /chat: {r.status_code}")

    # Wait for agent to finish
    time.sleep(15)
    stop.set()

    # Verify we got expected event types
    event_types = [e["type"] for e in events]
    print(f"  Event types received: {event_types}")

    assert "token" in event_types, "Expected token events from LLM"
    assert "tool_start" in event_types, "Expected tool_start event"
    print("  PASS")


def main():
    print("=" * 60)
    print("E2E API Test")
    print("=" * 60)

    app = create_app()
    port = 18765
    base_url = f"http://127.0.0.1:{port}"

    start_server(app, port)

    test_health(base_url)
    test_chat_and_stream(base_url)

    print("\n" + "=" * 60)
    print("All E2E API tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
