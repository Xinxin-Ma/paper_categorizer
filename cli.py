"""
CLI Module

Command-line interface for the paper categorizer.

Responsibilities:
    - Argument parsing
    - Command handlers
    - User interaction
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List

from .config import config
from .categories import category_manager, CategoriesNotFoundError
from .ai_providers import ProviderFactory, AIProvider
from .pdf_utils import extract_text, extract_text_ocr, is_pdf_support_available, is_ocr_available, filename_to_title
from .zotero_db import zotero_db
from .file_manager import file_manager, PaperFile
from .summarizer import summarizer, ProcessingResult


class CLI:
    """
    Command-line interface for paper categorization.

    Usage:
        cli = CLI()
        cli.run()
    """

    def __init__(self):
        self.parser = self._create_parser()

    def run(self, args: Optional[List[str]] = None) -> None:
        """Run the CLI with the given arguments."""
        parsed = self.parser.parse_args(args)
        self._execute(parsed)

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="Categorize academic papers using AI APIs (Gemini, Claude, or OpenAI)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # First-time setup
  python -m paper_categorizer --init

  # Interactive mode
  python -m paper_categorizer --interactive

  # Batch process Inbox
  python -m paper_categorizer --batch

  # Dry run (preview)
  python -m paper_categorizer --batch --dry-run

  # Use specific provider
  python -m paper_categorizer --batch --provider claude

  # Single paper
  python -m paper_categorizer --title "Neural Bandits for Recommendation"

  # Check status
  python -m paper_categorizer --zotero-status
            """
        )

        # Setup commands
        parser.add_argument("--init", action="store_true",
                           help="Initialize categories.json and folder structure")

        # Categorization modes
        parser.add_argument("--title", "-t", help="Paper title to categorize")
        parser.add_argument("--abstract", "-a", help="Paper abstract (optional)")
        parser.add_argument("--interactive", "-i", action="store_true",
                           help="Interactive mode")
        parser.add_argument("--batch", "-b", action="store_true",
                           help="Batch process Inbox folder")
        parser.add_argument("--dry-run", action="store_true",
                           help="Preview without moving files")

        # Provider options
        parser.add_argument("--provider", "-p", choices=["gemini", "claude", "openai"],
                           help="AI provider to use")

        # Info commands
        parser.add_argument("--list-categories", "-l", action="store_true",
                           help="List all categories")
        parser.add_argument("--list-providers", action="store_true",
                           help="List available AI providers")
        parser.add_argument("--zotero-status", action="store_true",
                           help="Check Zotero status")
        parser.add_argument("--sync-zotero", action="store_true",
                           help="Sync Zotero collection names to match categories.json")
        parser.add_argument("--check-threshold", action="store_true",
                           help="Check uncategorized threshold")

        # Utility commands
        parser.add_argument("--update-summary", action="store_true",
                           help="Update Papers_Summary.md")
        parser.add_argument("--suggest-categories", action="store_true",
                           help="Get AI suggestions for new categories")

        return parser

    def _execute(self, args) -> None:
        """Execute the appropriate command."""
        # Commands that don't require categories
        if args.init:
            self._cmd_init()
            return
        elif args.list_providers:
            self._cmd_list_providers()
            return
        elif args.zotero_status:
            self._cmd_zotero_status()
            return
        elif args.sync_zotero:
            self._cmd_sync_zotero()
            return

        # Check if categories exist for other commands
        if not category_manager.is_initialized():
            self._prompt_first_time_setup()
            return

        # Load categories
        try:
            category_manager.load()
        except CategoriesNotFoundError:
            self._prompt_first_time_setup()
            return

        # Handle commands that require categories
        if args.list_categories:
            self._cmd_list_categories()
        elif args.check_threshold:
            self._cmd_check_threshold()
        elif args.update_summary:
            self._cmd_update_summary()
        elif args.interactive:
            self._cmd_interactive(args.provider)
        elif args.batch:
            self._cmd_batch(args.provider, args.dry_run)
        elif args.title:
            self._cmd_single(args.title, args.abstract, args.provider)
        elif args.suggest_categories:
            self._cmd_suggest_categories(args.provider)
        else:
            self.parser.print_help()

    # =========================================================================
    # Command Handlers
    # =========================================================================

    def _prompt_first_time_setup(self) -> None:
        """Prompt user to run first-time setup."""
        print("\n" + "="*60)
        print("First-Time Setup Required")
        print("="*60)
        print(f"\ncategories.json not found at:")
        print(f"  {config.paths.categories_file}")
        print("\nTo get started, run:")
        print("  python -m paper_categorizer --init")
        print("\nThis will guide you through setting up your paper categories.")
        print("="*60 + "\n")

    def _cmd_init(self) -> None:
        """Initialize the system with user-provided categories."""
        print("\n" + "="*60)
        print("Paper Categorization System - Setup")
        print("="*60)

        # Step 1: Ensure Inbox folder exists
        self._ensure_inbox_setup()

        # Case 1: categories.json already exists
        if config.paths.categories_file.exists():
            print(f"\ncategories.json already exists at {config.paths.categories_file}")
            print("\nOptions:")
            print("  1. Keep existing categories and update folders")
            print("  2. Create new categories from template")
            response = input("\nChoice (1/2): ").strip()
            if response != '2':
                print("\nKeeping existing categories.")
                category_manager.load()
                print("Creating folder structure...")
                file_manager.create_category_folders()
                print(f"Folder structure updated in {config.paths.auto_category}")
                return

        # Case 2: Check for existing folders - first in root directory, then in auto_category
        root_has_folders = file_manager.has_existing_folders_in_root()
        auto_has_folders = file_manager.has_existing_folders()

        if root_has_folders or auto_has_folders:
            if root_has_folders:
                scan_path = config.paths.papers_root
                print(f"\nFound existing category folders in {config.paths.papers_root}")
            else:
                scan_path = config.paths.auto_category
                print(f"\nFound existing category folders in {config.paths.auto_category}")

            print("\nOptions:")
            print("  1. Generate categories.json from existing folders (recommended)")
            print("  2. Create new categories from template (ignores existing folders)")
            response = input("\nChoice (1/2): ").strip()

            if response != '2':
                print("\nScanning existing folders...")
                categories = file_manager.scan_existing_folders(scan_path)

                if categories:
                    # Check for auto-numbered (originally unnumbered) folders
                    auto_numbered = []
                    for code, info in categories.items():
                        if info.get("_auto_numbered"):
                            auto_numbered.append((code, info["name"]))
                            del info["_auto_numbered"]
                        # Clean up subcategory originals
                        subcats = info.get("subcategories", {})
                        for key in list(subcats.keys()):
                            if key.startswith("_original_"):
                                del subcats[key]

                    data = {
                        "version": "2.0",
                        "last_updated": "",
                        "uncategorized_threshold": 20,
                        "categories": categories
                    }

                    # Save category_root if using root directory (not default auto_category)
                    if scan_path == config.paths.papers_root:
                        data["category_root"] = str(scan_path)

                    with open(config.paths.categories_file, 'w') as f:
                        json.dump(data, f, indent=2)

                    print(f"\nGenerated categories.json with {len(categories)} categories:")
                    for code in sorted(categories.keys(), key=lambda x: int(x)):
                        cat_name = categories[code]["name"]
                        subcat_count = len([k for k in categories[code].get("subcategories", {}).keys()
                                           if not k.startswith("_")])
                        print(f"  {cat_name} ({subcat_count} subcategories)")

                    if auto_numbered:
                        print("\nNote: The following folders were auto-numbered:")
                        for code, folder_name in auto_numbered:
                            print(f"  Code {code} -> '{folder_name}'")
                        print("\nFolder names on disk are NOT changed.")
                        print("Edit categories.json if you want different numbers.")

                    print(f"\nSaved to: {config.paths.categories_file}")
                    print("\nYou can edit categories.json to adjust names, descriptions, and keywords.")
                    return
                else:
                    print("No valid category folders found. Creating template instead.")

        # Case 3: Create from template
        self._create_template_categories()

    def _create_template_categories(self) -> None:
        """Create a template categories.json file."""
        template = {
            "version": "2.0",
            "last_updated": "",
            "uncategorized_threshold": 20,
            "categories": {
                "0": {
                    "name": "0. Uncategorized",
                    "description": "Papers that don't fit into existing categories",
                    "keywords": [],
                    "subcategories": {}
                },
                "1": {
                    "name": "1. Example Category",
                    "description": "Description of this category",
                    "keywords": ["keyword1", "keyword2"],
                    "subcategories": {
                        "1.1": "1.1 Subcategory Example"
                    }
                },
                "2": {
                    "name": "2. Another Category",
                    "description": "Another category description",
                    "keywords": ["keyword3"],
                    "subcategories": {}
                }
            }
        }

        print("\nCreating categories.json template...")
        with open(config.paths.categories_file, 'w') as f:
            json.dump(template, f, indent=2)

        print(f"\nCreated: {config.paths.categories_file}")
        print("\n" + "-"*60)
        print("IMPORTANT: Edit categories.json to define your categories!")
        print("-"*60)
        print("\nThe template includes example categories. You should:")
        print("  1. Open categories.json in a text editor")
        print("  2. Replace example categories with your own")
        print("  3. Add as many categories and subcategories as needed")
        print("  4. Run --init again to create the folder structure")
        print("\nCategory format:")
        print('''  {
    "1": {
      "name": "1. Category Name",
      "description": "What papers belong here",
      "keywords": ["keyword1", "keyword2"],
      "subcategories": {
        "1.1": "1.1 Subcategory Name",
        "1.1.1": "1.1 Subcategory Name/1.1.1 Sub-subcategory"
      }
    }
  }''')
        print("\nAfter editing, run:")
        print("  python -m paper_categorizer --init")
        print("\nTo see your categories:")
        print("  python -m paper_categorizer --list-categories")

    def _cmd_list_categories(self) -> None:
        """List all categories."""
        print(category_manager.generate_prompt())

    def _cmd_list_providers(self) -> None:
        """List available AI providers."""
        print("\nAvailable AI Providers:")
        print("-" * 40)

        providers = ProviderFactory.list_available()

        for name, available in providers.items():
            status = "[x]" if available else "[ ]"
            key_status = "key set" if available else "key not set"
            print(f"  {status} {name.capitalize()} ({key_status})")

        print("\nTo install libraries:")
        print("  pip install google-generativeai anthropic openai python-dotenv")

    def _cmd_zotero_status(self) -> None:
        """Show Zotero status."""
        print("\n" + "="*50)
        print("Zotero Integration Status")
        print("="*50)

        status = zotero_db.get_status()

        print(f"Enabled: {'Yes' if status['enabled'] else 'No'}")

        if status['enabled']:
            print(f"Database path: {status['db_path']}")
            print(f"Database exists: {'Yes' if status['db_exists'] else 'No'}")
            print(f"Storage path: {status['storage_path']}")
            print(f"Storage exists: {'Yes' if status['storage_exists'] else 'No'}")

            if status.get('paper_count') is not None:
                print(f"Papers in Zotero: {status['paper_count']}")
                print(f"Collections: {status['collection_count']}")

            if status.get('error'):
                print(f"Error: {status['error']}")
        else:
            print("\nTo enable Zotero integration, set ZOTERO_ENABLED=true in .env")

        print("="*50)

    def _cmd_sync_zotero(self) -> None:
        """Sync Zotero collection names to match categories.json."""
        print("\n" + "="*50)
        print("Sync Zotero Collection Names")
        print("="*50)

        if not zotero_db.is_enabled:
            print("Zotero integration is disabled.")
            print("Set ZOTERO_ENABLED=true in .env to enable.")
            return

        if not zotero_db.is_available():
            print("Zotero database not accessible.")
            return

        # Load categories
        try:
            category_manager.load()
        except CategoriesNotFoundError:
            print("categories.json not found. Run --init first.")
            return

        # Backup first
        print("Backing up Zotero database...")
        if not zotero_db.backup():
            print("Error: Could not backup Zotero. Aborting.")
            return

        # Sync names
        print("Syncing collection names to match categories.json...")
        renamed = zotero_db.sync_collection_names(category_manager)

        if renamed > 0:
            print(f"\nRenamed {renamed} collections to match categories.json")
            print("Restart Zotero to see the changes.")
        else:
            print("\nAll collection names already match categories.json")

        print("="*50)

    def _cmd_check_threshold(self) -> None:
        """Check uncategorized threshold."""
        count = file_manager.count_uncategorized()
        threshold = category_manager.threshold

        print(f"Uncategorized papers: {count}")
        print(f"Threshold: {threshold}")

        if count >= threshold:
            self._warn_threshold_exceeded(count, threshold)
        else:
            print("Status: OK (below threshold)")

    def _cmd_update_summary(self) -> None:
        """Update the summary file."""
        summarizer.generate()

    def _cmd_interactive(self, provider_name: Optional[str]) -> None:
        """Run interactive mode."""
        provider = ProviderFactory.get_provider(provider_name)

        print("\n" + "="*60)
        print(f"Paper Categorization - Interactive Mode (using {provider.name})")
        print("="*60)
        print("Enter a paper title to get its category.")
        print("Type 'quit' to exit.\n")

        while True:
            print("-" * 40)
            title = input("Paper Title: ").strip()

            if title.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not title:
                print("Error: Title is required.")
                continue

            abstract = input("Abstract (optional, press Enter to skip): ").strip()

            print("\nCategorizing...")
            try:
                result = provider.categorize(title, abstract if abstract else None)

                cat_code = result.get('category_code', '0')
                cat_name = result.get('category_name', 'Uncategorized')
                folder_path = category_manager.get_folder_path(cat_code)

                print("\n" + "="*50)
                print(f"Category: {cat_code} {cat_name}")
                print(f"Folder:   {folder_path}")
                print(f"Confidence: {result.get('confidence', 'unknown')}")
                print(f"Reasoning: {result.get('reasoning', 'N/A')}")

                if result.get('alternative_categories'):
                    print(f"Alternatives: {', '.join(result['alternative_categories'])}")

                print("="*50 + "\n")

            except Exception as e:
                print(f"Error: {e}\n")

    def _filename_needs_rename(self, filename: str) -> bool:
        """
        Check if a filename looks like it needs renaming to a proper title.

        Returns True for filenames that are likely NOT proper titles:
        - arXiv IDs (e.g., "2510.26787v1.pdf")
        - Pure numeric names
        - Very short names (less than 10 chars without extension)
        - Names with only underscores/hyphens and numbers

        Returns False for filenames that look like proper titles.
        """
        import re

        # Remove extension
        name = filename.replace('.pdf', '').replace('.PDF', '')

        # arXiv ID pattern (e.g., 2510.26787, 2510.26787v1)
        if re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', name):
            return True

        # Pure numeric or mostly numeric
        if re.match(r'^[\d\s\-_.]+$', name):
            return True

        # Very short names (likely not a full title)
        if len(name) < 10:
            return True

        # Names that look like IDs (all caps with numbers)
        if re.match(r'^[A-Z0-9\-_]+$', name) and len(name) < 30:
            return True

        return False

    def _titles_match(self, filename: str, extracted_title: str) -> bool:
        """
        Check if the filename already matches the extracted title.

        Normalizes both strings for comparison.
        """
        import re

        # Normalize filename (remove extension, replace separators)
        name = filename.replace('.pdf', '').replace('.PDF', '')
        name = name.replace('-', ' ').replace('_', ' ')
        name = re.sub(r'\s+', ' ', name).strip().lower()

        # Normalize extracted title
        title = re.sub(r'\s+', ' ', extracted_title).strip().lower()

        # Exact match
        if name == title:
            return True

        # One contains the other (for truncated filenames)
        if len(name) > 20 and (name in title or title in name):
            return True

        # Check if significant portion matches (for truncated titles)
        if len(name) > 50 and title.startswith(name[:50]):
            return True

        return False

    def _extract_title_from_pdf(self, provider: AIProvider, pdf_path: Path) -> Optional[str]:
        """
        Extract the paper title from PDF content using AI.

        Args:
            provider: AI provider to use
            pdf_path: Path to the PDF file

        Returns:
            Extracted title, or None if extraction fails
        """
        # Try PyPDF2 first
        text = extract_text(pdf_path, max_pages=1) if is_pdf_support_available() else None
        used_ocr = False

        # Fall back to OCR if PyPDF2 fails
        if not text or len(text.strip()) < 50:
            if is_ocr_available():
                print(f"  Trying OCR extraction...")
                text = extract_text_ocr(pdf_path, max_pages=1)
                used_ocr = True

        if not text or len(text.strip()) < 50:
            if not is_pdf_support_available() and not is_ocr_available():
                print(f"  Warning: No PDF extraction available (install PyPDF2 or pytesseract)")
            elif not text:
                if is_ocr_available():
                    print(f"  Warning: No text extracted even with OCR")
                else:
                    print(f"  Warning: No text extracted (scanned PDF? Install pytesseract for OCR)")
            else:
                print(f"  Warning: Insufficient text extracted ({len(text.strip())} chars)")
            return None

        if used_ocr:
            print(f"  OCR extracted {len(text.strip())} chars")

        prompt = f"""Extract ONLY the title of this academic paper from the text below.
Return ONLY the title, nothing else. No quotes, no explanation.

Text from first page:
{text[:1500]}"""

        try:
            # Use a simple prompt to get just the title
            result = provider.query(prompt)
            if result:
                # Clean up the title
                title = result.strip().strip('"\'')
                # Replace newlines with spaces (titles can span multiple lines)
                title = ' '.join(title.split())
                # Remove common prefixes the AI might add
                for prefix in ["Title:", "The title is:", "Paper title:"]:
                    if title.lower().startswith(prefix.lower()):
                        title = title[len(prefix):].strip()
                if len(title) > 10 and len(title) < 300:
                    return title
                else:
                    print(f"  Warning: Extracted title invalid (len={len(title)}): {title[:50]}...")
            else:
                print(f"  Warning: AI returned empty response")
        except Exception as e:
            print(f"  Warning: Could not extract title: {e}")

        return None

    def _rename_papers_by_title(self, provider: AIProvider, papers: List, dry_run: bool) -> List:
        """
        Rename papers in Inbox if their filename doesn't match the paper's actual title.

        For each paper:
        1. Check if filename looks like it needs renaming (arXiv IDs, numeric names, etc.)
        2. Extract the actual title from the PDF using AI
        3. Compare with current filename
        4. Rename if they don't match

        Args:
            provider: AI provider to use
            papers: List of PaperFile objects
            dry_run: If True, only preview changes

        Returns:
            Updated list of PaperFile objects with new paths
        """
        print("\n" + "-"*40)
        print("Step 1: Checking and renaming papers by title")
        print("-"*40)

        updated_papers = []
        renamed_count = 0
        skipped_count = 0

        for i, paper in enumerate(papers, 1):
            needs_check = self._filename_needs_rename(paper.filename)

            if needs_check:
                print(f"[{i}/{len(papers)}] {paper.filename[:40]}... (needs title extraction)")
            else:
                print(f"[{i}/{len(papers)}] {paper.filename[:40]}... (checking title match)")

            # Extract title from PDF
            title = self._extract_title_from_pdf(provider, paper.path)

            if title:
                # Check if filename already matches title
                if self._titles_match(paper.filename, title):
                    print(f"  ✓ Filename already matches title")
                    paper.title = title
                    updated_papers.append(paper)
                    skipped_count += 1
                else:
                    print(f"  Title: {title[:60]}{'...' if len(title) > 60 else ''}")

                    if not dry_run:
                        new_path = file_manager.rename_file(paper.path, title)
                        # Create updated PaperFile with new path
                        updated_paper = PaperFile(
                            path=new_path,
                            filename=new_path.name,
                            title=title
                        )
                        updated_papers.append(updated_paper)
                        renamed_count += 1
                    else:
                        print(f"  [DRY RUN] Would rename to: {title[:50]}.pdf")
                        paper.title = title
                        updated_papers.append(paper)
                        renamed_count += 1
            else:
                print(f"  Could not extract title, keeping original name")
                updated_papers.append(paper)
                skipped_count += 1

        print()
        print(f"Renamed: {renamed_count}, Kept original: {skipped_count}")
        print()
        return updated_papers

    def _cmd_batch(self, provider_name: Optional[str], dry_run: bool) -> None:
        """Run batch processing."""
        provider = ProviderFactory.get_provider(provider_name)

        print("\n" + "="*60)
        print(f"Batch Processing - Inbox Papers (using {provider.name})")
        print("="*60)

        # Show Zotero status
        if zotero_db.is_enabled:
            print(f"Zotero integration: ENABLED")
            print(f"  Database: {config.zotero.db_path}")
            print(f"  Storage: {config.zotero.storage_path}")
        else:
            print(f"Zotero integration: DISABLED")
        print()

        # Get papers
        papers = file_manager.get_inbox_papers()

        if not papers:
            file_manager.ensure_inbox_exists()
            print("No PDF files found in Inbox.")
            return

        print(f"Found {len(papers)} PDF files to process.\n")

        # Step 1: Rename papers by their extracted titles
        papers = self._rename_papers_by_title(provider, papers, dry_run)

        if not dry_run:
            file_manager.create_category_folders()

        # Step 2: Categorize papers
        print("-"*40)
        print("Step 2: Categorizing papers")
        print("-"*40)

        # Backup Zotero and sync collection names
        zotero_backup_ok = False
        if zotero_db.is_available() and not dry_run:
            print("Backing up Zotero database...")
            zotero_backup_ok = zotero_db.backup()
            if not zotero_backup_ok:
                print("Warning: Could not backup Zotero. Zotero operations disabled.")
            else:
                # Sync collection names to match categories.json
                renamed = zotero_db.sync_collection_names(category_manager)
                if renamed > 0:
                    print(f"  Synced {renamed} Zotero collection names to match categories.json")

        # Process papers
        results = []
        successful = 0
        failed = 0
        zotero_updated = 0
        zotero_added = 0

        for i, paper in enumerate(papers, 1):
            print(f"[{i}/{len(papers)}] {paper.filename[:50]}...")

            try:
                # Extract text
                abstract = extract_text(paper.path) if is_pdf_support_available() else None

                # Categorize
                result = provider.categorize(paper.title, abstract)

                cat_code = result.get('category_code', '0')
                cat_name = result.get('category_name', 'Uncategorized')
                confidence = result.get('confidence', 'low')
                reasoning = result.get('reasoning', '')

                # Get category info
                folder_path = category_manager.get_folder_path(cat_code)
                main_category = category_manager.get_main_category_name(cat_code)
                sub_category = category_manager.get_full_name(cat_code) if '.' in cat_code else None
                full_category = f"{cat_code} {cat_name}"

                print(f"  -> {full_category} ({confidence})")

                # Zotero integration
                zotero_action = None
                if zotero_db.is_available() and zotero_backup_ok and not dry_run:
                    zotero_paper = zotero_db.find_paper(paper.title, paper.filename)

                    if zotero_paper:
                        print(f"  Zotero: Found existing entry (ID: {zotero_paper.item_id})")
                        if zotero_db.update_collection(zotero_paper.item_id, main_category, sub_category):
                            print(f"  Zotero: Updated collection -> {cat_name}")
                            zotero_action = "updated"
                            zotero_updated += 1
                        else:
                            zotero_action = "update_failed"
                    else:
                        print(f"  Zotero: Not found, adding new entry...")
                        new_paper = zotero_db.add_paper(paper.path, paper.title, main_category)
                        if new_paper:
                            print(f"  Zotero: Added with key {new_paper.key}")
                            if sub_category:
                                zotero_db.update_collection(new_paper.item_id, main_category, sub_category)
                            zotero_action = "added"
                            zotero_added += 1
                        else:
                            zotero_action = "add_failed"

                elif zotero_db.is_enabled and dry_run:
                    zotero_paper = zotero_db.find_paper(paper.title, paper.filename)
                    if zotero_paper:
                        print(f"  [DRY RUN] Zotero: Would update collection")
                        zotero_action = "would_update"
                    else:
                        print(f"  [DRY RUN] Zotero: Would add new entry")
                        zotero_action = "would_add"

                # Move file
                if not dry_run:
                    dest_path = file_manager.move_to_category(paper.path, cat_code)
                    print(f"  Moved to: {folder_path}")
                else:
                    print(f"  [DRY RUN] Would move to: {folder_path}")

                results.append(ProcessingResult(
                    filename=paper.filename,
                    title=paper.title,
                    category_code=cat_code,
                    category_name=cat_name,
                    full_category=full_category,
                    folder_path=str(folder_path),
                    confidence=confidence,
                    reasoning=reasoning,
                    status="success",
                    zotero_action=zotero_action
                ))
                successful += 1

            except Exception as e:
                print(f"  x Error: {e}")
                uncat_code = category_manager.get_uncategorized_code()
                uncat_name = category_manager.get_uncategorized_name()
                uncat_folder = str(category_manager.get_uncategorized_folder())
                results.append(ProcessingResult(
                    filename=paper.filename,
                    title=paper.title,
                    category_code=uncat_code,
                    category_name="Uncategorized",
                    full_category=uncat_name,
                    folder_path=uncat_folder,
                    confidence="low",
                    reasoning=f"Error: {str(e)}",
                    status="error",
                    error=str(e)
                ))
                failed += 1

        # Summary
        print("\n" + "-"*40)
        print(f"Processed: {len(papers)} papers")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        if zotero_db.is_enabled:
            print(f"Zotero updated: {zotero_updated}")
            print(f"Zotero added: {zotero_added}")

        # Update summary
        if results and not dry_run:
            summarizer.generate(results)
            self._check_threshold_warning()

    def _cmd_single(self, title: str, abstract: Optional[str], provider_name: Optional[str]) -> None:
        """Categorize a single paper."""
        provider = ProviderFactory.get_provider(provider_name)
        print(f"Using AI provider: {provider.name}")

        result = provider.categorize(title, abstract)

        cat_code = result.get('category_code', '0')
        cat_name = result.get('category_name', 'Uncategorized')
        folder_path = category_manager.get_folder_path(cat_code)

        print(f"\nCategory: {cat_code} {cat_name}")
        print(f"Folder: {folder_path}")
        print(f"Confidence: {result.get('confidence', 'unknown')}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")

        if result.get('alternative_categories'):
            print(f"Alternatives: {', '.join(result['alternative_categories'])}")

        print("\nFull result:")
        print(json.dumps(result, indent=2))

    def _cmd_suggest_categories(self, provider_name: Optional[str]) -> None:
        """Get AI suggestions for new categories."""
        papers = file_manager.get_uncategorized_papers()

        if not papers:
            print("No uncategorized papers found.")
            return

        provider = ProviderFactory.get_provider(provider_name)
        print(f"\nAnalyzing {len(papers)} uncategorized papers...")

        # Build prompt
        titles = [p.title for p in papers[:50]]
        titles_text = "\n".join(f"- {t}" for t in titles)

        prompt = f"""Analyze these uncategorized academic paper titles and suggest potential new categories:

{titles_text}

Current categories:
{category_manager.generate_prompt()}

Suggest 1-3 new categories. For each:
1. Category name
2. Short description
3. 3-5 keywords
4. Estimated papers that would fit

Respond in JSON:
{{
    "suggestions": [
        {{
            "name": "Category Name",
            "description": "Brief description",
            "keywords": ["keyword1", "keyword2"],
            "estimated_papers": 5
        }}
    ],
    "reasoning": "Why these categories are needed"
}}
"""

        result = provider.categorize(prompt, None)

        print("\n" + "="*60)
        print("Category Suggestions")
        print("="*60)
        print(json.dumps(result, indent=2))

    # =========================================================================
    # Helpers
    # =========================================================================

    def _check_threshold_warning(self) -> None:
        """Check and warn about uncategorized threshold."""
        count = file_manager.count_uncategorized()
        if count >= category_manager.threshold:
            self._warn_threshold_exceeded(count, category_manager.threshold)

    def _warn_threshold_exceeded(self, count: int, threshold: int) -> None:
        """Print threshold exceeded warning."""
        print("\n" + "="*60)
        print("⚠️  CATEGORY REVIEW RECOMMENDED")
        print("="*60)
        print(f"You have {count} uncategorized papers (threshold: {threshold}).")
        print("Consider reviewing your categories.")
        print("\nOptions:")
        print("  1. Review uncategorized papers manually")
        print("  2. Run with --suggest-categories for AI suggestions")
        print("  3. Edit categories.json to add new categories")
        print("  4. Increase threshold in categories.json")
        print("="*60 + "\n")

    def _ensure_inbox_setup(self) -> None:
        """Ensure Inbox folder exists, create if not."""
        inbox_path = config.paths.inbox

        if inbox_path.exists():
            print(f"\n[OK] Inbox folder: {inbox_path}")
        else:
            inbox_path.mkdir(parents=True, exist_ok=True)
            print(f"\n[OK] Created Inbox folder: {inbox_path}")
            print("     Place your PDFs here, then run: python -m paper_categorizer --batch")


def main():
    """Main entry point."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
