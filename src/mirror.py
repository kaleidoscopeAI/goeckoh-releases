import re


class MirrorNetwork:
    """
    Adaptive linguistic reflection engine.
    Converts second-person phrasing into first-person scaffolding.
    Adjusts complexity based on Global Coherence Level (GCL).
    """

    def __init__(self):
        self.transformations = [
            (r"\b(are|Are)\s+you\b", "am I"),
            (r"\b(y|Y)ou\b", "I"),
            (r"\b(y|Y)our\b", "my"),
            (r"\b(m|M)e\b", "you"),
            (r"\b(m|M)y\b", "your"),
        ]

    def reflect(self, text: str, gcl: float = 1.0) -> str:
        """
        Reflect text into first-person.
        If GCL is low (<0.5), use ultra-simple scripts.
        """
        if not text:
            return ""

        # Crisis Gating: If coherence is low, ignore complex intent and provide grounding
        if gcl < 0.4:
            return "I am safe. I can breathe."
        elif gcl < 0.6:
            # Simple correction only
            return "I can say: " + self._basic_transform(text)

        # High Coherence: Full reflection
        return self._basic_transform(text).capitalize()

    def _basic_transform(self, text: str) -> str:
        for pattern, replacement in self.transformations:
            text = re.sub(pattern, replacement, text)
        
        text = text.strip()
        # Vygotskian Scaffolding: Ensure "I" is the subject
        if len(text.split()) < 3 and "I" not in text:
            text = "I want " + text
        return text

