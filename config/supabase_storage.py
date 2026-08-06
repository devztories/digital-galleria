import os
import mimetypes
from uuid import uuid4

from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible

from supabase import create_client


@deconstructible
class SupabaseStorage(Storage):

    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.bucket_name = os.environ.get(
            "SUPABASE_BUCKET",
            "digital-galleria-media"
        )

        if not self.supabase_url:
            raise ValueError(
                "SUPABASE_URL is not configured."
            )

        if not self.supabase_key:
            raise ValueError(
                "SUPABASE_KEY is not configured."
            )

        self.client = create_client(
            self.supabase_url,
            self.supabase_key
        )

    def _clean_name(self, name):
        """
        Normalize Django file paths for Supabase Storage.
        """

        return name.replace("\\", "/").lstrip("/")

    def _generate_unique_name(self, name):
        """
        Prevent accidental overwriting of files with the same name.
        """

        name = self._clean_name(name)

        directory, filename = os.path.split(name)
        base_name, extension = os.path.splitext(filename)

        unique_filename = (
            f"{base_name}_{uuid4().hex}{extension}"
        )

        if directory:
            return f"{directory}/{unique_filename}"

        return unique_filename

    def _open(self, name, mode="rb"):
        """
        Download a file from Supabase when Django needs to open it.
        """

        name = self._clean_name(name)

        file_data = (
            self.client
            .storage
            .from_(self.bucket_name)
            .download(name)
        )

        return ContentFile(
            file_data,
            name=os.path.basename(name)
        )

    def _save(self, name, content):
        """
        Upload Django ImageField/FileField content to Supabase.
        """

        name = self._generate_unique_name(name)

        if hasattr(content, "seek"):
            content.seek(0)

        file_data = content.read()

        content_type = getattr(
            content,
            "content_type",
            None
        )

        if not content_type:
            content_type = (
                mimetypes.guess_type(name)[0]
                or
                "application/octet-stream"
            )

        (
            self.client
            .storage
            .from_(self.bucket_name)
            .upload(
                path=name,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": "false",
                }
            )
        )

        return name

    def delete(self, name):
        """
        Delete file from Supabase Storage.
        """

        if not name:
            return

        name = self._clean_name(name)

        try:
            (
                self.client
                .storage
                .from_(self.bucket_name)
                .remove([name])
            )

        except Exception:
            pass

    def exists(self, name):
        """
        UUID filenames are generated during save,
        so Django does not need collision checking here.
        """

        return False

    def url(self, name):
        """
        Return public URL for a stored file.

        The Supabase bucket must be PUBLIC for this URL
        to display directly in <img> tags.
        """

        if not name:
            return ""

        name = self._clean_name(name)

        result = (
            self.client
            .storage
            .from_(self.bucket_name)
            .get_public_url(name)
        )

        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            return (
                result.get("publicUrl")
                or result.get("publicURL")
                or result.get("public_url")
                or ""
            )

        return str(result)

    def size(self, name):
        """
        Optional compatibility method.
        """

        return 0