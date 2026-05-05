"""
AI Providers Module

Provides abstract interface and implementations for AI-based paper categorization.

Responsibilities:
    - Abstract AIProvider interface
    - Gemini, Claude, OpenAI implementations
    - Response parsing and error handling
    - Provider factory

Design Pattern: Strategy Pattern
"""

import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List

from .config import config
from .categories import category_manager


@dataclass
class CategorizationResult:
    """Result of paper categorization."""
    category_code: str
    category_name: str
    confidence: str  # high, medium, low
    reasoning: str
    alternative_categories: List[str]
    raw_response: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "category_code": self.category_code,
            "category_name": self.category_name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "alternative_categories": self.alternative_categories,
        }


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All providers must implement the categorize method.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def categorize(self, title: str, abstract: Optional[str] = None) -> Dict:
        """
        Categorize a paper based on title and optional abstract.

        Args:
            title: Paper title
            abstract: Optional paper abstract or text content

        Returns:
            Dict with category_code, category_name, confidence, reasoning, alternative_categories
        """
        pass

    @abstractmethod
    def query(self, prompt: str) -> str:
        """
        Send a simple query to the AI and return the raw response.

        Args:
            prompt: The prompt to send

        Returns:
            Raw text response from the AI
        """
        pass

    def _get_system_prompt(self) -> str:
        """Generate the system prompt with current categories."""
        category_manager.ensure_loaded()

        uncat_name = category_manager.get_uncategorized_name()

        return f"""You are an expert categorizer for books and papers. Your task is to categorize items into the most appropriate category from the provided hierarchy.

## Instructions:
1. Analyze the title and abstract/context carefully
2. Identify the PRIMARY subject matter and discipline - focus on WHAT the content is about, not HOW it's delivered
3. Select the MOST SPECIFIC subcategory that fits (always prefer subcategories like "5.3" over main categories like "5")
4. If the item fits multiple categories, choose based on primary discipline/field

## IMPORTANT - Avoid Common Mistakes:
- "Computer-Based Testing" or "Automated Scoring" → Psychology/Psychometrics (educational assessment), NOT Computer Science
- "Machine Learning for X" → If X is the main topic (biology, psychology, etc.), categorize under X
- "Digital/Online X" → Categorize by the subject X, not by the delivery method
- Technical terms in title don't automatically mean Computer Science

## Response Format:
You MUST respond in valid JSON format with these fields:
{{
    "category_code": "X.X",
    "category_name": "Full Category Name",
    "confidence": "high/medium/low",
    "reasoning": "Brief explanation of why this category was chosen",
    "alternative_categories": ["other possible categories if any"]
}}

CRITICAL: Use the EXACT category codes shown in the hierarchy (e.g., "5.3", "13.8"), not made-up codes.

""" + category_manager.generate_prompt()

    def _build_user_prompt(self, title: str, abstract: Optional[str]) -> str:
        """Build the user prompt for categorization."""
        prompt = f"Please categorize this paper:\n\nTitle: {title}"
        if abstract:
            max_len = config.app.max_abstract_length
            prompt += f"\n\nAbstract/Context: {abstract[:max_len]}"
        return prompt

    def _parse_response(self, response_text: str) -> Dict:
        """Parse JSON response from AI, with fallback handling."""
        response_text = response_text.strip()

        # Remove markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            return {
                "category_code": "0",
                "category_name": "Uncategorized",
                "confidence": "low",
                "reasoning": "Failed to parse API response",
                "alternative_categories": [],
                "raw_response": response_text[:500]
            }


