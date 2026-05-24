from enum import Enum


class ModelProvider(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"
