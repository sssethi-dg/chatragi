
Follow the steps listed below to set up **phi4** and **nomic-embed-text**, or any other open-source model supported by **Ollama** on your local machine.

**Step 1: Download and Install Ollama**
1. **Visit the Ollama Website:**
	-  Open your browser and navigate to [https://ollama.com/download](https://ollama.com/download)
2. **Select the Appropriate Version:**
	- Choose the version of Ollama suitable for your operating system (Windows, macOS, or Linux).
3. **Download and Install:**
	- Download the installer and double-click it to begin the installation.
	- Follow the on-screen instructions to complete the setup.
4. **Verify Installation:**
	- After installation, look for the Ollama icon/logo in the status bar to confirm successful setup.

**Step 2: Add Microsoft Phi-4 Using the Terminal**
1. **Visit the Ollama Library:**
	- Open your browser and go to the [Ollama Library](https://ollama.com/library).
2. **Select the Model:**
	- Locate and select **phi4** ([Direct Link](https://ollama.com/library/phi4)). 
	- _Phi-4 is a 14B parameter, state-of-the-art open model from Microsoft._
3. **Install the Model:**
	- Open the terminal and run the following command to install the Phi-4 14B model:
```
ollama run phi4
```
4. **Verify Installation:**
	- Wait for the process to complete, then type the following command to exit:
```
/bye
```

**Step 3: Add NOMIC nomic-embed-text Using the Terminal**
1. **Visit the Ollama Library:**
	- Open your browser and go to the [Ollama Library](https://ollama.com/library).
2. **Select the Model:**
	- Locate and select **nomic-embed-text** ([Direct Link](https://ollama.com/library/nomic-embed-text)). 
	- _nomic-embed-text A high-performing open embedding model with a large token context window._
3. **Install the Model:**
	- Open the terminal and run the following command to install the nomic-embed-text model:
```
ollama pull nomic-embed-text
```
4. **Verify Installation:**
	- Wait for the process to complete, then type the following command to exit:
```
/bye
```

> [!tip] Optional  
    > If you prefer to run smaller models locally, check out the list of available models listed on the [Ollama's website](https://ollama.com/search)
