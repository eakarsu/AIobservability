"""Sample AI application that generates telemetry data."""
import random
import time
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "src"))

from aiobserve import ObserveClient

ENDPOINT = os.getenv("AIOBSERVE_ENDPOINT", "http://localhost:8000")
API_KEY = os.getenv("AIOBSERVE_API_KEY", "")

SAMPLE_PROMPTS = [
    "What is the capital of France?",
    "Explain quantum computing in simple terms.",
    "Write a Python function to sort a list.",
    "What are the benefits of cloud computing?",
    "Summarize the history of artificial intelligence.",
    "How does photosynthesis work?",
    "What is machine learning?",
    "Explain the difference between SQL and NoSQL databases.",
    "What is the theory of relativity?",
    "How do neural networks learn?",
]

SAMPLE_RESPONSES = [
    "The capital of France is Paris, a city known for the Eiffel Tower and rich cultural heritage.",
    "Quantum computing uses quantum bits (qubits) that can exist in multiple states simultaneously, enabling parallel computation.",
    "def sort_list(lst): return sorted(lst)",
    "Cloud computing offers scalability, cost-efficiency, reliability, and global accessibility for businesses.",
    "AI began in the 1950s with Turing's work, evolved through expert systems in the 80s, and now uses deep learning.",
    "Photosynthesis converts sunlight, water, and CO2 into glucose and oxygen using chlorophyll in plant cells.",
    "Machine learning is a subset of AI where systems learn patterns from data without explicit programming.",
    "SQL databases are relational with fixed schemas; NoSQL databases are non-relational with flexible schemas.",
    "Einstein's theory of relativity describes how space and time are interlinked and affected by gravity.",
    "Neural networks learn by adjusting connection weights through backpropagation based on prediction errors.",
]

MODELS = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "llama-3-70b"]
PROVIDERS = {"gpt-4": "openai", "gpt-3.5-turbo": "openai", "claude-3-opus": "anthropic", "claude-3-sonnet": "anthropic", "llama-3-70b": "meta"}

def simulate_ai_call(model: str):
    """Simulate an AI model call with realistic telemetry."""
    prompt = random.choice(SAMPLE_PROMPTS)
    response = random.choice(SAMPLE_RESPONSES)

    # Simulate latency based on model
    base_latency = {"gpt-4": 800, "gpt-3.5-turbo": 200, "claude-3-opus": 1000, "claude-3-sonnet": 400, "llama-3-70b": 600}
    latency = base_latency.get(model, 500) + random.gauss(0, 100)
    latency = max(50, latency)

    # Simulate token counts
    input_tokens = len(prompt.split()) * 1.3 + random.randint(5, 20)
    output_tokens = len(response.split()) * 1.3 + random.randint(10, 50)

    # Simulate occasional errors
    status = "success"
    error_msg = None
    if random.random() < 0.05:  # 5% error rate
        status = "error"
        error_msg = random.choice(["Rate limit exceeded", "Context length exceeded", "Model timeout", "Internal server error"])
        response = None

    # Simulate hallucination-prone responses
    if random.random() < 0.1 and response is not None:  # 10% hallucination chance
        response = response + " Additionally, this was first discovered in 1823 by Dr. Johannes Schmidt at the University of Heidelberg, " \
                              "as documented in the Journal of Advanced Sciences (vol. 42, pp. 156-189). " \
                              "Visit https://fake-source.example.com/paper/12345 for more details."

    return {
        "model_name": model,
        "model_provider": PROVIDERS.get(model, "unknown"),
        "input_text": prompt,
        "output_text": response,
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "latency_ms": round(latency, 2),
        "status": status,
        "error_message": error_msg,
        "metadata": {
            "temperature": round(random.uniform(0.0, 1.0), 2),
            "max_tokens": random.choice([256, 512, 1024, 2048]),
        },
        "tags": [f"model:{model}", "env:demo"],
    }


def main():
    client = ObserveClient(
        endpoint=ENDPOINT,
        api_key=API_KEY,
        batch_size=10,
        flush_interval=3.0,
    )

    print(f"Starting traffic generation to {ENDPOINT}")
    print(f"API Key: {API_KEY[:12]}...")

    try:
        event_count = 0
        while True:
            model = random.choice(MODELS)
            call_data = simulate_ai_call(model)
            client.log(**call_data)
            event_count += 1

            if event_count % 10 == 0:
                print(f"Sent {event_count} events")

            # Random delay between calls (0.5 - 3 seconds)
            time.sleep(random.uniform(0.5, 3.0))

    except KeyboardInterrupt:
        print(f"\nStopping. Total events sent: {event_count}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
