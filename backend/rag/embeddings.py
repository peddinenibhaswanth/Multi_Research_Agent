from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import settings

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("--- Initializing Google embedding model ---")
        _embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",  
            google_api_key=settings.GOOGLE_API_KEY
        )
        print("--- Google embedding model ready ---")
    return _embedding_model