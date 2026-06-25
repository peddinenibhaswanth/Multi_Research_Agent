from langchain_huggingface import HuggingFaceEmbeddings
from config import settings

# Don't load at import time — load only when first needed
_embedding_model = None

def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        print("--- Loading embedding model (first time only) ---")
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME,
            encode_kwargs={"normalize_embeddings": True},
        )
        print("--- Embedding model loaded successfully ---")
    return _embedding_model