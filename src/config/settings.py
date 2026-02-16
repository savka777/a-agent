# -----------------------------------------------------------------------------
# Model Settings
#
# Configure LLM provider and model mappings.
# Supports: "vertex" (Claude on Vertex AI) or "gemini" (Google Gemini)
# -----------------------------------------------------------------------------
import os

# LLM Provider: "vertex" or "gemini"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "vertex")

# Model mappings for each provider
MODEL_MAPPING = {
    "vertex": {
        "claude-opus": "claude-opus-4-5@20251101",
        "claude-sonnet": "claude-sonnet-4-5-v2@20250514",
        "default": "claude-opus-4-5@20251101",
    },
    "gemini": {
        "gemini-3-pro": "gemini-3-pro-preview",
        "default": "gemini-3-pro-preview",
    }
}

# Vertex AI settings (used when LLM_PROVIDER="vertex")
VERTEX_PROJECT_ID = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID", "gen-lang-client-0494134627")
VERTEX_REGION = os.environ.get("CLOUD_ML_REGION", "us-east5")


def get_model_id(model_name: str) -> str:
    """Get the actual model ID for the current provider."""
    provider_models = MODEL_MAPPING.get(LLM_PROVIDER, MODEL_MAPPING["vertex"])
    return provider_models.get(model_name, provider_models.get("default", model_name))


def get_provider() -> str:
    """Get the current LLM provider."""
    return LLM_PROVIDER
