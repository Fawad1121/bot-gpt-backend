"""
Groq LLM integration service
"""
from groq import Groq
from typing import List, Dict, Any, Optional
import asyncio
from functools import partial

from app.config import settings
from app.utils.logger import setup_logger
from app.utils.token_counter import count_messages_tokens, truncate_messages_to_fit

logger = setup_logger(__name__)


class LLMService:
    """Service for interacting with Groq LLM API"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.DEFAULT_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.context_window_size = settings.CONTEXT_WINDOW_SIZE
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_retries: int = 3,
        timeout: int = 30
    ) -> tuple[str, int]:
        """
        Generate a response from the LLM
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_retries: Maximum number of retry attempts
            timeout: Timeout in seconds
        
        Returns:
            Tuple of (response_text, tokens_used)
        """
        # Truncate messages to fit context window
        truncated_messages = truncate_messages_to_fit(
            messages,
            self.context_window_size,
            keep_system=True
        )
        
        # Log token usage
        input_tokens = count_messages_tokens(truncated_messages)
        logger.info(f"Sending {len(truncated_messages)} messages ({input_tokens} tokens) to LLM")
        
        # Print the final prompt being sent to LLM
        logger.info("=" * 80)
        logger.info("FINAL PROMPT SENT TO LLM:")
        logger.info("=" * 80)
        for i, msg in enumerate(truncated_messages):
            logger.info(f"\n[Message {i+1}] Role: {msg['role']}")
            logger.info(f"Content:\n{msg['content']}")  # Full content
            logger.info("-" * 80)
        logger.info("=" * 80)
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                # Run synchronous Groq API call in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    partial(
                        self._call_groq_api,
                        truncated_messages
                    )
                )
                
                response_text = response.choices[0].message.content
                total_tokens = response.usage.total_tokens
                
                logger.info(f"LLM response generated successfully ({total_tokens} total tokens)")
                return response_text, total_tokens
                
            except Exception as e:
                logger.error(f"LLM API error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    # Last attempt failed
                    raise Exception(f"Failed to generate LLM response after {max_retries} attempts: {e}")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Failed to generate LLM response")
    
    def _call_groq_api(self, messages: List[Dict[str, str]]):
        """Synchronous call to Groq API"""
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
    
    async def generate_title(self, first_message: str) -> str:
        """
        Generate a conversation title from the first message
        
        Args:
            first_message: The first user message
        
        Returns:
            Generated title (max 50 chars)
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Generate a short, concise title (max 6 words) for a conversation that starts with the following message. Only return the title, nothing else."
                },
                {
                    "role": "user",
                    "content": first_message
                }
            ]
            
            title, _ = await self.generate_response(messages)
            return title.strip()[:50]  # Limit to 50 chars
            
        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            # Fallback: use first few words of message
            words = first_message.split()[:5]
            return " ".join(words) + ("..." if len(first_message.split()) > 5 else "")


# Global LLM service instance
llm_service = LLMService()