class DigitalOceanProvider(AIProvider):
    """DigitalOcean GenAI API provider (OpenAI-compatible)."""

    def __init__(self, api_key: str):
        super().__init__("digitalocean")
        self.api_key = api_key
        self.model_name = config.ai.digitalocean_model

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url="https://inference.do-ai.run/v1/")
        except ImportError:
            raise ImportError("openai package not installed")

    def categorize(self, title: str, abstract: Optional[str] = None) -> Dict:
        user_prompt = self._build_user_prompt(title, abstract)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )

        response_text = response.choices[0].message.content
        return self._parse_response(response_text)

    def query(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=512
        )
        return response.choices[0].message.content


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str):
        super().__init__("gemini")
        self.api_key = api_key
        self.model_name = config.ai.gemini_model

        # Import and configure
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            raise ImportError("google-generativeai package not installed")

    def categorize(self, title: str, abstract: Optional[str] = None) -> Dict:
        user_prompt = self._build_user_prompt(title, abstract)

        model = self.genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )

        chat = model.start_chat(history=[])
        response = chat.send_message(self._get_system_prompt() + "\n\n" + user_prompt)
        return self._parse_response(response.text)

    def query(self, prompt: str) -> str:
        model = self.genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 512,
            }
        )
        response = model.generate_content(prompt)
        return response.text


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str):
        super().__init__("claude")
        self.api_key = api_key
        self.model_name = config.ai.claude_model

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed")

    def categorize(self, title: str, abstract: Optional[str] = None) -> Dict:
        user_prompt = self._build_user_prompt(title, abstract)

        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": self._get_system_prompt() + "\n\n" + user_prompt}
            ]
        )

        response_text = message.content[0].text
        return self._parse_response(response_text)

    def query(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=512,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str):
        super().__init__("openai")
        self.api_key = api_key
        self.model_name = config.ai.openai_model

        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed")

    def categorize(self, title: str, abstract: Optional[str] = None) -> Dict:
        user_prompt = self._build_user_prompt(title, abstract)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )

        response_text = response.choices[0].message.content
        return self._parse_response(response_text)

    def query(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=512
        )
        return response.choices[0].message.content


class ProviderFactory:
    """
    Factory for creating AI providers.

    Usage:
        provider = ProviderFactory.get_provider()  # Auto-select
        provider = ProviderFactory.get_provider("claude")  # Specific
    """

    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> AIProvider:
        """
        Get an AI provider instance.

        Args:
            provider_name: Optional provider name (gemini, claude, openai)
                          If None, uses default or first available.

        Returns:
            An initialized AI provider

        Raises:
            SystemExit: If no provider is available
        """
        # If specific provider requested
        if provider_name:
            provider_name = provider_name.lower()
            if provider_name == "digitalocean" and config.ai.digitalocean_key:
                return DigitalOceanProvider(config.ai.digitalocean_key)
            elif provider_name == "gemini" and config.ai.gemini_key:
                return GeminiProvider(config.ai.gemini_key)
            elif provider_name == "claude" and config.ai.anthropic_key:
                return ClaudeProvider(config.ai.anthropic_key)
            elif provider_name == "openai" and config.ai.openai_key:
                return OpenAIProvider(config.ai.openai_key)
            else:
                print(f"Error: Provider '{provider_name}' not available or API key not set.")
                sys.exit(1)

        # Use default provider if set
        if config.ai.default_provider:
            default = config.ai.default_provider
            if default == "digitalocean" and config.ai.digitalocean_key:
                return DigitalOceanProvider(config.ai.digitalocean_key)
            elif default == "gemini" and config.ai.gemini_key:
                return GeminiProvider(config.ai.gemini_key)
            elif default == "claude" and config.ai.anthropic_key:
                return ClaudeProvider(config.ai.anthropic_key)
            elif default == "openai" and config.ai.openai_key:
                return OpenAIProvider(config.ai.openai_key)

        # Fall back to first available
        if config.ai.digitalocean_key:
            return DigitalOceanProvider(config.ai.digitalocean_key)
        elif config.ai.gemini_key:
            return GeminiProvider(config.ai.gemini_key)
        elif config.ai.anthropic_key:
            return ClaudeProvider(config.ai.anthropic_key)
        elif config.ai.openai_key:
            return OpenAIProvider(config.ai.openai_key)

        print("Error: No API key found.")
        print("Please set one of the following environment variables or create a .env file:")
        print("  - DIGITALOCEAN_API_KEY")
        print("  - GEMINI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - OPENAI_API_KEY")
        print("\nSee .env.example for reference.")
        sys.exit(1)

    @staticmethod
    def list_available() -> Dict[str, bool]:
        """
        List available providers and their status.

        Returns:
            Dict mapping provider name to availability status
        """
        return {
            "digitalocean": bool(config.ai.digitalocean_key),
            "gemini": bool(config.ai.gemini_key),
            "claude": bool(config.ai.anthropic_key),
            "openai": bool(config.ai.openai_key),
        }
