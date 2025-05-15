# ChangeLog

## [v1.1.0] — 2025-04-28

🎯 **New Features**
- **Persona-Based Tone Variations**  
  - Users can now select from three response styles:  
    - 🧠 Neutral – clear and balanced  
    - 💼 Professional – formal and structured  
    - 😄 Witty – playful and conversational  
  - Tone selection available in both Web UI and CLI

---

🛠️ **Core Improvements**
- **Structured Prompting Refined**  
  - Professional tone now consistently uses Markdown formatting with **Summary**, **Details**, and **Tips** sections.
- **Improved Markdown Output**  
  - Enhanced formatting for nested bullet points and better Markdown consistency.
- **Reduced LLM Drift**  
  - Stronger prompt anchoring discourages off-topic responses, especially in Neutral and Professional tones.

---

🎨 **UI & UX Enhancements**
- **Modernized Persona Selector**  
  - Redesigned dropdown styling to match ChatRagi's clean visual aesthetic.
  - Fully styled for dark mode compatibility.
- **Simplified Tone Options**  
  - Removed "Casual" tone (merged with Neutral) to streamline tone behavior and reduce overlap.

---

⚙️ **Backend Enhancements**
- The `/ask` endpoint now supports persona-specific prompt injection.
- Neutral versions of answers are stored in memory, ensuring consistent recall and minimizing drift.

---

📄 **Deferred to Future Releases**
These features were scoped but moved to `v1.2+`:
- `DEBUG_MODE_UI` toggle for advanced frontend debugging.
- `STRICT_MARKDOWN_MODE` flag for stricter output structure.
- Advanced LLM Drift Detection (post-processing level).
- Expanded system documentation and quick start refinements.

📅 **Documentation Completed in v1.1.0**
  • Finalized README with revised Web App, Persona, and System Overview sections.
  • Completed Architecture Overview and detailed Mermaid flow diagrams.
  • Updated File Watcher, App Backend, and Config documentation with markdown captions and ALT text.

---

✅ **v1.1.0** delivers customizable response tones, improved Markdown structuring, and tighter answer alignment — making ChatRagi more **personalized**, and **precise**.

---