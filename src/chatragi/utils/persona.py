"""
Persona Tone Utilities

Provides persona tone enumeration and functions to adjust chatbot input
prompts accordingly.
"""

from enum import Enum


class PersonaTone(str, Enum):
    """
    Enumeration of supported persona tones for chatbot responses.
    """

    DEFAULT = "default"
    PROFESSIONAL = "professional"
    WITTY = "witty"


def apply_persona_tone(text: str, tone: PersonaTone) -> str:
    """
    Adjusts the user query text based on the selected persona tone.

    Args:
        text (str): Original user query.
        tone (PersonaTone): Selected persona tone.

    Returns:
        str: Modified query text to influence LLM response style.
    """
    if tone == PersonaTone.PROFESSIONAL:
        return f"As a professional, I would explain it like this:\n\n{text}"
    elif tone == PersonaTone.WITTY:
        return f"Alright, let's jazz this up with some wit:\n\n{text}"
    else:
        return text  # Default, no adjustment
