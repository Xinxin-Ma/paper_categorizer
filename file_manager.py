"""
File Manager Module

Handles file and folder operations for paper organization.

Responsibilities:
    - Create category folder structure
    - Move/rename files
    - Scan folders for papers
    - List PDFs in Inbox
"""

import re
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from .config import config
from .categories import category_manager
from .pdf_utils import filename_to_title


@dataclass
class PaperFile:
    """Represents a PDF file."""
    path: Path
    filename: str
    title: str

    @classmethod
    def from_path(cls, path: Path) -> 'PaperFile':
        return cls(
            path=path,
            filename=path.name,
            title=filename_to_title(path.name)
        )


@dataclass
class CategorizedPaper:
    """Represents a paper found in category folders."""
    path: Path
    filename: str
    title: str
    category_folder: str
    subcategory_folder: Optional[str]
    category_code: Optional[str]


class FileManager:
    """
    Manages file operations for paper organization.

    Usage:
        fm = FileManager()

        # Get PDFs from inbox
        papers = fm.get_inbox_papers()

        # Move a paper to category folder
        fm.move_to_category(paper.path, "1.1.2")

        # Create all category folders
        fm.create_category_folders()
    """

    def __init__(self):
        self.inbox_path = config.paths.inbox
        self.output_path = config.paths.auto_category  # Default, may be overridden

    def get_output_path(self) -> Path:
        """Get the actual output path (from category_manager if loaded, else default)."""
        if category_manager._loaded and category_manager.category_root:
            return category_manager.category_root
        return self.output_path

    # =========================================================================
    # Inbox Operations
    # =========================================================================

    def get_inbox_papers(self) -> List[PaperFile]:
        """
        Get all PDF files from the Inbox folder.

        Returns:
            List of PaperFile objects
        """
        if not self.inbox_path.exists():
            return []

        pdf_files = list(self.inbox_path.glob("*.pdf")) + list(self.inbox_path.glob("*.PDF"))
        return [PaperFile.from_path(p) for p in pdf_files]

    def ensure_inbox_exists(self) -> Path:
        """Create Inbox folder if it doesn't exist."""
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        return self.inbox_path

    def inbox_paper_count(self) -> int:
        """Get count of PDFs in Inbox."""
        return len(self.get_inbox_papers())

    # =========================================================================
    # Category Folder Operations
    # =========================================================================

    def scan_existing_folders(self, scan_path: Path = None) -> Dict:
        """
        Scan existing category folders and generate category hierarchy.

        Handles:
        - Numbered folders: "1. Category Name" or "1.1 Subcategory"
        - Unnumbered folders: "Category Name" (will auto-assign numbers starting from 1)
        - Flat structures (no subcategories)
        - Recursive structures (nested subcategories)

        Args:
            scan_path: Path to scan. Defaults to output_path (Papers Auto Category).
                       Pass papers_root to scan the parent directory directly.

        Returns:
            Dict suitable for categories.json (ordered by category number)
        """
        target_path = scan_path or self.output_path

        if not target_path.exists():
            return {}

        # Pattern to match numbered folder names like "1. Category" or "1 Category"
        numbered_pattern = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$')

        # Collect all top-level folders (exclude special folders)
        exclude_folders = {'Inbox', 'paper_categorizer', '.git', '__pycache__', 'venv', 'Papers Auto Category'}
        folders = []
        for item in sorted(target_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.') and item.name not in exclude_folders:
                folders.append(item)

        if not folders:
            return {}

        # Separate numbered vs unnumbered folders
        numbered_folders = []  # List of (folder, code_str)
        unnumbered_folders = []  # List of folder

        for folder in folders:
            match = numbered_pattern.match(folder.name)
            if match and '.' not in match.group(1):  # Main category (no dots in code)
                numbered_folders.append((folder, match.group(1)))
            else:
                unnumbered_folders.append(folder)

        # Build categories dict - collect all first, then sort by number
        categories_list = []  # List of (code_int, code_str, category_dict, folder)

        # Process numbered folders first
        for folder, code in numbered_folders:
            cat_dict = {
                "name": folder.name,
                "description": "",
                "keywords": [],
                "subcategories": {}
            }
            self._scan_subcategories(folder, code, cat_dict["subcategories"], numbered_pattern)
            categories_list.append((int(code), code, cat_dict, folder))

        # Auto-number unnumbered folders starting from 1 (or next available)
        used_nums = {item[0] for item in categories_list}
        next_num = 1

        for folder in unnumbered_folders:
            # Find next unused number
            while next_num in used_nums:
                next_num += 1

            code = str(next_num)
            cat_dict = {
                "name": folder.name,
                "description": "",
                "keywords": [],
                "subcategories": {},
                "_auto_numbered": True
            }
            # Use the enhanced subcategory scanner for all folders
            self._scan_subcategories(folder, code, cat_dict["subcategories"], numbered_pattern)
            categories_list.append((next_num, code, cat_dict, folder))
            used_nums.add(next_num)
            next_num += 1

        # Sort by category number and build final dict
        categories_list.sort(key=lambda x: x[0])
        categories = {}
        for _, code, cat_dict, _ in categories_list:
            categories[code] = cat_dict

        # Add Uncategorized as category 0 if not present
        has_uncategorized = any(
            "uncategorized" in info.get("name", "").lower()
            for info in categories.values()
        )
        if not has_uncategorized:
            categories["0"] = {
                "name": "0. Uncategorized",
                "description": "Papers that don't fit into existing categories",
                "keywords": [],
                "subcategories": {}
            }

        return categories

    def _scan_subcategories(self, parent_path: Path, parent_code: str,
                            subcategories: Dict, pattern: re.Pattern) -> None:
        """Recursively scan for subcategories (supports multiple formats)."""
        # Pattern for "NN-Name" format (e.g., "01-LLM_Applications")
        dash_pattern = re.compile(r'^(\d+)-(.+)$')

        for item in sorted(parent_path.iterdir()):
            if not item.is_dir() or item.name.startswith('.'):
                continue

            # Try standard numbered format first (e.g., "1.1 Subcategory")
            match = pattern.match(item.name)
            if match:
                code = match.group(1)
                rel_path = str(item.relative_to(parent_path.parent))
                subcategories[code] = rel_path
                self._scan_subcategories(item, code, subcategories, pattern)
                continue

            # Try dash format (e.g., "01-LLM_Applications")
            dash_match = dash_pattern.match(item.name)
            if dash_match:
                sub_num = dash_match.group(1).lstrip('0') or '0'  # Remove leading zeros
                code = f"{parent_code}.{sub_num}"
                # Store just the folder name as the path
                subcategories[code] = item.name
                # Recurse into deeper subcategories
                self._scan_subcategories(item, code, subcategories, pattern)

    def _scan_subcategories_unnumbered(self, parent_path: Path, parent_code: str,
                                        subcategories: Dict) -> None:
        """Scan for unnumbered subcategories and auto-assign numbers."""
        subfolders = []
        for item in sorted(parent_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                subfolders.append(item)

        for i, folder in enumerate(subfolders, 1):
            code = f"{parent_code}.{i}"
            # Keep original folder path (don't rename on disk)
            rel_path = folder.name  # Just the subfolder name
            subcategories[code] = rel_path
            subcategories[f"_original_{code}"] = folder.name  # Track original for display

            # Recurse (but typically we keep it flat for unnumbered)
            # Uncomment below to support deep nesting for unnumbered folders
            # self._scan_subcategories_unnumbered(folder, code, subcategories)

    def has_existing_folders(self, path: Path = None) -> bool:
        """Check if category folders already exist."""
        check_path = path or self.output_path
        if not check_path.exists():
            return False

        for item in check_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                return True
        return False

    def has_existing_folders_in_root(self) -> bool:
        """Check if category folders exist directly in papers_root (parent folder)."""
        root_path = config.paths.papers_root
        if not root_path.exists():
            return False

        # Folders to exclude (not actual categories)
        exclude_folders = {'Inbox', 'paper_categorizer', '.git', '__pycache__', 'venv', 'Papers Auto Category'}

        for item in root_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in exclude_folders:
                return True
        return False

    def create_category_folders(self) -> None:
        """Create all category folders based on category hierarchy."""
        category_manager.ensure_loaded()
        output_path = self.get_output_path()

        output_path.mkdir(exist_ok=True)

        for cat_num, info in category_manager.hierarchy.items():
            main_path = output_path / info["name"]
            main_path.mkdir(exist_ok=True)

            for sub_code, sub_path in info.get("subcategories", {}).items():
                full_path = main_path / sub_path
                full_path.mkdir(parents=True, exist_ok=True)

    def move_to_category(self, source_path: Path, category_code: str) -> Path:
        """
        Move a file to the appropriate category folder.

        Args:
            source_path: Path to the source file
            category_code: Category code (e.g., "1.1.2")

        Returns:
            Path to the destination file
        """
        category_manager.ensure_loaded()

        folder_path = category_manager.get_folder_path(category_code)
        dest_folder = self.get_output_path() / folder_path
        dest_folder.mkdir(parents=True, exist_ok=True)

        dest_path = dest_folder / source_path.name

        # Handle filename conflicts
        if dest_path.exists() and dest_path != source_path:
            counter = 1
            stem = dest_path.stem
            suffix = dest_path.suffix
            while dest_path.exists():
                dest_path = dest_folder / f"{stem} ({counter}){suffix}"
                counter += 1

        shutil.move(str(source_path), str(dest_path))
        return dest_path

    def get_category_folder_path(self, category_code: str) -> Path:
        """Get the full path to a category folder."""
        category_manager.ensure_loaded()
        folder_path = category_manager.get_folder_path(category_code)
        return self.get_output_path() / folder_path

    # =========================================================================
    # File Rename Operations
    # =========================================================================

    def rename_file(self, file_path: Path, new_title: str) -> Path:
        """
        Rename a file to match a title.

        Args:
            file_path: Path to the file
            new_title: New title for the file

        Returns:
            Path to the renamed file
        """
        # Clean title for filename
        clean_title = re.sub(r'[<>:"/\\|?*]', '', new_title)
        clean_title = clean_title[:config.app.max_filename_length].strip()

        new_filename = f"{clean_title}.pdf"
        new_path = file_path.parent / new_filename

        if new_path == file_path:
            return file_path

        # Handle conflicts
        if new_path.exists():
            counter = 1
            while new_path.exists():
                new_filename = f"{clean_title} ({counter}).pdf"
                new_path = file_path.parent / new_filename
                counter += 1

        try:
            file_path.rename(new_path)
            print(f"  Renamed: {file_path.name} -> {new_filename}")
            return new_path
        except Exception as e:
            print(f"  Warning: Could not rename file: {e}")
            return file_path

    # =========================================================================
    # Scanning Operations
    # =========================================================================

    def scan_categorized_papers(self) -> Dict[str, List[CategorizedPaper]]:
        """
        Scan all categorized papers in the output folder.

        Returns:
            Dict mapping category folder names to lists of papers
        """
        all_papers: Dict[str, List[CategorizedPaper]] = {}
        output_path = self.get_output_path()

        if not output_path.exists():
            return all_papers

        for pdf_path in output_path.rglob("*.pdf"):
            rel_path = pdf_path.relative_to(output_path)
            parts = str(rel_path.parent).split("/")

            if parts and parts[0] and parts[0] != ".":
                main_cat = parts[0]
                if main_cat not in all_papers:
                    all_papers[main_cat] = []

                # Extract category code from subfolder
                subcat_code = None
                if len(parts) > 1:
                    subfolder = parts[-1]
                    match = re.match(r'^(\d+(?:\.\d+)*)', subfolder)
                    if match:
                        subcat_code = match.group(1)

                paper = CategorizedPaper(
                    path=pdf_path,
                    filename=pdf_path.name,
                    title=filename_to_title(pdf_path.name),
                    category_folder=main_cat,
                    subcategory_folder="/".join(parts[1:]) if len(parts) > 1 else None,
                    category_code=subcat_code
                )
                all_papers[main_cat].append(paper)

        return all_papers

    def count_uncategorized(self) -> int:
        """Count papers in the Uncategorized folder."""
        uncat_folder = self.get_output_path() / category_manager.get_uncategorized_folder()
        if not uncat_folder.exists():
            return 0

        pdf_count = len(list(uncat_folder.glob("*.pdf")))
        pdf_count += len(list(uncat_folder.glob("*.PDF")))
        return pdf_count

    def get_uncategorized_papers(self) -> List[PaperFile]:
        """Get all papers in the Uncategorized folder."""
        uncat_folder = self.get_output_path() / category_manager.get_uncategorized_folder()
        if not uncat_folder.exists():
            return []

        pdf_files = list(uncat_folder.glob("*.pdf")) + list(uncat_folder.glob("*.PDF"))
        return [PaperFile.from_path(p) for p in pdf_files]


# Global instance for convenience
file_manager = FileManager()
