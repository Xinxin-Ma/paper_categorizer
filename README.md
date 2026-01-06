# Paper Categorization System

A system for organizing and categorizing academic papers using AI-powered classification. Supports **Google Gemini**, **Anthropic Claude**, and **OpenAI** APIs, with optional **Zotero integration**.

---

## Overview

This system provides:
- **Multi-provider support** - Works with Gemini, Claude, or OpenAI (uses first available)
- **Zotero integration** - Automatically sync categories to your Zotero library
- **Interactive categorization** - Enter a paper title and get its category instantly
- **Batch processing** - Automatically sort PDFs from an Inbox folder into categorized folders
- **Dynamic categories** - Categories are loaded from `categories.json` and fully customizable
- **Auto-generated summaries** - Papers_Summary.md shows newly processed papers at the top
- **Uncategorized threshold alerts** - Get warnings when too many papers are uncategorized
- **AI-powered category suggestions** - Analyze uncategorized papers and suggest new categories
- **PDF text extraction** - Optionally extracts abstract from PDFs for better categorization

---

## Workflow

The typical user workflow is:

1. **Add papers to Inbox** - Drop PDF files into the `Inbox/` folder
2. **Rename if needed** - If the filename doesn't match the paper title, rename it first
3. **Run batch processing** - The script will:
   - Categorize each paper using AI
   - If Zotero is enabled:
     - Papers already in Zotero: Update their collection/category
     - Papers not in Zotero: Add them with the PDF attachment
   - Move files to category folders
4. **Review results** - Check `Papers_Summary.md` for the updated catalog

---

## Quick Start

### First-Time Setup

```bash
# 1. Navigate to the paper_categorizer folder
cd ~/Documents/Papers/paper_categorizer

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
# Or manually: pip install google-generativeai python-dotenv PyPDF2

# 4. Set up configuration
cp .env.example .env
# Edit .env and add your API key (at least one required)
# Configure Zotero paths if you want Zotero integration

# 5. Initialize the system
cd ~/Documents/Papers
./paper_categorizer/run.sh --init
# This will either:
#   - Scan existing category folders and generate categories.json
#   - Or create a template categories.json for you to customize

# 6. (If using template) Edit categories.json
# Skip this if --init scanned your existing folders
cp paper_categorizer/categories.json.example paper_categorizer/categories.json  # Optional: start from example
# Edit categories.json to define your own paper categories

# 7. Check Zotero status (optional)
./paper_categorizer/run.sh --zotero-status
```

### Basic Usage

```bash
# Run from the Papers folder
cd ~/Documents/Papers

# Option 1: Use the wrapper script (recommended - handles venv automatically)
./paper_categorizer/run.sh --batch

# Option 2: Activate venv manually
source paper_categorizer/venv/bin/activate
python -m paper_categorizer --batch

# Interactive mode - get category for a single paper
./paper_categorizer/run.sh --interactive

# Dry run - preview without making changes
./paper_categorizer/run.sh --batch --dry-run
```

---

## Zotero Integration

The system can optionally integrate with your Zotero library to:
- **Update collections** for papers already in Zotero
- **Add new papers** to Zotero with PDF attachments
- **Create collection hierarchy** matching your category structure

### Enable Zotero Integration

Edit `.env` file:

```bash
# Enable Zotero integration
ZOTERO_ENABLED=true

# Path to your Zotero database
ZOTERO_DB_PATH=~/Zotero/zotero.sqlite

# Path to Zotero storage folder
ZOTERO_STORAGE_PATH=~/Zotero/storage
```

### Check Zotero Status

```bash
./paper_categorizer/run.sh --zotero-status
```

Output:
```
==================================================
Zotero Integration Status
==================================================
Enabled: Yes
Database path: /Users/username/Zotero/zotero.sqlite
Database exists: Yes
Storage path: /Users/username/Zotero/storage
Storage exists: Yes
Papers in Zotero: 150
Collections: 25
==================================================
```

