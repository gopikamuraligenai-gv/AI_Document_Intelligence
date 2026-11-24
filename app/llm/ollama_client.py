
import ollama


class OllamaClient:

    def __init__(self, model="llama3.2:latest"):
        self.model = model

    def generate(self, prompt: str) -> str:

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )

            return response["response"].strip()

        except Exception as error:
            raise RuntimeError(
                f"Ollama generation failed: {error}"
            ) from error

    def correct_grammar(self, text: str) -> str:

        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        prompt = f"""
You are a professional English grammar correction assistant.

Correct the grammar and spelling in the following text.

Instructions:
1. Preserve the original meaning.
2. Do not add new information.
3. Do not summarize the content.
4. Preserve paragraph structure.
5. Return only the corrected text.

Text:
{text}
"""

        return self.generate(prompt)
