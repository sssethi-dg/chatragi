import csv
import time

from langchain_ollama import OllamaLLM

# === Configuration Section ===

# List of GPU layer settings to benchmark.
# Increasing num_gpu_layers shifts more computation to GPU.
GPU_LAYER_OPTIONS = [1, 10, 20, 30]

# Prompt sent to the model for performance comparison.
TEST_PROMPT = "What's Goodhart's Law?"

# Name of the model to benchmark.
# Must already be pulled via `ollama pull <model-name>`.
# Options: "phi4:14b-q8_0", "llama3.2:3b", "qwq:32b", "phi4:14b-q4_K_M"
LLM_MODEL_NAME = "phi4:14b-q8_0"

# Output file where benchmarking results will be stored.
CSV_FILENAME = "gpu_layer_benchmark_results.csv"


def benchmark_model_response():
    """
    Benchmarks model response time for various `num_gpu_layers` settings
    using OllamaLLM.

    Sends a fixed prompt to a specified model with varying GPU acceleration
    settings, logs the response time and a preview of the model's output,
    and saves results to a CSV file.

    Raises:
        Any exceptions encountered while invoking the model are caught and
        logged per test.
    """

    # Open CSV file and write the header row
    with open(CSV_FILENAME, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "num_gpu_layers",
                "response_time_sec",
                "response_preview",
                LLM_MODEL_NAME,
            ]
        )

        # Iterate through each GPU layer configuration
        for num_layers in GPU_LAYER_OPTIONS:
            print(f"\n🔧 Testing with num_gpu_layers = {num_layers}...")

            # Initialize OllamaLLM with specified model and hardware settings
            # num_gpu_layers - Number of layers to offload to GPU
            # quantization - Reduces memory usage (at some accuracy cost)
            llm = OllamaLLM(
                model=LLM_MODEL_NAME,
                request_timeout=360.0,
                options={
                    "num_gpu_layers": num_layers,
                    "quantization": "4bit",
                },
            )

            start_time = time.time()
            try:
                # Send prompt and measure response time
                response = llm.invoke(TEST_PROMPT)
                elapsed_time = time.time() - start_time

                # Display results to console
                print(f"🧠 Response: {response.strip()}")
                print(f"⏱️ Time taken: {elapsed_time:.2f} seconds")

                # Write result to CSV (preview first 100 chars of response)
                writer.writerow(
                    [
                        num_layers,
                        round(elapsed_time, 2),
                        response.strip()[:100],
                    ]
                )

            except Exception as e:
                # Log any errors encountered with this config
                print(f"❌ Error at num_gpu_layers={num_layers}: {e}")
                writer.writerow([num_layers, "ERROR", str(e)[:100]])


if __name__ == "__main__":
    """
    Main function to run the GPU benchmark test.
    """
    benchmark_model_response()
