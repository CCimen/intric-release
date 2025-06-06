import pytest
from unittest.mock import Mock, patch

from intric.ai_models.completion_models.completion_model import Context, Message, ModelKwargs
from intric.completion_models.infrastructure.adapters.gemini_model_adapter import (
    GeminiModelAdapter,
)
from tests.fixtures import TEST_MODEL_GEMINI_FLASH

TEST_QUESTION = "I have a question"


def test_gemini_adapter_initialization():
    """Test that GeminiModelAdapter initializes correctly with the proper base URL."""
    with patch("intric.main.config.SETTINGS") as mock_settings:
        mock_settings.gemini_api_key = "test-api-key"
        
        adapter = GeminiModelAdapter(TEST_MODEL_GEMINI_FLASH)
        
        assert adapter.model == TEST_MODEL_GEMINI_FLASH
        assert adapter.client.base_url == GeminiModelAdapter.GEMINI_BASE_URL
        assert adapter.extra_headers is None


def test_gemini_adapter_inherits_query_creation():
    """Test that GeminiModelAdapter creates queries identical to OpenAI adapter."""
    with patch("intric.main.config.SETTINGS") as mock_settings:
        mock_settings.gemini_api_key = "test-api-key"
        
        adapter = GeminiModelAdapter(TEST_MODEL_GEMINI_FLASH)
        context = Context(input=TEST_QUESTION, prompt="You are a helpful assistant")
        
        expected_query = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": [{"type": "text", "text": TEST_QUESTION}]},
        ]
        
        query = adapter.create_query_from_context(context=context)
        
        assert query == expected_query


def test_gemini_adapter_thinking_kwargs_for_flash_model():
    """Test that thinking_budget is set correctly for Gemini 2.5 Flash models."""
    with patch("intric.main.config.SETTINGS") as mock_settings:
        mock_settings.gemini_api_key = "test-api-key"
        
        adapter = GeminiModelAdapter(TEST_MODEL_GEMINI_FLASH)
        
        # Test with no model_kwargs provided
        kwargs = adapter._get_kwargs(None)
        assert kwargs == {"thinking_budget": 512}  # Default for 2.5 Flash
        
        # Test with custom thinking_budget
        model_kwargs = ModelKwargs(thinking_budget=1024)
        kwargs = adapter._get_kwargs(model_kwargs)
        assert kwargs["thinking_budget"] == 1024


def test_gemini_adapter_thinking_kwargs_for_pro_model():
    """Test that thinking_budget is set correctly for Gemini 2.5 Pro models."""
    # Create a Pro model for testing
    pro_model = TEST_MODEL_GEMINI_FLASH.model_copy()
    pro_model.name = "gemini-2.5-pro"
    
    with patch("intric.main.config.SETTINGS") as mock_settings:
        mock_settings.gemini_api_key = "test-api-key"
        
        adapter = GeminiModelAdapter(pro_model)
        
        # Test with no model_kwargs provided
        kwargs = adapter._get_kwargs(None)
        assert kwargs == {"thinking_budget": 1024}  # Default for 2.5 Pro


def test_gemini_adapter_no_thinking_for_non_reasoning_model():
    """Test that thinking_budget is not set for non-reasoning models."""
    # Create a non-reasoning model (like 2.0 Flash)
    non_reasoning_model = TEST_MODEL_GEMINI_FLASH.model_copy()
    non_reasoning_model.name = "gemini-2.0-flash"
    non_reasoning_model.reasoning = False
    
    with patch("intric.main.config.SETTINGS") as mock_settings:
        mock_settings.gemini_api_key = "test-api-key"
        
        adapter = GeminiModelAdapter(non_reasoning_model)
        
        kwargs = adapter._get_kwargs(None)
        assert kwargs == {}


def test_gemini_adapter_with_conversation_history():
    """Test that GeminiModelAdapter handles conversation history correctly."""
    with patch("intric.main.config.SETTINGS") as mock_settings:
        mock_settings.gemini_api_key = "test-api-key"
        
        adapter = GeminiModelAdapter(TEST_MODEL_GEMINI_FLASH)
        
        previous_messages = [
            Message(
                question="What is AI?",
                answer="AI stands for Artificial Intelligence.",
            ),
            Message(
                question="How does it work?", 
                answer="AI systems process data to make predictions or decisions.",
            )
        ]
        
        context = Context(
            input=TEST_QUESTION,
            prompt="You are an AI expert",
            messages=previous_messages
        )
        
        query = adapter.create_query_from_context(context=context)
        
        expected_query = [
            {"role": "system", "content": "You are an AI expert"},
            {"role": "user", "content": [{"type": "text", "text": "What is AI?"}]},
            {"role": "assistant", "content": "AI stands for Artificial Intelligence."},
            {"role": "user", "content": [{"type": "text", "text": "How does it work?"}]},
            {"role": "assistant", "content": "AI systems process data to make predictions or decisions."},
            {"role": "user", "content": [{"type": "text", "text": TEST_QUESTION}]},
        ]
        
        assert query == expected_query


def test_gemini_adapter_custom_kwargs_override():
    """Test that custom model kwargs properly override defaults."""
    with patch("intric.main.config.SETTINGS") as mock_settings:
        mock_settings.gemini_api_key = "test-api-key"
        
        adapter = GeminiModelAdapter(TEST_MODEL_GEMINI_FLASH)
        
        # Test with custom kwargs including thinking_budget=0 to disable thinking
        model_kwargs = ModelKwargs(
            thinking_budget=0,
            temperature=0.7,
            max_tokens=1000
        )
        
        kwargs = adapter._get_kwargs(model_kwargs)
        
        expected_kwargs = {
            "thinking_budget": 0,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        assert kwargs == expected_kwargs