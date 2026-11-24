
from app.llm.ollama_client import OllamaClient


def test_ollama_grammar_correction():

    client = OllamaClient(model="llama3.2:latest")

    original_text = (
        "She go to school everyday. "
        "He are a good boy."
    )

    print("\n========== OLLAMA GRAMMAR TEST ==========")

    print("\nOriginal Text:")
    print(original_text)

    corrected_text = client.correct_grammar(original_text)

    print("\nCorrected Text:")
    print(corrected_text)

    assert corrected_text.strip(), "Empty correction received."

    print("\nOLLAMA TEST: PASSED")


if __name__ == "__main__":
    test_ollama_grammar_correction()
