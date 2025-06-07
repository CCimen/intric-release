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
    
    def _model_supports_reasoning(self) -> bool:
        """
        Check if the current Gemini model supports reasoning/thinking parameters.
        
        Based on Google's Gemini API documentation:
        - gemini-2.0-flash: No reasoning support
        - gemini-2.5-flash-*: Optional reasoning support  
        - gemini-2.5-pro-*: Reasoning support (always-on for Pro)
        
        Returns:
            bool: True if model supports reasoning_effort parameter
        """
        model_name = self._get_correct_model_name()
        
        # Models that do NOT support reasoning
        non_reasoning_models = [
            "gemini-2.0-flash"
        ]
        
        # Models that DO support reasoning
        reasoning_models = [
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-pro-preview-06-05"
        ]
        
        if model_name in non_reasoning_models:
            return False
        elif model_name in reasoning_models:
            return True
        else:
            # Default: assume reasoning support for newer/unknown models
            # Log a warning for unknown models
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Unknown Gemini model '{model_name}' - assuming reasoning support. Please update model capability list.")
            return True
    
    def _get_kwargs(self, kwargs: ModelKwargs | None):
        """
        Override to handle Gemini-specific parameters with reasoning_effort support.
        
        Maps reasoning_level to Google's reasoning_effort parameter.
        Maintains backward compatibility with thinking_budget.
        Only adds reasoning parameters for models that support them.
        """
        base_kwargs = super()._get_kwargs(kwargs)
        
        # Remove Intric-specific parameters not supported by Gemini/OpenAI API
        # These are our internal abstractions that need to be mapped to API-specific params
        base_kwargs.pop("thinking_budget", None)   # Legacy parameter
        base_kwargs.pop("reasoning_level", None)   # Unified abstraction
        
        # Get model information for logging and capability checking
        model_name = self._get_correct_model_name()
        supports_reasoning = self._model_supports_reasoning()
        
        # Enhanced logging for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Gemini Model: {model_name}, supports_reasoning: {supports_reasoning}")
        
        # Only add reasoning_effort for models that support reasoning capabilities
        if kwargs and supports_reasoning:
            reasoning_effort = self._map_reasoning_level_to_effort(kwargs)
            if reasoning_effort and reasoning_effort != "none":
                base_kwargs["reasoning_effort"] = reasoning_effort
                logger.info(f"Gemini API: Added reasoning_effort={reasoning_effort}")
            else:
                logger.info(f"Gemini API: No reasoning_effort (disabled or none)")
        elif kwargs:
            # Log when reasoning is requested but not supported
            reasoning_effort = self._map_reasoning_level_to_effort(kwargs)
            if reasoning_effort and reasoning_effort != "none":
                logger.warning(f"Gemini API: Model {model_name} does not support reasoning, ignoring reasoning_effort={reasoning_effort}")
        
        logger.info(f"Gemini API: Final parameters: {list(base_kwargs.keys())}")
        return base_kwargs
    
    def _map_reasoning_level_to_effort(self, kwargs: ModelKwargs) -> str:
        """
        Map reasoning_level or thinking_budget to Google's reasoning_effort parameter.
        
        Priority:
        1. reasoning_level (new unified approach)
        2. thinking_budget (legacy fallback)
        3. "none" (default - disabled)
        """
        # Use reasoning_level if provided
        if kwargs.reasoning_level:
            if kwargs.reasoning_level == "disabled":
                return "none"
            return kwargs.reasoning_level  # Direct mapping for "low", "medium", "high"
        
        # Fallback to thinking_budget conversion for backward compatibility
        if kwargs.thinking_budget is not None:
            if kwargs.thinking_budget == 0:
                return "none"
            elif kwargs.thinking_budget <= 512:
                return "low"
            elif kwargs.thinking_budget <= 1024:
                return "medium"
            else:
                return "high"
        
        # Default: disabled
        return "none"
    
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