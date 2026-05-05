"""
Configuration Module

Single source of truth for all configuration settings.
Loads from environment variables and .env file.

Responsibilities:
    - Load environment variables
    - Define paths (Inbox, Output, Zotero)
    - Provide configuration access via Config class
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass


@dataclass
class PathConfig:
    """File system paths configuration."""
    script_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    papers_root: Path = field(init=False)
    inbox: Path = field(init=False)
    auto_category: Path = field(init=False)
    summary_file: Path = field(init=False)
    categories_file: Path = field(init=False)

    def __post_init__(self):
        self.papers_root = self.script_dir.parent
        self.inbox = self.papers_root / "Inbox"
        self.auto_category = self.papers_root / "Papers Auto Category"
        self.summary_file = self.papers_root / "Papers_Summary.md"
        self.categories_file = self.script_dir / "categories.json"


@dataclass
class ZoteroConfig:
    """Zotero integration configuration."""
    enabled: bool = field(default_factory=lambda: os.environ.get("ZOTERO_ENABLED", "false").lower() == "true")
    db_path: Path = field(default_factory=lambda: Path(os.environ.get("ZOTERO_DB_PATH", "~/Zotero/zotero.sqlite")).expanduser())
    storage_path: Path = field(default_factory=lambda: Path(os.environ.get("ZOTERO_STORAGE_PATH", "~/Zotero/storage")).expanduser())
    temp_backup_path: Path = field(init=False)

    def __post_init__(self):
        self.temp_backup_path = self.db_path.parent / "zotero_temp_backup.sqlite"


@dataclass
class AIConfig:
    """AI provider configuration."""
    digitalocean_key: Optional[str] = field(default_factory=lambda: os.environ.get("DIGITALOCEAN_API_KEY"))
    gemini_key: Optional[str] = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY"))
    anthropic_key: Optional[str] = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY"))
    openai_key: Optional[str] = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY"))
    default_provider: Optional[str] = field(default_factory=lambda: os.environ.get("DEFAULT_PROVIDER", "").lower() or None)

    # Model names
    digitalocean_model: str = "anthropic-claude-4.5-sonnet"
    gemini_model: str = "gemini-2.0-flash"
    claude_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4o-mini"


@dataclass
class AppConfig:
    """Application-level configuration."""
    uncategorized_threshold: int = 20
    max_pdf_pages: int = 3
    max_abstract_length: int = 2000
    max_filename_length: int = 150


class Config:
    """
    Main configuration container.

    Usage:
        from paper_categorizer.config import Config

        config = Config()
        print(config.paths.inbox)
        print(config.zotero.enabled)
        print(config.ai.gemini_key)
    """
    _instance: Optional['Config'] = None

    def __new__(cls):
        """Singleton pattern - only one Config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.paths = PathConfig()
        self.zotero = ZoteroConfig()
        self.ai = AIConfig()
        self.app = AppConfig()
        self._initialized = True

    def reload(self):
        """Reload configuration from environment."""
        self._initialized = False
        self.__init__()

    @property
    def has_any_ai_key(self) -> bool:
        """Check if any AI API key is configured."""
        return bool(self.ai.digitalocean_key or self.ai.gemini_key or self.ai.anthropic_key or self.ai.openai_key)

    def get_available_providers(self) -> list:
        """Get list of available AI providers."""
        providers = []
        if self.ai.digitalocean_key:
            providers.append("digitalocean")
        if self.ai.gemini_key:
            providers.append("gemini")
        if self.ai.anthropic_key:
            providers.append("claude")
        if self.ai.openai_key:
            providers.append("openai")
        return providers


# Global config instance for convenience
config = Config()
