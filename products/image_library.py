"""ONE flat folder for every catalogue image:   static/image_library/

Admins no longer upload pictures (that used up external storage). They drop the
files into this folder once (commit + deploy) and, when adding a category /
product / colour in the admin panel, simply PICK the images from this folder.
Only the file NAME is stored in the database; the picture is served as a normal
static file.

Old rows that still point at an uploaded file keep working: LibraryStorage
falls back to the normal (Supabase / media) storage for any name that is not in
this folder.
"""
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage, default_storage
from django.templatetags.static import static
from django.utils.deconstruct import deconstructible

LIBRARY_DIR_NAME = "image_library"
LIBRARY_ROOT = Path(settings.BASE_DIR) / "static" / LIBRARY_DIR_NAME
IMAGE_EXTS = {".webp", ".jpg", ".jpeg", ".png", ".avif", ".gif"}


def _natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _scan():
    if not LIBRARY_ROOT.is_dir():
        return []
    files = [p.name for p in LIBRARY_ROOT.iterdir()
             if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not p.name.startswith(".")]
    return sorted(files, key=_natural)


@lru_cache(maxsize=1)
def _cached():
    return tuple(_scan())


def list_names():
    """Every image file name in the library (re-scanned each time in DEBUG)."""
    return _scan() if settings.DEBUG else list(_cached())


def is_valid(name):
    """True only for a plain file name that really exists in the library."""
    return bool(name) and "/" not in name and "\\" not in name and name in set(list_names())


def clean_names(names):
    """Keep only valid library names, drop duplicates, preserve the picked order."""
    seen, out = set(), []
    for n in names or []:
        n = (n or "").strip()
        if n and n not in seen and is_valid(n):
            seen.add(n)
            out.append(n)
    return out


def library_url(name):
    path = f"{LIBRARY_DIR_NAME}/{name}"
    try:
        return static(path)
    except ValueError:  # manifest storage and collectstatic not re-run yet
        return f"{settings.STATIC_URL}{path}"


def listing():
    """[{name, url}] for the admin picker."""
    return [{"name": n, "url": library_url(n)} for n in list_names()]


@deconstructible
class LibraryStorage(Storage):
    """Storage used by the catalogue ImageFields.

    * a name that is in static/image_library/  -> served as a static file
    * any other name (old uploads)             -> delegated to the default storage
    """

    def url(self, name):
        if is_valid(name):
            return library_url(name)
        return default_storage.url(name)

    def exists(self, name):
        return is_valid(name) or default_storage.exists(name)

    def _open(self, name, mode="rb"):
        if is_valid(name):
            return File(open(LIBRARY_ROOT / name, mode))
        return default_storage.open(name, mode)

    def size(self, name):
        if is_valid(name):
            return (LIBRARY_ROOT / name).stat().st_size
        return default_storage.size(name)

    def path(self, name):
        if is_valid(name):
            return str(LIBRARY_ROOT / name)
        return default_storage.path(name)

    # Library files are never deleted from here; old uploads still can be.
    def delete(self, name):
        if not is_valid(name):
            default_storage.delete(name)

    # Only reached by the legacy Django /admin upload widgets.
    def get_available_name(self, name, max_length=None):
        return default_storage.get_available_name(name, max_length)

    def _save(self, name, content):
        return default_storage.save(name, content)


def library_storage():
    """Callable referenced by the model fields / migrations."""
    return LibraryStorage()
