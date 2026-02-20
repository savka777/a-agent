"""Pydantic schemas for ALPHY research data."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# --- App Store Schemas ---

class AppSummary(BaseModel):
    """Summary of an app from search results."""
    app_id: str
    name: str
    developer: str
    developer_id: Optional[str] = None
    platform: Literal["ios", "android"]
    score: Optional[float] = None
    ratings_count: Optional[int] = None
    free: bool = True
    url: Optional[str] = None


class AppDetails(BaseModel):
    """Full app details from MCP."""
    app_id: str
    name: str
    developer: str
    developer_id: Optional[str] = None
    platform: Literal["ios", "android"]
    description: Optional[str] = None
    score: Optional[float] = None
    ratings_count: Optional[int] = None
    reviews_count: Optional[int] = None
    version: Optional[str] = None
    released: Optional[str] = None
    updated: Optional[str] = None
    size: Optional[str] = None
    installs: Optional[str] = None  # Android only
    price: Optional[float] = 0.0
    free: bool = True
    url: Optional[str] = None
    icon: Optional[str] = None
    screenshots: list[str] = Field(default_factory=list)
    genre: Optional[str] = None
    content_rating: Optional[str] = None


class DeveloperInfo(BaseModel):
    """Developer portfolio info for indie detection."""
    developer_id: str
    name: str
    platform: Literal["ios", "android"]
    total_apps: int
    apps: list[AppSummary] = Field(default_factory=list)
    average_rating: Optional[float] = None
    total_ratings: Optional[int] = None
    is_indie: bool = Field(default=True, description="True if total_apps < 5")


class PricingDetails(BaseModel):
    """App monetization model."""
    app_id: str
    base_price: float = 0.0
    currency: str = "USD"
    in_app_purchases: list[dict] = Field(default_factory=list)
    has_subscriptions: bool = False
    monetization_model: Literal["free", "paid", "freemium", "subscription", "ads"] = "free"


class ReviewSummary(BaseModel):
    """Aggregated review analysis."""
    app_id: str
    total_reviews: int = 0
    average_score: Optional[float] = None
    sentiment_positive: float = 0.0
    sentiment_neutral: float = 0.0
    sentiment_negative: float = 0.0
    common_themes: list[str] = Field(default_factory=list)
    recent_issues: list[str] = Field(default_factory=list)
    keyword_frequency: dict[str, int] = Field(default_factory=dict)


# --- Product Hunt Schemas ---

class ProductSummary(BaseModel):
    """Summary of a Product Hunt launch."""
    id: str
    name: str
    tagline: str
    slug: str
    votes_count: int = 0
    comments_count: int = 0
    featured: bool = False
    url: Optional[str] = None
    thumbnail: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    makers_count: int = 0


class ProductDetails(BaseModel):
    """Full Product Hunt product details."""
    id: str
    name: str
    tagline: str
    slug: str
    description: Optional[str] = None
    votes_count: int = 0
    comments_count: int = 0
    featured: bool = False
    url: Optional[str] = None
    website: Optional[str] = None
    thumbnail: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    makers: list[dict] = Field(default_factory=list)
    created_at: Optional[str] = None


# --- Research Task Schemas ---

class ResearchTask(BaseModel):
    """A single research task for a worker."""
    id: str
    type: Literal["discover", "deep_research", "validate", "compare"]
    target: str  # App name, search query, or app ID
    platform: Literal["ios", "android", "both", "producthunt"] = "both"
    context: str  # User's overall intent
    success_criteria: list[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2


class ResearchResult(BaseModel):
    """Result from a research worker."""
    task_id: str
    app_name: str
    app_id: Optional[str] = None
    platform: str
    exists: bool = True
    confidence: Literal["high", "medium", "low"] = "medium"

    # Data from MCPs
    details: Optional[AppDetails] = None
    developer_info: Optional[DeveloperInfo] = None
    pricing: Optional[PricingDetails] = None
    reviews_summary: Optional[ReviewSummary] = None
    similar_apps: list[str] = Field(default_factory=list)
    product_hunt: Optional[ProductSummary] = None

    # Revenue (from web search)
    revenue_estimate: Optional[str] = None
    revenue_sources: list[str] = Field(default_factory=list)

    # Indie assessment
    is_indie: Optional[bool] = None
    indie_signals: list[str] = Field(default_factory=list)

    # Metadata
    gaps: list[str] = Field(default_factory=list, description="What we couldn't find")
    sources: list[str] = Field(default_factory=list, description="MCP tools called")


class FailedTask(BaseModel):
    """A task that failed after retries."""
    task: ResearchTask
    error: str
    attempts: int


# --- Scratchpad Schema ---

class Scratchpad(BaseModel):
    """Central scratchpad for research session."""
    discovered_apps: list[AppSummary] = Field(default_factory=list)
    researched_apps: dict[str, ResearchResult] = Field(default_factory=dict)
    product_hunt_launches: list[ProductSummary] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list, description="Cross-app observations")
    user_refinements: list[str] = Field(default_factory=list, description="User feedback incorporated")


# --- Revenue Search Schemas ---

class RevenueSearchResult(BaseModel):
    """Result from Tavily revenue search."""
    app_name: str
    revenue_found: bool = False
    mrr: Optional[str] = None
    arr: Optional[str] = None
    revenue_mentions: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class SocialBuzzResult(BaseModel):
    """Social media mentions and buzz."""
    app_name: str
    reddit_mentions: int = 0
    twitter_mentions: int = 0
    hacker_news_mentions: int = 0
    notable_posts: list[dict] = Field(default_factory=list)
    sentiment: Literal["positive", "neutral", "negative", "mixed"] = "neutral"
