from langchain.agents import create_react_agent, AgentExecutor
from .tools import research_tools, scrape_url, search_web_results
from .prompts import react_agent_prompt
from llm import llm_with_fallback


MIN_SCRAPED_TEXT_LENGTH = 500


def create_research_agent():
    """
    Creates and returns a ReAct agent equipped with research tools.

    The agent is built using a predefined prompt, a language model (with fallbacks),
    and a set of tools for searching and scraping the web.

    Returns:
        A LangChain agent runnable.
    """
    print("--- Creating ReAct research agent ---")
    # The create_react_agent function initializes an agent that follows the ReAct framework.
    agent = create_react_agent(
        llm=llm_with_fallback,
        tools=research_tools,
        prompt=react_agent_prompt
    )
    print("--- ReAct research agent created successfully ---")
    return agent


def get_agent_executor():
    """
    Creates and returns an AgentExecutor for running the research agent.

    The executor is responsible for managing the agent's lifecycle, including
    calling the agent, executing the tools it chooses, and passing the results
    back to the agent.

    Returns:
        An AgentExecutor instance.
    """
    print("--- Creating agent executor ---")
    agent = create_research_agent()
    executor = AgentExecutor(
        agent=agent,
        tools=research_tools,
        verbose=True,  # Set to True to see the agent's thought process
        handle_parsing_errors=True,  # Gracefully handle any LLM output parsing errors
        max_iterations=10,  # Add a safeguard to prevent infinite loops
        return_intermediate_steps=True
    )
    print("--- Agent executor created successfully ---")
    return executor


def fallback_search_and_scrape(topic: str, max_sources: int) -> list[dict[str, str]]:
    """
    Performs deterministic search and scraping if the LLM agent fails to collect sources.
    """
    print("--- Running fallback search and scrape ---")
    scraped_texts = []
    search_results = search_web_results(topic, max_results=max(max_sources * 3, 8))

    for result in search_results:
        if len(scraped_texts) >= max_sources:
            break

        url = result["url"]
        try:
            text = scrape_url(url)
        except Exception as exc:
            print(f"--- Fallback scrape failed for {url}: {exc} ---")
            continue

        if len(text) < MIN_SCRAPED_TEXT_LENGTH:
            print(f"--- Fallback scrape skipped short page: {url} ---")
            continue

        scraped_texts.append({
            "url": url,
            "text": text,
        })

    print(f"--- Fallback finished. Found {len(scraped_texts)} valid scraped texts. ---")
    return scraped_texts


def run_agent_and_get_scraped_texts(topic: str, max_sources: int) -> list[dict[str, str]]:
    """
    Runs the research agent for a given topic and extracts the scraped text
    content from its intermediate steps.

    Args:
        topic (str): The research topic.
        max_sources (int): The maximum number of sources the agent should aim to find.

    Returns:
        list[dict[str, str]]: Scraped source objects with a URL and text content.
    """
    print(f"--- Running agent for topic: {topic} ---")
    response = {"intermediate_steps": []}
    try:
        agent_executor = get_agent_executor()

        # Invoke the agent executor
        response = agent_executor.invoke({
            "topic": topic,
            "max_sources": max_sources
        })
    except Exception as exc:
        print(f"--- Agent failed before collecting sources: {exc} ---")
    

    # Extract scraped content from the agent's intermediate steps
    scraped_texts = []
    for step in response.get("intermediate_steps", []):
        action, observation = step
        is_scraper_result = action.tool == "web_scraper"
        if not is_scraper_result or not isinstance(observation, str):
            continue

        is_error = observation.lower().startswith(("error", "an unexpected error"))
        if not is_error:
            scraped_texts.append({
                "url": str(action.tool_input),
                "text": observation
            })

    if not scraped_texts:
        scraped_texts = fallback_search_and_scrape(topic, max_sources)

    print(f"--- Agent finished running. Found {len(scraped_texts)} valid scraped texts. ---")
    return scraped_texts
