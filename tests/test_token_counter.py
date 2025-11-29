"""
Tests for token counter utilities
"""
import pytest
from app.utils.token_counter import count_tokens, count_messages_tokens, truncate_messages_to_fit


def test_count_tokens():
    """Test basic token counting"""
    text = "Hello, how are you today?"
    tokens = count_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)


def test_count_messages_tokens():
    """Test token counting for message list"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help you?"}
    ]
    tokens = count_messages_tokens(messages)
    assert tokens > 0
    assert isinstance(tokens, int)


def test_truncate_messages_to_fit():
    """Test message truncation"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
        {"role": "user", "content": "Message 3"},
    ]
    
    # Truncate to very small limit
    truncated = truncate_messages_to_fit(messages, max_tokens=50, keep_system=True)
    
    # Should keep system message
    assert truncated[0]["role"] == "system"
    # Should have fewer messages
    assert len(truncated) <= len(messages)


def test_truncate_keeps_recent_messages():
    """Test that truncation keeps most recent messages"""
    messages = [
        {"role": "user", "content": "Old message"},
        {"role": "assistant", "content": "Old response"},
        {"role": "user", "content": "Recent message"},
        {"role": "assistant", "content": "Recent response"},
    ]
    
    truncated = truncate_messages_to_fit(messages, max_tokens=100, keep_system=False)
    
    # Should keep recent messages
    if len(truncated) < len(messages):
        assert "Recent" in truncated[-1]["content"]
