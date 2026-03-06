import re


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    # split transcript text into overlapping chunks while trying to keep sentence boundaries

    if not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0:
        raise ValueError("overlap must be zero or greater")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()
    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]

        chunk_text = " ".join(chunk_words)

        # try to end chunk at sentence boundary
        if end < len(words):
            sentence_end = max(
                chunk_text.rfind("."),
                chunk_text.rfind("?"),
                chunk_text.rfind("!")
            )

            if sentence_end > len(chunk_text) * 0.5:
                chunk_text = chunk_text[: sentence_end + 1]

        chunks.append(chunk_text)

        if end >= len(words):
            break

        start += chunk_size - overlap

    return chunks