from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from config import settings
from google.api_core.exceptions import ResourceExhausted


# Primary LLM: Google Gemini 2.5 Flash
# This is our main model for generation tasks. It's configured to use the API key
# from our settings and set to a specific model version.
# The temperature is set to 0 for deterministic and factual outputs.
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0,
    max_output_tokens=4096
)

# Fallback LLM: Groq Llama 3 70B
# This model serves as a backup in case the primary Gemini model fails or is rate-limited.
# Groq provides very fast inference speeds.
fallback_llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0,
    max_tokens=4096
)

# llm_with_fallback = primary_llm.with_fallbacks(
#     [fallback_llm],
#     exceptions_to_handle=(ResourceExhausted,)  # Handle rate limits and resource exhaustion gracefully
# )

llm_with_fallback = fallback_llm