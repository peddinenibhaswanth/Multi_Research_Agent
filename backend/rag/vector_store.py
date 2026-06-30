from typing import TypedDict
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from config import settings
from .embeddings import get_embedding_model


class ScrapedSource(TypedDict):
    url: str
    text: str


def get_vector_store(collection_name: str) -> Chroma:
    """
    Initializes and returns a Chroma vector store.

    This function sets up a persistent ChromaDB vector store using the directory
    specified in the application settings. It uses the pre-configured embedding
    model to handle vectorization of documents.

    Args:
        collection_name (str): The name of the collection within ChromaDB.
                               This helps in namespacing different sets of documents.

    Returns:
        Chroma: An instance of the Chroma vector store, ready for use.
    """
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=settings.CHROMA_PERSIST_DIR,
        embedding_function=get_embedding_model(),
    )
    return vector_store


def create_source_documents(sources: list[ScrapedSource]) -> list[Document]:
    """
    Converts scraped source objects into LangChain documents with source metadata.
    """
    return [
        Document(
            page_content=source["text"],
            metadata={"source": source["url"]},
        )
        for source in sources
        if source.get("text") and source.get("url")
    ]


def split_source_documents(documents: list[Document]) -> list[Document]:
    """
    Splits source documents into chunks using the shared RAG chunking settings.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
    )
    return text_splitter.split_documents(documents)


def add_texts_to_vector_store(texts: list[ScrapedSource], collection_name: str) -> Chroma:
    """
    Splits texts, creates documents, and adds them to the Chroma vector store.

    This function takes a list of raw text strings, splits them into manageable
    chunks using a text splitter, converts them into LangChain Document objects,
    and finally ingests them into the specified ChromaDB collection.

    Args:
        texts (list[ScrapedSource]): Scraped source objects to be added to the store.
        collection_name (str): The name of the collection to add the documents to.

    Returns:
        Chroma: The Chroma vector store instance after adding the new documents.
    """
    print(f"--- Splitting and adding {len(texts)} documents to collection '{collection_name}' ---")
    documents = create_source_documents(texts)
    
    # Split the documents into smaller chunks
    chunked_documents = split_source_documents(documents)
    
    print(f"--- Created {len(chunked_documents)} chunks ---")
    
    if not chunked_documents:
        raise ValueError(
            "No usable content could be extracted from the scraped sources. "
            "Try a different research topic or check if sources are accessible."
        )

    # Initialize the vector store
    vector_store = get_vector_store(collection_name)
    
    # Add the chunked documents to the vector store
    vector_store.add_documents(chunked_documents)
    
    print(f"--- Finished adding documents to collection '{collection_name}' ---")
    return vector_store