### How Zotero Integration Works

1. **Before processing**: Creates a backup of your Zotero database (`zotero_temp_backup.sqlite`)
2. **For each paper**:
   - Searches Zotero by title or filename
   - If found: Updates the paper's collection to match the AI category
   - If not found: Creates a new entry with the PDF attachment
3. **After processing**: The backup remains until the next batch run

### Adding New Papers to Zotero

When a paper is not found in Zotero, the system automatically:

1. **Creates a new item** as "Journal Article" type
2. **Sets the title** from the PDF filename or AI-extracted title
3. **Copies the PDF** to Zotero's storage folder (`~/Zotero/storage/<key>/filename.pdf`)
4. **Links the attachment** to the item record
5. **Assigns to collection** matching the AI-determined category

The paper appears in Zotero after you restart Zotero (or it syncs automatically if open).

### Updating Existing Papers

When a paper is already in Zotero:

1. **Searches by title** (partial match) or **filename** in attachments
2. **Creates collection** if the category doesn't exist yet
3. **Adds item to collection** (doesn't remove from other collections)

### Safety Features

- **Automatic backup**: Database is backed up before any modifications
- **Single backup**: Old backup is deleted before creating new one
- **Dry run support**: Use `--dry-run` to preview Zotero changes without modifying
- **Disable option**: Set `ZOTERO_ENABLED=false` to skip all Zotero operations

### Important Notes

- **Close Zotero** before running batch processing to avoid database locks
- Papers are added as "Journal Article" type by default
- Collections are created to match your category hierarchy

---

## Configuration

### .env File

```bash
# API Keys (at least one required)
GEMINI_API_KEY=your-gemini-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Default AI provider
DEFAULT_PROVIDER=gemini

# Zotero Integration (optional)
ZOTERO_ENABLED=true
ZOTERO_DB_PATH=~/Zotero/zotero.sqlite
ZOTERO_STORAGE_PATH=~/Zotero/storage
```

### Finding Your Zotero Paths

| OS | Default Database Path | Default Storage Path |
|----|----------------------|---------------------|
| macOS | `~/Zotero/zotero.sqlite` | `~/Zotero/storage` |
| Windows | `C:\Users\<username>\Zotero\zotero.sqlite` | `C:\Users\<username>\Zotero\storage` |
| Linux | `~/Zotero/zotero.sqlite` | `~/Zotero/storage` |

To find your actual paths: In Zotero, go to **Edit > Preferences > Advanced > Files and Folders**.

---

## All Commands

| Command | Description |
|---------|-------------|
| `--init` | Initialize system: scan existing folders or create template categories.json |
| `--interactive`, `-i` | Enter paper titles interactively and get categories |
| `--batch`, `-b` | Process all PDFs in Inbox folder |
| `--dry-run` | Preview batch processing without moving files or modifying Zotero |
| `--update-summary` | Regenerate Papers_Summary.md from existing folders |
| `--title`, `-t` | Categorize a single paper by title |
| `--abstract`, `-a` | Provide abstract for better categorization |
| `--provider`, `-p` | Choose AI provider: `gemini`, `claude`, or `openai` |
| `--list-providers` | Show available AI providers and their status |
| `--list-categories`, `-l` | Show all available categories |
| `--check-threshold` | Check if uncategorized papers exceed threshold |
| `--suggest-categories` | Analyze uncategorized papers and suggest new categories |
| `--zotero-status` | Check Zotero integration status and configuration |

---

## Folder Structure

```
Documents/Papers/
├── Inbox/                      # Drop new PDFs here
├── Papers Auto Category/       # Auto-organized papers
│   ├── 1. Multi-Armed Bandits & Online Learning/
│   │   ├── 1.1 Contextual Bandits/
│   │   │   ├── 1.1.1 Linear Contextual Bandits/
│   │   │   └── ...
│   │   └── ...
│   ├── 2. Recommender Systems/
│   │   └── ...
│   └── ...
├── Papers_Summary.md           # Auto-generated summary
└── paper_categorizer/          # Main package
    ├── venv/                   # Python virtual environment
    ├── run.sh                  # Wrapper script (recommended way to run)
    ├── __init__.py             # Package marker
    ├── __main__.py             # Entry point
    ├── config.py               # Configuration management
    ├── categories.py           # Category operations
    ├── ai_providers.py         # AI provider implementations
    ├── pdf_utils.py            # PDF text extraction
    ├── zotero_db.py            # Zotero database operations
    ├── file_manager.py         # File operations
    ├── summarizer.py           # Summary generation
    ├── cli.py                  # Command-line interface
    ├── categories.json         # Customizable categories
    ├── .env                    # Your configuration (git-ignored)
    ├── .env.example            # Configuration template
    ├── requirements.txt        # Python dependencies
    └── README.md               # This file
```

---

## Examples

### Batch Processing with Zotero

```bash
# Process papers with Zotero integration (close Zotero first!)
./paper_categorizer/run.sh --batch

# Output:
# ============================================================
# Batch Processing - Inbox Papers (using gemini)
# ============================================================
# Zotero integration: ENABLED
#   Database: /Users/username/Zotero/zotero.sqlite
#   Storage: /Users/username/Zotero/storage
#
# Found 3 PDF files to process.
#
# Backing up Zotero database...
#   Deleted old temp backup: zotero_temp_backup.sqlite
#   Created Zotero backup: zotero_temp_backup.sqlite
#
# [1/3] Neural_Bandits_Paper.pdf...
#   -> 1.1.2 Neural & Non-linear Contextual Bandits (high)
#   Zotero: Found existing entry (ID: 1234)
#   Zotero: Updated collection -> Neural & Non-linear Contextual Bandits
#   Moved to: 1. Multi-Armed Bandits & Online Learning/1.1 Contextual Bandits/...
#
# [2/3] New_LLM_Paper.pdf...
#   -> 3.1 LLM Evaluation & Benchmarking (high)
#   Zotero: Not found, adding new entry...
#   Zotero: Added with key ABC12345
#   Moved to: 3. Large Language Models & NLP/3.1 LLM Evaluation...
#
# ----------------------------------------
# Processed: 3 papers
# Successful: 3
# Failed: 0
# Zotero updated: 1
# Zotero added: 2
```

### Without Zotero Integration

```bash
# Disable Zotero in .env
ZOTERO_ENABLED=false

# Or just run - it will skip Zotero if not configured
./paper_categorizer/run.sh --batch

# Output shows:
# Zotero integration: DISABLED
```

---

## Importing Existing Category Folders

If you already have papers organized in category folders but no `categories.json`, the system can automatically generate one from your existing folder structure.

### How It Works

When you run `--init` without a `categories.json` file, the system will:

1. **Detect existing folders** in `Papers Auto Category/`
2. **Offer to scan them** and generate `categories.json` automatically
3. **Preserve your folder names** on disk (no renaming)

### Supported Folder Formats

The system handles both numbered and unnumbered folder structures:

**Numbered folders** (recommended):
```
Papers Auto Category/
├── 1. Machine Learning/
│   ├── 1.1 Supervised Learning/
│   └── 1.2 Unsupervised Learning/
└── 2. Natural Language Processing/
```

**Unnumbered folders** (also supported):
```
Papers Auto Category/
├── Machine Learning/
│   ├── Supervised Learning/
│   └── Unsupervised Learning/
└── Natural Language Processing/
```

### Auto-Numbering for Unnumbered Folders

When scanning unnumbered folders, the system:
- Assigns category codes internally (1, 2, 3...)
- **Does NOT rename** folders on disk
- Maps codes to original folder names in `categories.json`

Example output when scanning unnumbered folders:
```
Scanning existing folders...

Generated categories.json with 3 categories:
  Machine Learning (2 subcategories)
  Natural Language Processing (0 subcategories)
  Uncategorized (0 subcategories)

Note: The following folders were auto-numbered:
  Code 1 -> 'Machine Learning'
  Code 2 -> 'Natural Language Processing'

Folder names on disk are NOT changed.
Edit categories.json if you want different numbers.
```

### Resulting categories.json

For unnumbered folders, the generated file looks like:
```json
{
  "categories": {
    "1": {
      "name": "Machine Learning",
      "description": "",
      "keywords": [],
      "subcategories": {
        "1.1": "Supervised Learning",
        "1.2": "Unsupervised Learning"
      }
    },
    "2": {
      "name": "Natural Language Processing",
      "description": "",
      "keywords": [],
      "subcategories": {}
    }
  }
}
```

After generation, you can edit the file to add descriptions and keywords for better AI categorization.

---

## Dynamic Categories

Categories are stored in `categories.json` and can be customized.

### Add a New Category

```json
{
  "categories": {
    "17": {
      "name": "17. Your New Category",
      "description": "Description of what papers belong here",
      "keywords": ["keyword1", "keyword2"],
      "subcategories": {
        "17.1": "17.1 Subcategory Name"
      }
    }
  }
}
```

### Adjust Uncategorized Threshold

```json
{
  "uncategorized_threshold": 20
}
```

When the threshold is exceeded, you'll get a warning suggesting to review categories.

---

## Troubleshooting

### "No PDF extraction available" / Papers go to Uncategorized
- This happens when running with system Python instead of the virtual environment
- **Solution**: Use `./paper_categorizer/run.sh` instead of `python -m paper_categorizer`
- Or activate the venv first: `source paper_categorizer/venv/bin/activate`
- PyPDF2 is installed in the venv but not in system Python

### "No API key found"
- Create `.env` file with at least one API key
- Check the key is correctly formatted (no quotes needed)

### "Zotero database not found"
- Check `ZOTERO_DB_PATH` in `.env` points to the correct location
- Run `--zotero-status` to verify configuration
- Find your path: Zotero > Edit > Preferences > Advanced > Files and Folders

### "Database is locked"
- Close Zotero before running batch processing
- Zotero locks its database while running

### Papers not appearing in Zotero
- Check that `ZOTERO_ENABLED=true` in `.env`
- Restart Zotero to see newly added papers
- Check the Zotero collections for your categories

### Restore Zotero from Backup
If something goes wrong, restore from the temp backup:
```bash
cp ~/Zotero/zotero_temp_backup.sqlite ~/Zotero/zotero.sqlite
```

---

## Files

| File | Description |
|------|-------------|
| `run.sh` | Wrapper script that activates venv (recommended way to run) |
| `__init__.py` | Package marker with version info |
| `__main__.py` | Entry point for `python -m paper_categorizer` |
| `config.py` | Configuration management (Singleton pattern) |
| `categories.py` | Category hierarchy and operations |
| `ai_providers.py` | AI provider implementations (Strategy pattern) |
| `pdf_utils.py` | PDF text extraction utilities |
| `zotero_db.py` | Zotero database operations (Repository pattern) |
| `file_manager.py` | File and folder operations |
| `summarizer.py` | Summary markdown generation |
| `cli.py` | Command-line interface |
| `categories.json` | Your category configuration (git-ignored) |
| `categories.json.example` | Template for categories |
| `.env` | Your API keys and Zotero paths (git-ignored) |
| `.env.example` | Template for configuration |
| `requirements.txt` | Python dependencies |

---

## Tips

1. **Close Zotero** before batch processing to avoid database locks
2. **Rename files** before processing if filename doesn't match paper title
3. **Use dry run** first: `--batch --dry-run` to preview changes
4. **Check Zotero status** after setup: `--zotero-status`
5. **Review uncategorized** periodically with `--check-threshold`
6. **Get AI suggestions** when many papers are uncategorized: `--suggest-categories`

---

*Last updated: January 6, 2026 (v5.1 - Added run.sh wrapper script)*
