from openai import AsyncOpenAI

from intric.ai_models.completion_models.completion_model import (
    CompletionModel,
    Context,
    ModelKwargs,
)
from intric.completion_models.infrastructure.adapters.openai_model_adapter import (
    OpenAIModelAdapter,
)
from intric.completion_models.infrastructure import get_response_open_ai
from intric.main.config import SETTINGS


class GeminiModelAdapter(OpenAIModelAdapter):
    """
    Adapter for Google Gemini models using OpenAI-compatible API.
    
    This adapter extends OpenAIModelAdapter because Gemini provides an 
    OpenAI-compatible endpoint. Changes to OpenAIModelAdapter may affect
    this adapter, but this is intentional as they share the same API interface.
    
    Supports:
    - gemini-2.0-flash (no thinking support)
    - gemini-2.5-flash-preview-05-20 (optional thinking via thinking_budget)
    - gemini-2.5-pro-preview-06-05 (mandatory thinking, min 128 tokens)
    """
    
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    def __init__(self, model: CompletionModel):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=SETTINGS.gemini_api_key,
            base_url=self.GEMINI_BASE_URL
        )
        self.extra_headers = None
    
    def _get_correct_model_name(self) -> str:
        """
        Map legacy model names to correct API model names.
        
        This handles the transition from simplified names to the actual
        API model names with preview versions and dates.
        """
        model_name_mapping = {
            "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-pro": "gemini-2.5-pro-preview-06-05",
            "gemini-2.0-flash": "gemini-2.0-flash"  # Already correct
        }
        
        return model_name_mapping.get(self.model.name, self.model.name)
    
    def _get_kwargs(self, kwargs: ModelKwargs | None):
        """
        Override to handle Gemini-specific parameters.
        
        Fallback approach: Remove all thinking parameters for now to restore basic functionality.
        This ensures Gemini models work without thinking-related errors.
        """
        base_kwargs = super()._get_kwargs(kwargs)
        
        # TEMPORARILY DISABLE thinking support to restore basic functionality
        # Remove thinking_budget entirely to prevent OpenAI client errors
        base_kwargs.pop("thinking_budget", None)
        
        # TODO: Re-implement thinking support once basic functionality is confirmed
        # The approach will likely need to use Gemini's native API or 
        # wait for OpenAI client library updates
        
        return base_kwargs
    
    async def get_response(
        self,
        context: Context,
        model_kwargs: ModelKwargs | None = None,
    ):
        """Override to use correct model name for API calls."""
        query = self.create_query_from_context(context=context)
        return await get_response_open_ai.get_response(
            client=self.client,
            model_name=self._get_correct_model_name(),  # Use mapped model name
            messages=query,
            model_kwargs=self._get_kwargs(model_kwargs),
            extra_headers=self.extra_headers,
        )

    def get_response_streaming(
        self,
        context: Context,
        model_kwargs: ModelKwargs | None = None,
    ):
        """Override to use correct model name for API calls."""
        query = self.create_query_from_context(context=context)
        tools = self._build_tools_from_context(context=context)
        return get_response_open_ai.get_response_streaming(
            client=self.client,
            model_name=self._get_correct_model_name(),  # Use mapped model name
            messages=query,
            model_kwargs=self._get_kwargs(model_kwargs),
            tools=tools,
            extra_headers=self.extra_headers,
        )