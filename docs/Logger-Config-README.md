# Logger-Config - Configuration File

#### Overview
The **logger_config.py** file is responsible for configuring the logging mechanism used throughout the ChatRagi chatbot application. This configuration ensures that important events and errors are recorded, which helps with monitoring the application’s behavior and troubleshooting any issues that may arise.

---
#### How it Works?
1. **Logging Setup:**
	The module defines a function called setup_logger() that sets the logging level, format, and output destinations. The log messages include a timestamp, the level of the log (such as INFO or DEBUG), the name of the logger, and the actual message.
2. **Output Destinations:**
	Log messages are written to both a file and the console. The file path is determined by the configuration settings, ensuring that logs are persisted and can be reviewed later if needed.
3. **Logger Instance:**
	A logger instance named “ChatRagi” is created and made available for use in the rest of the application. This allows consistent logging across different modules.

---
#### Benefits
- **Improved Monitoring:**
	With detailed logging, administrators can easily monitor the application’s behavior and performance.
- **Efficient Troubleshooting:**
	In the event of an error, the logs provide clear and timestamped information that can help developers diagnose and fix problems quickly.
- **Consistent Reporting:**
	The uniform log format ensures that all log messages are consistent, making them easier to read and analyze.