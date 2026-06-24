from langchain_core.runnables import RunnablePassthrough
from rag.retriever import get_retriever
from agent.prompts import report_generation_prompt
from models.schemas import ResearchReport
from llm import llm_with_fallback


def format_docs(docs):
    """
    Formats the retrieved documents into a single string for the prompt.
    """
    return "\n\n".join(
        f"Source URL: {doc.metadata.get('source', 'N/A')}\nContent: {doc.page_content}"
        for doc in docs
    )


def get_report_generation_chain(collection_name: str, documents: list):
    """
    Creates and returns a LangChain Expression Language (LCEL) chain for generating
    the final research report.

    This chain performs the following steps:
    1. Retrieves relevant documents from the vector store based on the user's topic.
    2. Formats the retrieved documents into a single string.
    3. Populates the report generation prompt with the topic and formatted context.
    4. Calls the LLM to generate the report content.
    5. Parses the LLM's output into the structured `ResearchReport` Pydantic model.

    Args:
        collection_name (str): The name of the ChromaDB collection for this research task.
        documents (list): The list of documents to be used for the retriever.

    Returns:
        An LCEL chain that takes a topic as input and produces a ResearchReport.
    """
    print("--- Creating report generation chain ---")

    # Initialize the retriever for the given collection
    retriever = get_retriever(collection_name, documents)

    # Configure the LLM with a structured output parser for the ResearchReport schema
    structured_llm = llm_with_fallback.with_structured_output(ResearchReport)

    # Create the LCEL chain
    chain = (
        {
            "context": retriever | format_docs,
            "topic": RunnablePassthrough()
        }
        | report_generation_prompt
        | structured_llm
    )

    print("--- Report generation chain created successfully ---")
    return chain
