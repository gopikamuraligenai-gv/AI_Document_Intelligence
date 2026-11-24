
def build_rag_prompt(query: str, retrieved_chunks: list) -> str:

    context = "\n\n".join(
        chunk["chunk_text"]
        for chunk in retrieved_chunks
    )

    prompt = f"""
You are an AI Document Intelligence Assistant.

Answer the user's question using ONLY the provided document context.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. If the answer is not available in the context,
   respond with:
   "The answer is not available in the provided document."
4. Provide a clear and concise answer.
5. Mention relevant supporting information.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER:
"""

    return prompt
