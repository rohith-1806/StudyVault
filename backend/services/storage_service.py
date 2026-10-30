import os
import uuid
import datetime
from supabase import create_client, Client
from flask import current_app, url_for

class StorageService:
    def __init__(self):
        self._supabase: Client = None

    def _get_supabase_client(self):
        url = current_app.config.get('SUPABASE_URL')
        key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY') or current_app.config.get('SUPABASE_ANON_KEY')
        if url and key:
            try:
                return create_client(url, key)
            except Exception:
                return None
        return None

    def upload_document_pdf(self, user_id: str, document_id: str, file_bytes: bytes, filename: str) -> str:
        """
        Uploads PDF to Supabase Storage private bucket 'documents/{user_id}/{document_id}.pdf'.
        Falls back to local file storage if Supabase credentials are not provided.
        Returns storage path string.
        """
        storage_path = f"documents/{user_id}/{document_id}.pdf"
        client = self._get_supabase_client()

        if client:
            bucket_name = current_app.config.get('STORAGE_BUCKET', 'documents')
            try:
                # Ensure bucket exists or upload file
                client.storage.from_(bucket_name).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"}
                )
                return storage_path
            except Exception as e:
                # Log error and fallback to local storage
                print(f"[StorageService] Supabase upload failed, falling back to local storage: {e}")

        # Local storage fallback
        local_dir = os.path.join(current_app.config['LOCAL_STORAGE_DIR'], user_id)
        os.makedirs(local_dir, exist_ok=True)
        local_filepath = os.path.join(local_dir, f"{document_id}.pdf")
        with open(local_filepath, 'wb') as f:
            f.write(file_bytes)

        return storage_path

    def get_signed_url(self, storage_path: str, expires_in_seconds: int = 300) -> str:
        """
        Generates a short-lived signed URL (default 5 mins) for private PDF download or preview.
        """
        client = self._get_supabase_client()
        if client:
            bucket_name = current_app.config.get('STORAGE_BUCKET', 'documents')
            try:
                res = client.storage.from_(bucket_name).create_signed_url(storage_path, expires_in_seconds)
                if isinstance(res, dict) and 'signedURL' in res:
                    return res['signedURL']
                elif hasattr(res, 'signed_url'):
                    return res.signed_url
            except Exception as e:
                print(f"[StorageService] Supabase signed URL generation failed: {e}")

        # Local storage URL route fallback
        # Returns backend preview/stream API endpoint
        parts = storage_path.split('/')
        if len(parts) >= 3:
            doc_id = parts[2].replace('.pdf', '')
            return f"/api/documents/{doc_id}/stream"
        return f"/api/documents/stream?path={storage_path}"

    def read_local_pdf(self, storage_path: str) -> bytes:
        """Helper to read local storage PDF bytes if using fallback."""
        parts = storage_path.split('/')
        if len(parts) >= 3:
            user_id = parts[1]
            doc_filename = parts[2]
            filepath = os.path.join(current_app.config['LOCAL_STORAGE_DIR'], user_id, doc_filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return f.read()
        return None

    def read_pdf_bytes(self, storage_path: str) -> bytes:
        """Helper to read PDF bytes from local storage or Supabase Storage."""
        # 1. Try local storage
        local_bytes = self.read_local_pdf(storage_path)
        if local_bytes:
            return local_bytes

        # 2. Try Supabase Storage
        client = self._get_supabase_client()
        if client:
            bucket_name = current_app.config.get('STORAGE_BUCKET', 'documents')
            try:
                res = client.storage.from_(bucket_name).download(storage_path)
                if isinstance(res, bytes):
                    return res
                elif hasattr(res, 'content'):
                    return res.content
                elif hasattr(res, 'read'):
                    return res.read()
            except Exception as e:
                print(f"[StorageService] Supabase download error: {e}")
        return None

    def delete_document_pdf(self, storage_path: str) -> bool:
        """Deletes file from storage."""
        client = self._get_supabase_client()
        if client:
            bucket_name = current_app.config.get('STORAGE_BUCKET', 'documents')
            try:
                client.storage.from_(bucket_name).remove([storage_path])
                return True
            except Exception as e:
                print(f"[StorageService] Supabase delete failed: {e}")

        parts = storage_path.split('/')
        if len(parts) >= 3:
            user_id = parts[1]
            doc_filename = parts[2]
            filepath = os.path.join(current_app.config['LOCAL_STORAGE_DIR'], user_id, doc_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        return False
