# Config - ChatRagi Configuration File

#### Overview

The **config.py** file is the central configuration module for the ChatRagi chatbot application. It sets up various parameters that control how the chatbot operates. These settings include file storage locations, artificial intelligence (AI) model selection, performance optimizations, and memory management. This document explains these configurations in simple terms.

---
#### Key Sections and Their Purpose
1. **General Configuration**
	This section defines where the application stores its data, archives processed files, persists chatbot knowledge, and logs activity. It ensures that required folders exist before the application starts.
2. **LLM Model Configuration**
	Here, the file specifies the AI model used by the chatbot. The default model is set to “phi4:latest”, but it can be changed by adjusting the environment variables. The model is loaded with settings optimized for performance.
3. **Embedding Model Configuration**
	This section sets up the model that converts text into numerical data (embeddings) so that the chatbot can understand and compare document content. If the primary embedding model fails, a fallback model from Hugging Face is used.
4. **LLM Query Optimization**
	These settings determine how much text the chatbot processes at one time and how many tokens it generates in its responses. This helps balance speed with the quality and detail of the chatbot’s answers.
5. **Memory Management**
	The chatbot is designed to remember recent conversations. This section controls how long these memories are kept and limits the length of user inputs to ensure optimal performance.
6. **Adaptive Chunking**
	Documents are automatically split into smaller, manageable chunks for efficient processing. The configuration allows for different chunk sizes and overlap ratios based on the document’s length.
7. **Debugging & Performance Logging**
	If debug mode is enabled, the configuration prints detailed information about the settings being used. This information helps with troubleshooting and optimizing the chatbot.

---
#### How it Works?

- When ChatRagi starts, it reads **config.py** to initialize settings.
- It checks for the existence of necessary folders and creates them if they do not exist.
- The file then loads the AI model and the embedding model, applying performance optimizations.
- It sets global settings so that other parts of the application can access these configurations.
- Finally, it configures parameters that control the behavior of the chatbot during runtime, such as how much text is processed at once and how many document chunks are retrieved during queries.

---
#### Summary
This configuration file is essential for ensuring that ChatRagi operates efficiently, accurately, and in a way that meets the performance requirements of the business.