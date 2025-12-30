"""
Summarizer Module

Generates Papers_Summary.md from categorized papers.

Responsibilities:
    - Generate markdown summary
    - Include newly processed papers section
    - Calculate statistics
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

from .config import config
from .categories import category_manager
from .file_manager import file_manager


@dataclass
class ProcessingResult:
    """Result of processing a single paper."""
    filename: str
    title: str
    category_code: str
    category_name: str
    full_category: str
    folder_path: str
    confidence: str
    reasoning: str
    status: str  # success, error
    error: Optional[str] = None
    zotero_action: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "filename": self.filename,
            "title": self.title,
            "category_code": self.category_code,
            "category_name": self.category_name,
            "full_category": self.full_category,
            "folder_path": self.folder_path,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "status": self.status,
            "error": self.error,
            "zotero_action": self.zotero_action,
        }


class Summarizer:
    """
    Generates Papers_Summary.md.

    Usage:
        summarizer = Summarizer()

        # Generate summary with newly processed papers
        summarizer.generate(results)

        # Generate summary from existing folders only
        summarizer.generate()
    """

    def __init__(self):
        self.summary_path = config.paths.summary_file

    def generate(self, results: Optional[List[ProcessingResult]] = None) -> None:
        """
        Generate the Papers_Summary.md file.

        Args:
            results: Optional list of newly processed papers to highlight
        """
        print("\nUpdating Papers_Summary.md...")

        category_manager.ensure_loaded()

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        content = self._build_header(now)

        # Add newly processed section if results provided
        if results:
            content += self._build_newly_processed_section(results)

        # Add all categories
        content += self._build_categories_section()

        # Add statistics
        content += self._build_statistics_section()

        # Write file
        with open(self.summary_path, 'w') as f:
            f.write(content)

        print(f"Updated {self.summary_path}")

    def _build_header(self, timestamp: str) -> str:
        """Build the header section."""
        return f"""# Papers Collection Summary

A categorized summary of research papers organized by research area.

**Last Updated:** {timestamp}

---

"""

    def _build_newly_processed_section(self, results: List[ProcessingResult]) -> str:
        """Build the newly processed papers section."""
        content = """## Newly Processed Papers

Papers added in the latest batch processing run:

| Paper Title | Category | Confidence |
|-------------|----------|------------|
"""
        # Sort by category code
        sorted_results = sorted(results, key=lambda x: x.category_code)

        for r in sorted_results:
            title = r.title[:60] + "..." if len(r.title) > 60 else r.title
            status_icon = "" if r.status == "success" else " (error)"
            content += f"| {title} | {r.full_category} | {r.confidence}{status_icon} |\n"

        content += f"\n**Total processed:** {len(results)} papers\n\n---\n\n"
        return content

    def _build_categories_section(self) -> str:
        """Build the categories section with all papers."""
        content = ""

        # Scan all papers
        all_papers = file_manager.scan_categorized_papers()

        # Get all category folder names
        all_category_folders = category_manager.get_all_folder_names()

        # Track statistics
        total_papers = 0
        categories_with_papers = 0

        # Sort categories by number
        sorted_cats = sorted(
            all_category_folders,
            key=lambda x: (int(re.match(r'(\d+)', x).group(1)) if re.match(r'(\d+)', x) else 99, x)
        )

        for cat_folder in sorted_cats:
            papers = all_papers.get(cat_folder, [])

            if papers:
                categories_with_papers += 1
                total_papers += len(papers)

            # Get category description
            cat_match = re.match(r'(\d+)', cat_folder)
            description = ""
            if cat_match:
                cat_info = category_manager.hierarchy.get(cat_match.group(1), {})
                description = cat_info.get("description", "")

            content += f"## {cat_folder}\n\n"
            if description:
                content += f"{description}\n\n"

            if papers:
                content += "| Paper Title | Category Code | Subfolder |\n"
                content += "|-------------|---------------|----------|\n"

                # Sort papers by subcategory code, then title
                sorted_papers = sorted(
                    papers,
                    key=lambda x: (x.category_code or "99", x.title)
                )

                for paper in sorted_papers:
                    subfolder = paper.subcategory_folder or "-"
                    title = paper.title[:70] + "..." if len(paper.title) > 70 else paper.title
                    subcat = paper.category_code or "-"
                    content += f"| {title} | {subcat} | {subfolder} |\n"

                content += f"\n**Papers in this category:** {len(papers)}\n"
            else:
                content += "*No papers in this category yet.*\n"

            content += "\n---\n\n"

        self._total_papers = total_papers
        self._categories_with_papers = categories_with_papers

        return content

    def _build_statistics_section(self) -> str:
        """Build the statistics section."""
        return f"""## Statistics

| Metric | Value |
|--------|-------|
| Total Papers | {getattr(self, '_total_papers', 0)} |
| Categories with Papers | {getattr(self, '_categories_with_papers', 0)} |
| Total Categories | {len(category_manager.hierarchy)} |

---

*Auto-generated by paper_categorizer*
"""


# Global instance for convenience
summarizer = Summarizer()
