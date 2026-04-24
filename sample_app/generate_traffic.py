"""Generate a burst of sample traffic for testing."""
import sys
import os
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "src"))

from aiobserve import ObserveClient
from app import simulate_ai_call, MODELS

ENDPOINT = os.getenv("AIOBSERVE_ENDPOINT", "http://localhost:8000")
API_KEY = os.getenv("AIOBSERVE_API_KEY", "")
NUM_EVENTS = int(os.getenv("NUM_EVENTS", "500"))

def main():
    client = ObserveClient(
        endpoint=ENDPOINT,
        api_key=API_KEY,
        batch_size=50,
        flush_interval=2.0,
    )

    print(f"Generating {NUM_EVENTS} events to {ENDPOINT}")

    for i in range(NUM_EVENTS):
        model = random.choice(MODELS)
        call_data = simulate_ai_call(model)

        # Add some drift simulation after first 250 events
        if i > NUM_EVENTS // 2:
            call_data["latency_ms"] *= 1.5  # Latency increases
            call_data["output_tokens"] = int(call_data.get("output_tokens", 50) * 1.3)

        client.log(**call_data)

        if (i + 1) % 50 == 0:
            print(f"Progress: {i + 1}/{NUM_EVENTS}")
            client.flush()
            time.sleep(0.1)

    client.close()
    print("Done! Traffic generation complete.")

if __name__ == "__main__":
    main()
