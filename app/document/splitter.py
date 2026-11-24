
from typing import List, Dict, Any


def split_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> List[str]:
    """
    Split document text into smaller chunks.

    Args:
        text: Extracted document text.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters.

    Returns:
        List of text chunks.
    """

    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    text = text.strip()

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(start + chunk_size, text_length)

        # Prefer breaking at a paragraph or sentence boundary
        if end < text_length:
            boundary = max(
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end)
            )

            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(end - chunk_overlap, start + 1)

    return chunks


def create_document_chunks(
    document: Dict[str, Any],
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Split an extracted document and attach metadata.
    """

    text = document.get("text", "")

    chunks = split_text(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    document_chunks = []

    for index, chunk in enumerate(chunks):

        document_chunks.append({
            "chunk_id": index,
            "file_name": document.get("file_name", "unknown"),
            "file_type": document.get("file_type", "unknown"),
            "chunk_text": chunk,
            "character_count": len(chunk),
            "word_count": len(chunk.split())
        })

    return document_chunks
