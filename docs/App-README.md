

#### App

> [!info] Overview
> 
> The ChatRagi web backend is the core component of the ChatRagi chatbot application. It provides a set of HTTP endpoints to serve the chatbot’s home page, process user queries, store conversation memory, refresh the document index, and list stored documents and conversation memories.

---

> [!question] How it Works?
> 
> 1. **Home Page Rendering:**
> 	When users visit the homepage, the application renders an HTML page that serves as the interface for interacting with the chatbot.
> 2. **Query Processing:**
> 	Users can submit their queries via the interface. The backend processes these queries by forwarding them to an AI query engine. The response from the AI is formatted using Markdown for better readability and returned to the user.
> 3. **Memory Storage:**
> 	After processing a query, the chatbot stores the interaction (both the user’s query and the AI’s response) in a memory database. This allows the system to refer back to previous conversations to provide context-aware responses in the future.
> 4. **Index Refreshing:**
> 	The system periodically refreshes the document index to ensure that any new documents are included. This ensures that the AI has access to the most up-to-date information for generating responses.
> 5. **Document and Memory Listing:**
> 	The backend also provides endpoints to list all indexed documents and all stored memories. This feature helps track and manage the data that the chatbot has processed over time.

--- 

> [!success] Benefits
> 
> - **Efficient Data Retrieval:**
> 	The system indexes documents and stores conversations, which allows the AI to quickly find relevant information to answer queries.
> - **Context Awareness:**
> 	By storing conversation memory, the chatbot can provide responses that take into account previous interactions, leading to more coherent and contextually appropriate answers.
> - **Robust and Maintainable:**
> 	The application includes structured logging and exception handling to ensure reliability and ease of maintenance. Any issues can be quickly identified through detailed log entries.


