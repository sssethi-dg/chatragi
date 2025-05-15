# Running LLMs Locally

Follow the steps listed below to set up **phi4** and **nomic-embed-text**, or any other open-source model supported by **Ollama** on your local machine.

## Step 1: Download and Install Ollama

1. **Visit the Ollama Website:**
	-  Open your browser and navigate to [https://ollama.com/download](https://ollama.com/download)
2. **Select the Appropriate Version:**
	- Choose the version of Ollama suitable for your operating system (Windows, macOS, or Linux).
3. **Download and Install:**
	- Download the installer and double-click it to begin the installation.
	- Follow the on-screen instructions to complete the setup.
4. **Verify Installation:**
	- After installation, look for the Ollama icon/logo in the status bar to confirm successful setup.

---

## Step 2: Add Microsoft Phi-4 Using the Terminal

1. **Visit the Ollama Library**
	- Open your browser and navigate to the [Ollama Model Library](https://ollama.com/library).
2. **Select the Phi-4 Model**
	- Locate **`phi4`**, the 14B parameter model released by Microsoft.
	- Recommended version: `phi4:14b` (default Q4_K_M quantization) ([Direct Link](https://ollama.com/library/phi4)).
	- Optional: `phi4:14b-q8_0` (Q8_0 quantization) — offers higher precision, but requires more memory (~15 GB) ([Direct Link](https://ollama.com/library/phi4:14b-q8_0)).
3. **Install the Model**
	- Open a terminal and run one of the following commands:
```bash
# Default (Q4_K_M, 4-bit quantized)
ollama run phi4:14b

# Optional (Q8_0, 8-bit quantized — larger & slower to load)
ollama run phi4:14b-q8_0
```
4. **Verify Installation**
	- Wait for the download to complete. You’ll be dropped into a test chat session.
	- To exit the session, type:
```bash
/bye
```

---

## Step 3: Add NOMIC nomic-embed-text Using the Terminal

1. **Visit the Ollama Library:**
	- Open your browser and go to the [Ollama Library](https://ollama.com/library).
2. **Select the Model:**
	- Locate and select **nomic-embed-text** ([Direct Link](https://ollama.com/library/nomic-embed-text)). 
	- _nomic-embed-text is a high-performing open embedding model with a large token context window._
3. **Install the Model:**
	- Open the terminal and run the following command to install the nomic-embed-text model:
```bash
ollama pull nomic-embed-text
```
4. **Verify Installation:**
	- Wait for the process to complete, then type the following command to exit:
```bash
/bye
```
---

## Step 4: (Optional) Benchmark Model Performance on Your Machine

If you’re unsure how a specific model will perform on your hardware, ChatRagi includes a GPU benchmarking utility:
```bash
python test/gpu_benchmark.py
```

This script benchmarks a given LLM with different num_gpu_layers settings and logs response times to a CSV.

### Sample Configuration

Edit the **gpu_benchmark.py** file to test different models or GPU layer settings by modifying the following lines:
```python
LLM_MODEL_NAME = "phi4:14b"  # or "llama3.2:3b"
GPU_LAYER_OPTIONS = [1, 10, 20, 30]
```

This helps determine the best balance of speed and quality based on your machine.

---

## Performance Tip

If you’re on a lower-spec device, start with a smaller model like:
```bash
ollama run llama3.2:3b
```

This allows you to test basic ChatRagi functionality without long load times or memory pressure.

Once everything runs smoothly, feel free to move up to more capable models like **phi4:14b**.

---

## Optional  

If you prefer to run smaller models locally, check out the full list of supported models on [Ollama's website](https://ollama.com/search)

---

## ⚠️ Limitations of Smaller Models

Smaller LLMs like `llama3.2:3b` or `deepseek-r1:1.5b` are great for testing and faster response times — especially on lower-spec machines. But keep in mind:

- They may **lack reasoning depth** for complex questions
- Answers can be **incomplete or overly generic**
- Markdown formatting and persona tone adherence may vary
- May **struggle with long context windows** or nuanced instructions

> 💡 For better response quality and tone control, models like `phi4` or `phi4:14b-q8_0` are recommended — especially when running on machines with 16+ GB of RAM and Apple Silicon (M1/M2/M3) or equivalent.

You can always start small and upgrade later once you’ve verified your setup.