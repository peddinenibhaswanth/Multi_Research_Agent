from typing import List
from pydantic import BaseModel, Field, field_validator


class Source(BaseModel):
    """
    Pydantic model for a single source cited in the research report.
    """
    title: str = Field(..., description="The title of the web page or article.")
    url: str = Field(..., description="The URL of the source.")
    key_insight: str = Field(..., description="A key insight or piece of information derived from this source.")


class ResearchReport(BaseModel):
    """
    Pydantic model for the final research report.
    This is the structured output we expect from our agent.
    """
    title: str = Field(..., description="A compelling title for the research report.")
    topic: str = Field(..., description="The original research topic provided by the user.")
    executive_summary: str = Field(..., description="A concise, high-level summary of the report's findings.")
    key_findings: List[str] = Field(
        ...,
        description="A list of exactly 5 key bullet-point findings from the research.",
        min_items=5,
        max_items=5
    )
    detailed_analysis: str = Field(..., description="An in-depth analysis of the research topic, synthesizing information from sources.")
    future_implications: str = Field(..., description="A discussion of the potential future impact and trends related to the topic.")
    sources: List[Source] = Field(..., description="A list of sources used to generate the report.")


class ResearchRequest(BaseModel):
    """
    Pydantic model for the incoming API request.
    """
    topic: str = Field(..., min_length=1)
    max_sources: int = Field(5, gt=0, le=10, description="The maximum number of sources to use for the research. Must be between 1 and 10.")

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_blank(cls, value: str) -> str:
        topic = value.strip()
        if not topic:
            raise ValueError("Topic must not be blank.")
        return topic
