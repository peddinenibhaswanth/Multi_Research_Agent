from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from .embeddings import embedding_model
from .vector_store import create_source_documents, get_vector_store, split_source_documents


def get_retriever(collection_name: str, documents: list):
    """
    Initializes and returns a retriever for the given ChromaDB collection.

    This function sets up a sophisticated retriever that combines the strengths
    of a keyword-based search (BM25) and a semantic search (vector-based).
    It uses an EnsembleRetriever to merge the results from both, aiming for
    high relevance and diversity in the retrieved documents.

    Args:
        collection_name (str): The name of the ChromaDB collection to retrieve from.
        documents (list): The list of documents to be used for the BM25 retriever.

    Returns:
        An instance of a LangChain retriever.
    """
    print(f"--- Initializing retriever for collection '{collection_name}' ---")

    # 1. Initialize the base vector store retriever
    vector_store = get_vector_store(collection_name)
    vector_retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    
    bm25_documents = split_source_documents(create_source_documents(documents))

    # 2. Initialize the BM25 retriever for keyword search
    bm25_retriever = BM25Retriever.from_documents(bm25_documents)
    bm25_retriever.k = 10

    # 3. Initialize the Ensemble Retriever
    # This retriever combines the results of the vector-based and keyword-based retrievers.
    # The weights parameter balances the contribution of each retriever.
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5]
    )

    # 4. Initialize a compressor pipeline for post-processing
    # This helps to filter out redundant documents from the retrieved set.
    redundant_filter = EmbeddingsRedundantFilter(embeddings=embedding_model)
    pipeline_compressor = DocumentCompressorPipeline(
        transformers=[redundant_filter]
    )

    # 5. Create the final contextual compression retriever
    # This wraps the ensemble retriever and applies the compression pipeline.
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=pipeline_compressor,
        base_retriever=ensemble_retriever
    )

    print("--- Retriever initialized successfully ---")
    return compression_retriever
