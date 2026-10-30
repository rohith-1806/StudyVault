import hashlib
import re

def normalize_title(title: str) -> str:
    """
    Normalizes document titles for duplicate detection:
    - Converts to lowercase
    - Trims leading and trailing spaces
    - Normalizes repeated whitespace
    - Removes .pdf extension (case-insensitive)
    - Normalizes harmless punctuation differences (hyphens, underscores, dots, colons, slashes, etc.)
    """
    if not title:
        return ""
    t = title.lower().strip()
    # Remove trailing .pdf extension if present
    t = re.sub(r'\.pdf\s*$', '', t, flags=re.IGNORECASE)
    # Replace punctuation characters with spaces:
    # hyphens, underscores, dots, commas, colons, semicolons, brackets, quotes, slashes, etc.
    t = re.sub(r'[\-_.:,;()[\]{}/\\|~`!@#$%^&*+=<>?"\']', ' ', t)
    # Collapse multiple whitespaces into a single space
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def compute_file_hash(file_bytes: bytes) -> str:
    """Level 1 Duplicate Detection: SHA-256 hash of exact binary file content."""
    return hashlib.sha256(file_bytes).hexdigest()

def compute_content_hash(extracted_text: str, page_count: int, file_size: int) -> str:
    """
    Level 2 Advanced Duplicate Detection:
    Generates a normalized content fingerprint from:
    - Cleaned alphanumeric text (first 2000 characters)
    - Page count
    - File size bucket (rounded to 5KB)
    """
    normalized_text = re.sub(r'[^a-zA-Z0-9]', '', (extracted_text or "").lower())
    truncated_text = normalized_text[:2000]
    size_bucket = (file_size // 5120) * 5120
    fingerprint = f"text:{truncated_text}|pages:{page_count}|size:{size_bucket}"
    return hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()

def check_is_duplicate(
    db_service, 
    file_hash: str, 
    content_hash: str = None, 
    title: str = None, 
    storage_service = None
) -> tuple[bool, dict | None, str | None]:
    """
    Checks if a document with matching title, file_hash, or content_hash already exists in the library.
    Returns (is_duplicate, existing_document_dict, duplicate_type).
    duplicate_type can be 'title' or 'content_hash'.
    """
    # 1. Check title conflict if title provided
    if title:
        norm_title = normalize_title(title)
        existing_title_doc = db_service.find_document_by_title_normalized(norm_title)
        if existing_title_doc:
            return True, existing_title_doc, "title"

    # 2. Check exact SHA-256 binary file hash
    if file_hash:
        existing_hash_doc = db_service.find_document_by_file_hash(file_hash)
        if existing_hash_doc:
            return True, existing_hash_doc, "content_hash"

        # 3. Check legacy documents where file_hash might be missing or unpopulated
        if storage_service:
            existing_legacy_doc = db_service.find_legacy_document_by_file_hash(file_hash, storage_service)
            if existing_legacy_doc:
                return True, existing_legacy_doc, "content_hash"

    # 4. Check Level 2 normalized content fingerprint
    if content_hash:
        existing_content_doc = db_service.find_document_by_content_hash(content_hash)
        if existing_content_doc:
            return True, existing_content_doc, "content_hash"

    return False, None, None
