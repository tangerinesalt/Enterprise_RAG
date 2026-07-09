import ntpath
import os


WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def validate_leaf_name(value: str, label: str = "name") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    if not value.strip():
        raise ValueError(f"{label} must not be empty")
    if value in {".", ".."}:
        raise ValueError(f"{label} must not be '.' or '..'")
    if "/" in value or "\\" in value:
        raise ValueError(f"{label} must not contain path separators")

    drive, _tail = ntpath.splitdrive(value)
    if drive:
        raise ValueError(f"{label} must not contain a drive prefix")
    if value.startswith(("/", "\\")):
        raise ValueError(f"{label} must not be absolute")
    if value.endswith((" ", ".")):
        raise ValueError(f"{label} must not end with a space or dot")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{label} must not contain control characters")

    illegal_windows_chars = '<>:"|?*'
    if any(ch in value for ch in illegal_windows_chars):
        raise ValueError(f"{label} must not contain Windows-illegal characters: {illegal_windows_chars}")

    reserved_key = value.rstrip(" .").split(".", 1)[0].upper()
    if reserved_key in WINDOWS_RESERVED_NAMES:
        raise ValueError(f"{label} uses a reserved Windows device name")
    return value


def validate_relative_path(value: str, label: str = "path") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    if not value.strip():
        raise ValueError(f"{label} must not be empty")

    drive, _tail = ntpath.splitdrive(value)
    if drive:
        raise ValueError(f"{label} must not contain a drive prefix")
    if value.startswith(("/", "\\")) or value.startswith("//") or value.startswith("\\\\"):
        raise ValueError(f"{label} must not be absolute")

    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if any(part == "" for part in parts):
        raise ValueError(f"{label} must not contain empty path segments")
    return "/".join(validate_leaf_name(part, label) for part in parts)


def resolve_under_root(root: str, relative_path: str, label: str = "path") -> str:
    normalized = validate_relative_path(relative_path, label)
    root_abs = os.path.abspath(root)
    candidate = os.path.abspath(os.path.join(root_abs, *normalized.split("/")))
    if os.path.commonpath([root_abs, candidate]) != root_abs:
        raise ValueError(f"{label} escapes the storage root")
    return candidate


def child_path(root: str, name: str, label: str = "name") -> str:
    leaf = validate_leaf_name(name, label)
    return resolve_under_root(root, leaf, label)


def basename_then_validate(filename: str, label: str = "filename") -> str:
    leaf = (filename or "").replace("\\", "/").split("/")[-1]
    return validate_leaf_name(leaf, label)
