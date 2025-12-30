"""
Zotero Database Module

Handles all Zotero SQLite database operations.

Responsibilities:
    - Database connection management
    - Backup and restore
    - Paper lookup and creation
    - Collection management

Design: Repository Pattern with context manager for connections
"""

import sqlite3
import shutil
import uuid
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from contextlib import contextmanager

from .config import config


@dataclass
class ZoteroPaper:
    """Represents a paper in Zotero."""
    item_id: int
    key: str
    title: str


@dataclass
class ZoteroCollection:
    """Represents a collection in Zotero."""
    collection_id: int
    key: str
    name: str
    parent_id: Optional[int] = None


class ZoteroDatabase:
    """
    Manages Zotero SQLite database operations.

    Usage:
        db = ZoteroDatabase()

        if db.is_available():
            db.backup()

            paper = db.find_paper("Paper Title")
            if paper:
                db.update_collection(paper.item_id, "Category Name")
            else:
                db.add_paper(pdf_path, "Title", "Category")
    """

    def __init__(self):
        self._backup_created = False

    @property
    def is_enabled(self) -> bool:
        """Check if Zotero integration is enabled."""
        return config.zotero.enabled

    @property
    def db_path(self) -> Path:
        """Get the database path."""
        return config.zotero.db_path

    @property
    def storage_path(self) -> Path:
        """Get the storage path."""
        return config.zotero.storage_path

    def is_available(self) -> bool:
        """Check if Zotero database is available."""
        return self.is_enabled and self.db_path.exists()

    def get_status(self) -> Dict:
        """Get Zotero status information."""
        status = {
            "enabled": self.is_enabled,
            "db_exists": self.db_path.exists() if self.is_enabled else False,
            "storage_exists": self.storage_path.exists() if self.is_enabled else False,
            "db_path": str(self.db_path),
            "storage_path": str(self.storage_path),
        }

        if self.is_available():
            try:
                with self._connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM items WHERE itemTypeID != 14")
                    status["paper_count"] = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM collections")
                    status["collection_count"] = cursor.fetchone()[0]
            except Exception as e:
                status["error"] = str(e)

        return status

    # =========================================================================
    # Backup Management
    # =========================================================================

    def backup(self) -> bool:
        """
        Create a backup of the Zotero database.
        Deletes any existing temp backup first.

        Returns:
            True if backup was successful
        """
        if not self.is_available():
            return False

        backup_path = config.zotero.temp_backup_path

        try:
            # Delete existing backup
            if backup_path.exists():
                backup_path.unlink()
                print(f"  Deleted old temp backup: {backup_path.name}")

            # Create new backup
            shutil.copy2(self.db_path, backup_path)
            print(f"  Created Zotero backup: {backup_path.name}")
            self._backup_created = True
            return True
        except Exception as e:
            print(f"Error creating Zotero backup: {e}")
            return False

    def restore(self) -> bool:
        """
        Restore database from temp backup.

        Returns:
            True if restore was successful
        """
        backup_path = config.zotero.temp_backup_path

        if not backup_path.exists():
            return False

        try:
            shutil.copy2(backup_path, self.db_path)
            print("Restored Zotero database from backup")
            return True
        except Exception as e:
            print(f"Error restoring Zotero database: {e}")
            return False

    def cleanup_backup(self) -> None:
        """Remove the temp backup file."""
        backup_path = config.zotero.temp_backup_path

        if backup_path.exists():
            try:
                backup_path.unlink()
                print("  Cleaned up temp backup")
            except Exception as e:
                print(f"Warning: Could not delete temp backup: {e}")

    @property
    def has_backup(self) -> bool:
        """Check if a backup exists."""
        return config.zotero.temp_backup_path.exists()

    # =========================================================================
    # Connection Management
    # =========================================================================

    @contextmanager
    def _connection(self):
        """Context manager for database connections."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Zotero database not found at {self.db_path}")

        conn = sqlite3.connect(str(self.db_path))
        try:
            yield conn
        finally:
            conn.close()

    def _get_library_id(self, cursor) -> int:
        """Get the library ID (usually 1 for personal library)."""
        cursor.execute("SELECT libraryID FROM libraries LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 1

    # =========================================================================
    # Paper Operations
    # =========================================================================

    def find_paper(self, title: str, filename: Optional[str] = None) -> Optional[ZoteroPaper]:
        """
        Find a paper in Zotero by title or filename.

        Args:
            title: Paper title to search
            filename: Optional filename to search in attachments

        Returns:
            ZoteroPaper if found, None otherwise
        """
        if not self.is_available():
            return None

        try:
            with self._connection() as conn:
                cursor = conn.cursor()

                # Search by title
                cursor.execute("""
                    SELECT i.itemID, i.key, idv.value as title
                    FROM items i
                    JOIN itemData id ON i.itemID = id.itemID
                    JOIN itemDataValues idv ON id.valueID = idv.valueID
                    JOIN fields f ON id.fieldID = f.fieldID
                    WHERE f.fieldName = 'title'
                    AND i.itemTypeID != 14
                    AND (idv.value LIKE ? OR idv.value LIKE ?)
                """, (f"%{title}%", f"%{title[:50]}%"))

                result = cursor.fetchone()
                if result:
                    return ZoteroPaper(item_id=result[0], key=result[1], title=result[2])

                # Search by filename in attachments
                if filename:
                    clean_name = filename.replace(".pdf", "").replace(".PDF", "")
                    cursor.execute("""
                        SELECT i.itemID, i.key, ia.path
                        FROM items i
                        JOIN itemAttachments ia ON i.itemID = ia.itemID
                        WHERE ia.path LIKE ?
                    """, (f"%{clean_name}%",))

                    result = cursor.fetchone()
                    if result:
                        # Get parent item
                        cursor.execute(
                            "SELECT parentItemID FROM itemAttachments WHERE itemID = ?",
                            (result[0],)
                        )
                        parent = cursor.fetchone()
                        if parent and parent[0]:
                            cursor.execute("""
                                SELECT i.itemID, i.key, idv.value as title
                                FROM items i
                                JOIN itemData id ON i.itemID = id.itemID
                                JOIN itemDataValues idv ON id.valueID = idv.valueID
                                JOIN fields f ON id.fieldID = f.fieldID
                                WHERE f.fieldName = 'title' AND i.itemID = ?
                            """, (parent[0],))
                            parent_result = cursor.fetchone()
                            if parent_result:
                                return ZoteroPaper(
                                    item_id=parent_result[0],
                                    key=parent_result[1],
                                    title=parent_result[2]
                                )

                return None

        except Exception as e:
            print(f"  Error searching Zotero: {e}")
            return None

    def add_paper(self, pdf_path: Path, title: str, category_name: str) -> Optional[ZoteroPaper]:
        """
        Add a new paper to Zotero with PDF attachment.

        Args:
            pdf_path: Path to the PDF file
            title: Paper title
            category_name: Category/collection name

        Returns:
            ZoteroPaper if successful, None otherwise
        """
        if not self.is_available():
            return None

        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                library_id = self._get_library_id(cursor)

                # Create main item
                item_key = self._generate_key()
                cursor.execute(
                    "SELECT itemTypeID FROM itemTypes WHERE typeName = 'journalArticle'"
                )
                item_type = cursor.fetchone()
                item_type_id = item_type[0] if item_type else 2

                cursor.execute("""
                    INSERT INTO items (itemTypeID, libraryID, key, version, synced,
                                       dateAdded, dateModified, clientDateModified)
                    VALUES (?, ?, ?, 0, 0, datetime('now'), datetime('now'), datetime('now'))
                """, (item_type_id, library_id, item_key))
                item_id = cursor.lastrowid

                # Add title
                cursor.execute("SELECT fieldID FROM fields WHERE fieldName = 'title'")
                title_field = cursor.fetchone()
                if title_field:
                    cursor.execute(
                        "INSERT OR IGNORE INTO itemDataValues (value) VALUES (?)",
                        (title,)
                    )
                    cursor.execute(
                        "SELECT valueID FROM itemDataValues WHERE value = ?",
                        (title,)
                    )
                    value_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, ?, ?)",
                        (item_id, title_field[0], value_id)
                    )

                # Create attachment
                attachment_key = self._generate_key()
                cursor.execute(
                    "SELECT itemTypeID FROM itemTypes WHERE typeName = 'attachment'"
                )
                attach_type = cursor.fetchone()
                attach_type_id = attach_type[0] if attach_type else 14

                cursor.execute("""
                    INSERT INTO items (itemTypeID, libraryID, key, version, synced,
                                       dateAdded, dateModified, clientDateModified)
                    VALUES (?, ?, ?, 0, 0, datetime('now'), datetime('now'), datetime('now'))
                """, (attach_type_id, library_id, attachment_key))
                attachment_id = cursor.lastrowid

                # Copy file to storage
                storage_folder = self.storage_path / attachment_key
                storage_folder.mkdir(parents=True, exist_ok=True)
                dest_path = storage_folder / pdf_path.name
                shutil.copy2(pdf_path, dest_path)

                # Insert attachment record
                cursor.execute("""
                    INSERT INTO itemAttachments (itemID, parentItemID, linkMode,
                                                 contentType, path, syncState)
                    VALUES (?, ?, 1, 'application/pdf', ?, 0)
                """, (attachment_id, item_id, f"storage:{pdf_path.name}"))

                # Add to collection
                collection_id = self._get_or_create_collection(conn, category_name)
                if collection_id:
                    cursor.execute(
                        "INSERT OR IGNORE INTO collectionItems (collectionID, itemID) VALUES (?, ?)",
                        (collection_id, item_id)
                    )

                conn.commit()
                return ZoteroPaper(item_id=item_id, key=item_key, title=title)

        except Exception as e:
            print(f"  Error adding paper to Zotero: {e}")
            return None

    # =========================================================================
    # Collection Operations
    # =========================================================================

    def update_collection(self, item_id: int, category_name: str,
                         subcategory_name: Optional[str] = None) -> bool:
        """
        Update the collection for an existing paper.

        Args:
            item_id: Zotero item ID
            category_name: Main category name
            subcategory_name: Optional subcategory name

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            with self._connection() as conn:
                cursor = conn.cursor()

                # Get or create main collection
                main_collection_id = self._get_or_create_collection(conn, category_name)

                # Handle subcategory
                if subcategory_name and subcategory_name != category_name:
                    cursor.execute(
                        "SELECT key FROM collections WHERE collectionID = ?",
                        (main_collection_id,)
                    )
                    main_key_result = cursor.fetchone()
                    main_key = main_key_result[0] if main_key_result else None

                    sub_collection_id = self._get_or_create_collection(
                        conn, subcategory_name, main_key
                    )
                    target_collection_id = sub_collection_id
                else:
                    target_collection_id = main_collection_id

                # Add item to collection
                cursor.execute(
                    "INSERT OR IGNORE INTO collectionItems (collectionID, itemID) VALUES (?, ?)",
                    (target_collection_id, item_id)
                )

                conn.commit()
                return True

        except Exception as e:
            print(f"  Error updating Zotero collection: {e}")
            return False

    def _get_or_create_collection(self, conn, name: str,
                                  parent_key: Optional[str] = None) -> Optional[int]:
        """Get existing collection or create new one."""
        cursor = conn.cursor()

        # Check if exists
        if parent_key:
            cursor.execute("""
                SELECT c.collectionID FROM collections c
                JOIN collections pc ON c.parentCollectionID = pc.collectionID
                WHERE c.collectionName = ? AND pc.key = ?
            """, (name, parent_key))
        else:
            cursor.execute("""
                SELECT collectionID FROM collections
                WHERE collectionName = ? AND parentCollectionID IS NULL
            """, (name,))

        result = cursor.fetchone()
        if result:
            return result[0]

        # Create new collection
        new_key = self._generate_key()

        parent_id = None
        if parent_key:
            cursor.execute(
                "SELECT collectionID FROM collections WHERE key = ?",
                (parent_key,)
            )
            parent_result = cursor.fetchone()
            if parent_result:
                parent_id = parent_result[0]

        library_id = self._get_library_id(cursor)

        cursor.execute("""
            INSERT INTO collections (collectionName, parentCollectionID, libraryID,
                                     key, version, synced)
            VALUES (?, ?, ?, ?, 0, 0)
        """, (name, parent_id, library_id, new_key))

        return cursor.lastrowid

    def get_collections(self) -> List[ZoteroCollection]:
        """Get all collections."""
        if not self.is_available():
            return []

        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT collectionID, key, collectionName, parentCollectionID
                    FROM collections
                    ORDER BY collectionName
                """)
                return [
                    ZoteroCollection(
                        collection_id=row[0],
                        key=row[1],
                        name=row[2],
                        parent_id=row[3]
                    )
                    for row in cursor.fetchall()
                ]
        except Exception:
            return []

    # =========================================================================
    # Utilities
    # =========================================================================

    @staticmethod
    def _generate_key() -> str:
        """Generate a random 8-character Zotero key."""
        chars = "23456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
        return ''.join(chars[ord(c) % len(chars)] for c in uuid.uuid4().hex[:8])


# Global instance for convenience
zotero_db = ZoteroDatabase()
