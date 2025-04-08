# Chat-Memory

#### Overview
The Chat Memory module is a key component of the ChatRagi chatbot application. Its purpose is to store, retrieve, and manage previous interactions between the user and the chatbot. By recalling relevant past conversations, the chatbot can provide more informed and context-aware responses.

---
#### Key Features
- **Memory Retrieval:**
	When a user submits a query, the module searches through previously stored interactions to find and return the most relevant memories. It scores each memory based on its importance and recency, ensuring that recent and significant conversations are prioritized.
- **Fetching All Memories:**
	The module can retrieve all stored chatbot interactions along with their associated metadata, such as the user query, timestamp, and whether the interaction is marked as important. This feature is useful for administrative and reporting purposes.
- **Memory Storage:**
	The module stores new interactions only if an identical conversation does not already exist. If a duplicate is found, it can update the importance flag of the existing memory instead of creating a new entry. This prevents unnecessary duplication and helps maintain an organized memory database.

---
#### How it Works?
1. **Retrieving Memory:**
	The module queries the database for interactions that match the user’s current query. It then calculates a score for each memory using a decay factor based on the time elapsed since the memory was stored and an importance weight. The top three relevant memories are returned.
2. **Fetching All Memories:**
	The module retrieves all chatbot interactions stored in the database and organizes them by timestamp, allowing users or administrators to review the history of conversations.
3. **Storing Memory:**
	When a new interaction occurs, the module first checks for duplicates. If the interaction is new, it is stored along with the user’s query, timestamp, and an indicator of its importance. If an identical interaction already exists, the module updates the existing record if necessary.

---
#### Benefits
- **Improved Context:**
	By recalling previous interactions, the chatbot can provide responses that take the conversation history into account, leading to a more natural and informed user experience.
- **Efficient Memory Management:**
	The system avoids duplicate entries and automatically prioritizes recent and important interactions, ensuring that the memory database remains organized and effective.
- **Transparency:**
	Clear logging and error handling make it easier to troubleshoot issues and understand how memory management is performed.

---
#### Summary
This module plays an essential role in enhancing the chatbot’s performance by ensuring that past interactions are efficiently managed and leveraged for better future responses.