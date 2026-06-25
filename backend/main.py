import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import uuid
import re
import nest_asyncio
import traceback
import os

# Apply the patch to allow nested asyncio event loops
nest_asyncio.apply()

from models.schemas import ResearchRequest, ResearchReport
from agent.research_agent import run_agent_and_get_scraped_texts
from rag.vector_store import add_texts_to_vector_store
from chains.report_chain import get_report_generation_chain

# Initialize FastAPI app
app = FastAPI(
    title="AI Research Assistant API",
    description="An API for conducting AI-powered research and generating reports.",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:5173",  # Default Vite dev server
    "http://127.0.0.1:5173",
    "https://research-agent.vercel.app",
    "https://research-agent-*.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_collection_name(topic: str) -> str:
    """Creates a sanitized, unique collection name for ChromaDB."""
    # Sanitize the topic to be a valid collection name
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', topic).lower()
    # Truncate to a reasonable length
    sanitized = sanitized[:50]
    # Add a unique identifier
    return f"{sanitized}_{uuid.uuid4().hex[:8]}"

@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to ensure the API is running.
    """
    return {"status": "ok"}

@app.post("/api/research", response_model=ResearchReport, tags=["Research"])
async def research_endpoint(request: ResearchRequest):
    """
    The main endpoint to trigger the AI research agent.
    It takes a topic and max_sources, runs the full research pipeline,
    and returns a structured research report.
    """
    try:
        # Define a synchronous function to run the entire pipeline
        def sync_pipeline():
            # 1. Run the ReAct agent to search and scrape web content
            print("step1")
            texts = run_agent_and_get_scraped_texts(request.topic, request.max_sources)
            if not texts:
                return None, "Could not find or scrape any relevant sources. Please try a different topic."

            # 2. Create a unique collection name
            print("step2")
            collection_name = create_collection_name(request.topic)

            # 3. Add texts to vector store
            print("step3")
            add_texts_to_vector_store(texts, collection_name)

            # 4. Create the report generation chain
            print("step4")
            report_chain = get_report_generation_chain(collection_name, texts)

            # 5. Invoke the chain to generate the final report
            print("--- Generating final report ---")
            print("step5")
            final_report = report_chain.invoke(request.topic)
            print("--- Final report generated ---")
            print("step6")
            return final_report, None

        # Run the synchronous pipeline in a thread pool to avoid blocking the event loop
        final_report, error_message = await run_in_threadpool(sync_pipeline)

        if error_message:
            raise HTTPException(status_code=404, detail=error_message)

        return final_report

    except Exception as e:
        print("\n===== FULL ERROR =====")
        traceback.print_exc()
        print("======================\n")

        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}"
        )
if __name__ == "__main__":
    """
    Main entry point to run the FastAPI application using uvicorn.
    """
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
