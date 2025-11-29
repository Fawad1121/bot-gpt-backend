"""
Token counting utilities using tiktoken
"""
import tiktoken
from typing import List, Dict


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Count the number of tokens in a text string
    
    Args:
        text: The text to count tokens for
        model: The model to use for encoding (default: gpt-3.5-turbo)
    
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base encoding (used by gpt-3.5-turbo and gpt-4)
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))


def count_messages_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
    """
    Count tokens in a list of messages (chat format)
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: The model to use for encoding
    
    Returns:
        Total number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens_per_message = 3  # Every message follows <|start|>{role/name}\n{content}<|end|>\n
    tokens_per_name = 1  # If there's a name, the role is omitted
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    
    num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def truncate_messages_to_fit(
    messages: List[Dict[str, str]], 
    max_tokens: int, 
    model: str = "gpt-3.5-turbo",
    keep_system: bool = True
) -> List[Dict[str, str]]:
    """
    Truncate messages to fit within token limit
    
    Args:
        messages: List of message dictionaries
        max_tokens: Maximum number of tokens allowed
        model: The model to use for encoding
        keep_system: Whether to always keep system messages
    
    Returns:
        Truncated list of messages
    """
    if not messages:
        return messages
    
    # Separate system messages if needed
    system_messages = []
    other_messages = []
    
    if keep_system:
        for msg in messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)
    else:
        other_messages = messages
    
    # Start with system messages
    result = system_messages.copy()
    current_tokens = count_messages_tokens(result, model)
    
    # Add messages from the end (most recent first) until we hit the limit
    for msg in reversed(other_messages):
        msg_tokens = count_messages_tokens([msg], model)
        if current_tokens + msg_tokens <= max_tokens:
            result.insert(len(system_messages), msg)  # Insert after system messages
            current_tokens += msg_tokens
        else:
            break
    
    return result
