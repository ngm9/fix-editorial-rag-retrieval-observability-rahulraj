from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]
