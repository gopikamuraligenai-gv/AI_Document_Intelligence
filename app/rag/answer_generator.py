
import ollama

from app.rag.prompt import build_rag_prompt


class AnswerGenerator:

    def __init__(self, model: str = "llama3.2"):

        self.model = model

    def generate_answer(
        self,
        query: str,
        retrieved_chunks: list
    ) -> str:

        if not retrieved_chunks:
            return (
                "The answer is not available "
                "in the provided document."
            )

        prompt = build_rag_prompt(
            query=query,
            retrieved_chunks=retrieved_chunks
        )

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

