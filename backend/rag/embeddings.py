from langchain_huggingface import HuggingFaceEmbeddings

from config import settings

embedding_model = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL_NAME,
    encode_kwargs={"normalize_embeddings": True},
)
