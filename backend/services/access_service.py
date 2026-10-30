import datetime

class AccessService:
    @staticmethod
    def is_access_active(user_profile: dict) -> bool:
        """
        Server-side validation of active download access status based on server UTC time.
        """
        if not user_profile:
            return False

        # Admin role always has unlimited access
        if user_profile.get('role') == 'admin':
            return True

        expires_at_str = user_profile.get('download_access_expires_at')
        if not expires_at_str:
            return False

        try:
            if isinstance(expires_at_str, str):
                # Parse ISO timestamp
                expires_at = datetime.datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            elif isinstance(expires_at_str, datetime.datetime):
                expires_at = expires_at_str
            else:
                return False

            now = datetime.datetime.now(datetime.timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)

            return now < expires_at
        except Exception:
            return False

    @staticmethod
    def get_remaining_access_seconds(user_profile: dict) -> int:
        if not user_profile:
            return 0
            
        expires_at_str = user_profile.get('download_access_expires_at')
        if not expires_at_str:
            return 0

        try:
            if isinstance(expires_at_str, str):
                expires_at = datetime.datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            elif isinstance(expires_at_str, datetime.datetime):
                expires_at = expires_at_str
            else:
                return 0

            now = datetime.datetime.now(datetime.timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)

            remaining = int((expires_at - now).total_seconds())
            return max(0, remaining)
        except Exception:
            return 0

    @staticmethod
    def grant_24h_access(db_service, user_id: str, document_id: str, duration_hours: int = 24) -> dict:
        """
        Grants or extends 24-hour unlimited download access to user upon valid accepted contribution.
        """
        user_profile = db_service.get_profile_by_id(user_id)
        now = datetime.datetime.now(datetime.timezone.utc)

        current_expires_at_str = user_profile.get('download_access_expires_at') if user_profile else None
        
        base_time = now
        if current_expires_at_str:
            try:
                if isinstance(current_expires_at_str, str):
                    current_expires = datetime.datetime.fromisoformat(current_expires_at_str.replace('Z', '+00:00'))
                else:
                    current_expires = current_expires_at_str
                if current_expires.tzinfo is None:
                    current_expires = current_expires.replace(tzinfo=datetime.timezone.utc)

                if current_expires > now:
                    base_time = current_expires
            except Exception:
                pass

        new_expires_at = base_time + datetime.timedelta(hours=duration_hours)
        
        # Update user profile access timestamp
        updated_profile = db_service.update_user_access_expiry(
            user_id=user_id, 
            started_at=now.isoformat(), 
            expires_at=new_expires_at.isoformat()
        )

        # Log grant record
        db_service.create_access_grant(
            user_id=user_id,
            source_document_id=document_id,
            started_at=now.isoformat(),
            expires_at=new_expires_at.isoformat()
        )

        return {
            "user_id": user_id,
            "access_active": True,
            "started_at": now.isoformat(),
            "expires_at": new_expires_at.isoformat(),
            "duration_hours": duration_hours
        }

    @staticmethod
    def authorize_download(db_service, user_id: str, document: dict) -> tuple[bool, str]:
        """
        Verifies if a user is authorized to download a document:
        1. User owns the document -> Always allowed!
        2. Admin user -> Always allowed!
        3. Document is approved AND user has active 24h contribution access -> Allowed!
        4. Otherwise -> Denied with friendly explanation.
        """
        if not document:
            return False, "Document not found."

        if document.get('status') != 'approved':
            # Allow uploader or admin to download even if pending/rejected
            if str(document.get('uploader_id')) == str(user_id):
                return True, "Authorized (Uploader)."
            user_profile = db_service.get_profile_by_id(user_id) if user_id else None
            if user_profile and user_profile.get('role') == 'admin':
                return True, "Authorized (Admin)."
            return False, "This document is pending moderation or has been rejected."

        # 1. Uploader can ALWAYS download their own document
        if user_id and str(document.get('uploader_id')) == str(user_id):
            return True, "Authorized (Uploader)."

        # 2. Check user access status
        if not user_id:
            return False, "Please log in to download documents."

        user_profile = db_service.get_profile_by_id(user_id)
        if not user_profile:
            return False, "User account not found."

        if user_profile.get('role') == 'admin':
            return True, "Authorized (Admin)."

        if AccessService.is_access_active(user_profile):
            return True, "Authorized (Active Contribution Access)."

        return False, "Your free download access has expired. Upload a valid study document to unlock 24 hours of unlimited downloads."
