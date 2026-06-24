# 🔬 AI Research Assistant Agent

An autonomous AI agent that researches any topic by searching the web, scraping multiple sources, and generating a comprehensive structured research report with citations — all in minutes.


---

## 🧠 How It Works

```
User enters a topic
        ↓
ReAct Agent (LangChain) starts planning
        ↓
Tool 1: DuckDuckGo Search → finds relevant URLs
        ↓
Tool 2: Web Scraper (BeautifulSoup) → extracts text from each URL
        ↓
Text is chunked → embedded → stored in ChromaDB (vector store)
        ↓
Ensemble Retriever (BM25 + Semantic Search) retrieves relevant chunks
        ↓
Gemini 2.0 Flash generates structured report using retrieved context
        ↓
Structured JSON report returned to React frontend
```

---

## ✨ Features

- 🤖 **Autonomous ReAct Agent** — plans and executes multi-step research without manual intervention
- 🔍 **Multi-source Research** — searches and scrapes up to 10 web sources simultaneously
- 🧩 **Hybrid Retrieval** — combines BM25 keyword search + semantic vector search for best results
- 📄 **Structured Reports** — generates title, executive summary, 5 key findings, detailed analysis, future implications, and citations
- 💾 **Persistent Vector Store** — ChromaDB stores embeddings locally per research session
- 🔄 **LLM Fallback** — automatically falls back to Groq (Llama 3.3 70B) if Gemini is rate limited
- 📋 **Report History** — saves all generated reports in browser for later reference
- 📥 **Export Options** — download reports as JSON or plain text

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python + FastAPI | REST API server |
| LangChain | Agent framework, chains, RAG pipeline |
| Google Gemini 2.0 Flash | Primary LLM for report generation |
| Groq Llama 3.3 70B | Fallback LLM |
| ChromaDB | Local persistent vector database |
| HuggingFace Embeddings (BAAI/bge-small-en-v1.5) | Text embeddings |
| DuckDuckGo Search | Free web search (no API key needed) |
| BeautifulSoup4 + lxml | Web scraping and HTML parsing |
| Pydantic | Structured output validation |

### Frontend
| Technology | Purpose |
|---|---|
| React 19 + TypeScript | UI framework |
| Vite | Build tool and dev server |
| Lucide React | Icons |

---

## 📁 Project Structure

```
research-agent/
├── backend/
│   ├── agent/
│   │   ├── prompts.py          # ReAct agent + report generation prompts
│   │   ├── research_agent.py   # ReAct agent + fallback search logic
│   │   └── tools.py            # DuckDuckGo search + web scraper tools
│   ├── chains/
│   │   └── report_chain.py     # LCEL report generation chain
│   ├── models/
│   │   └── schemas.py          # Pydantic schemas (ResearchReport, Source)
│   ├── rag/
│   │   ├── embeddings.py       # HuggingFace embedding model
│   │   ├── retriever.py        # Ensemble retriever (BM25 + vector)
│   │   └── vector_store.py     # ChromaDB vector store setup
│   ├── config.py               # Settings and environment variables
│   ├── llm.py                  # Gemini primary + Groq fallback LLM
│   ├── main.py                 # FastAPI app + research endpoint
│   └── requirements.txt        # Python dependencies
├── frontend/
│   └── src/
│       └── App.tsx             # Full React UI
├── .env.example                # Environment variable template
└── .gitignore
```

---

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Conda or virtualenv

### 1. Clone the Repository

```bash
git clone https://github.com/peddinenibhaswanth/research-agent.git
cd research-agent
```

### 2. Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Fill in your API keys in .env
```

| Variable | Where to Get |
|---|---|
| `GOOGLE_API_KEY` | [ai.google.dev](https://ai.google.dev) — free, no credit card |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free, no credit card |

### 3. Set Up Backend

```bash
# Create conda environment
conda create -n research-agent python=3.11 -y
conda activate research-agent

# Install dependencies
pip install -r backend/requirements.txt
```

### 4. Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Backend running at: `http://localhost:8000`  
API docs available at: `http://localhost:8000/docs`

### 5. Set Up and Run Frontend

```bash
# Open a new terminal
cd frontend
npm install
npm run dev
```

Frontend running at: `http://localhost:5173`

---

## 🔑 Environment Variables

```bash
# .env.example
GOOGLE_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
MAX_SOURCES=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/research` | Run research agent |

### POST /api/research

**Request:**
```json
{
  "topic": "AI in healthcare",
  "max_sources": 5
}
```

**Response:**
```json
{
  "title": "AI Transforming Healthcare...",
  "topic": "AI in healthcare",
  "executive_summary": "...",
  "key_findings": [
    "finding 1",
    "finding 2",
    "finding 3",
    "finding 4",
    "finding 5"
  ],
  "detailed_analysis": "...",
  "future_implications": "...",
  "sources": [
    {
      "title": "Source Title",
      "url": "https://...",
      "key_insight": "..."
    }
  ]
}
```

---

## 🧩 LangChain Concepts Used

| Concept | Where Used |
|---|---|
| LLM Models | Gemini 2.0 Flash + Groq Llama 3.3 70B |
| PromptTemplates | ReAct agent prompt + report generation prompt |
| Structured Output | `.with_structured_output(ResearchReport)` |
| LCEL Chains | Report generation chain with pipe operator |
| Document Loaders | Web content via BeautifulSoup |
| Text Splitters | `RecursiveCharacterTextSplitter` |
| Vector Stores | ChromaDB with persistent storage |
| Retrievers | Ensemble (BM25 + Semantic) + Contextual Compression |
| RAG Pipeline | Full retrieval-augmented generation per report |
| Tools | DuckDuckGo search + custom web scraper |
| Tool Calling | Agent autonomously decides which tool to use |
| ReAct Agent | Plans and executes multi-step research |
| LLM Fallback | `.with_fallbacks()` for automatic failover |

---

## 🆓 Completely Free to Run

| Service | Free Tier |
|---|---|
| Google Gemini 2.0 Flash | 1,500 requests/day |
| Groq Llama 3.3 70B | 1,000 requests/day |
| DuckDuckGo Search | Unlimited |
| ChromaDB | Local, unlimited |
| HuggingFace Embeddings | Local, unlimited |

**Total cost: ₹0**

---

## 👨‍💻 Author

**Peddineni Bhaswanth**
- GitHub: [@peddinenibhaswanth](https://github.com/peddinenibhaswanth)
- Email: bhaswanthpeddineni@gmail.com
