"""
Categories Module

Manages the category hierarchy for paper classification.

Responsibilities:
    - Load/save categories from JSON
    - Generate category prompts for AI
    - Map category codes to folder paths
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from .config import config


class CategoriesNotFoundError(Exception):
    """Raised when categories.json doesn't exist and needs initialization."""
    pass


@dataclass
class CategoryInfo:
    """Information about a single category."""
    code: str
    name: str
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    subcategories: Dict[str, str] = field(default_factory=dict)


class CategoryManager:
    """
    Manages the category hierarchy.

    Usage:
        manager = CategoryManager()
        manager.load()

        # Get folder path for a category
        path = manager.get_folder_path("1.1.2")

        # Generate AI prompt
        prompt = manager.generate_prompt()
    """

    def __init__(self):
        self.hierarchy: Dict[str, Dict] = {}
        self.threshold: int = config.app.uncategorized_threshold
        self._loaded = False

    def load(self) -> bool:
        """
        Load categories from JSON file.

        Returns:
            True if loaded successfully.

        Raises:
            CategoriesNotFoundError if categories.json doesn't exist.
        """
        if not config.paths.categories_file.exists():
            raise CategoriesNotFoundError(
                f"categories.json not found at {config.paths.categories_file}"
            )

        try:
            with open(config.paths.categories_file, 'r') as f:
                data = json.load(f)
                self.hierarchy = data.get("categories", {})
                self.threshold = data.get("uncategorized_threshold", config.app.uncategorized_threshold)
                self._loaded = True
                return True
        except json.JSONDecodeError as e:
            print(f"Error: categories.json is not valid JSON: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: Could not load categories.json: {e}")
            sys.exit(1)

    def save(self) -> None:
        """Save categories to JSON file."""
        data = {
            "version": "2.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "uncategorized_threshold": self.threshold,
            "categories": self.hierarchy
        }
        with open(config.paths.categories_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_folder_path(self, category_code: str) -> Path:
        """
        Get the folder path for a category code.

        Args:
            category_code: e.g., "1.1.2"

        Returns:
            Relative path like "1. Multi-Armed.../1.1 Contextual.../1.1.2 Neural..."
        """
        main_cat = category_code.split(".")[0]

        if main_cat not in self.hierarchy:
            return self.get_uncategorized_folder()

        cat_info = self.hierarchy[main_cat]

        if "." in category_code and cat_info.get("subcategories"):
            if category_code in cat_info["subcategories"]:
                return Path(cat_info["name"]) / cat_info["subcategories"][category_code]

        return Path(cat_info["name"])

    def get_full_name(self, category_code: str) -> str:
        """
        Get the full category name with code.

        Args:
            category_code: e.g., "1.1.2"

        Returns:
            e.g., "1.1.2 Neural & Non-linear Contextual Bandits"
        """
        main_cat = category_code.split(".")[0]

        if main_cat not in self.hierarchy:
            return self.get_uncategorized_name()

        cat_info = self.hierarchy[main_cat]

        if "." in category_code and cat_info.get("subcategories"):
            subcat_path = cat_info["subcategories"].get(category_code, "")
            if subcat_path:
                parts = subcat_path.split("/")
                return parts[-1] if parts else category_code

        return cat_info["name"]

    def get_main_category_name(self, category_code: str) -> str:
        """Get the main category name for a code."""
        main_cat = category_code.split(".")[0]
        if main_cat in self.hierarchy:
            return self.hierarchy[main_cat]["name"]
        return self.get_uncategorized_name()

    def generate_prompt(self) -> str:
        """
        Generate category hierarchy text for AI prompts.

        Returns:
            Formatted markdown text of all categories.
        """
        lines = ["## Complete Category Hierarchy\n"]

        sorted_cats = sorted(self.hierarchy.keys(), key=lambda x: int(x))

        for cat_num in sorted_cats:
            cat_info = self.hierarchy[cat_num]
            cat_name = cat_info["name"]

            name_part = cat_name.split(". ", 1)[-1] if ". " in cat_name else cat_name
            lines.append(f"\n### {cat_num}. {name_part}")

            subcats = cat_info.get("subcategories", {})
            if subcats:
                sorted_subcats = sorted(subcats.keys(), key=lambda x: [int(p) for p in x.split(".")])

                for subcat_code in sorted_subcats:
                    subcat_path = subcats[subcat_code]
                    subcat_name = subcat_path.split("/")[-1] if "/" in subcat_path else subcat_path

                    depth = subcat_code.count(".")
                    indent = "  " * (depth - 1)
                    lines.append(f"{indent}- {subcat_name}")

        uncat_code = self.get_uncategorized_code()
        uncat_name = self.get_uncategorized_name()
        lines.append(f"\n(Use {uncat_name} only if paper truly doesn't fit any category)")

        return "\n".join(lines)

    def get_all_folder_names(self) -> List[str]:
        """Get list of all main category folder names."""
        return [info["name"] for info in self.hierarchy.values()]

    def get_uncategorized_code(self) -> str:
        """
        Get the code for the Uncategorized category.

        Searches for a category with 'Uncategorized' in its name.
        Falls back to the highest numbered category if not found.
        """
        for code, info in self.hierarchy.items():
            if "uncategorized" in info.get("name", "").lower():
                return code

        # Fallback: return highest number
        if self.hierarchy:
            return max(self.hierarchy.keys(), key=lambda x: int(x))
        return "1"

    def get_uncategorized_folder(self) -> Path:
        """Get the folder path for uncategorized papers."""
        code = self.get_uncategorized_code()
        if code in self.hierarchy:
            return Path(self.hierarchy[code]["name"])
        return Path("Uncategorized")

    def get_uncategorized_name(self) -> str:
        """Get the full name of the Uncategorized category."""
        code = self.get_uncategorized_code()
        if code in self.hierarchy:
            return self.hierarchy[code]["name"]
        return "Uncategorized"

    def ensure_loaded(self) -> None:
        """Ensure categories are loaded."""
        if not self._loaded:
            self.load()

    def is_initialized(self) -> bool:
        """Check if categories.json exists."""
        return config.paths.categories_file.exists()


# Global instance for convenience
category_manager = CategoryManager()
