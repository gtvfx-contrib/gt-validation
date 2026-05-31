"""Environment detection and Unreal Engine bootstrap helpers.

Detects whether the code is running inside Unreal Engine's embedded Python
interpreter or in a standalone Python environment.

Example::

    from validator.env import HAS_UNREAL

    if HAS_UNREAL:
        import unreal
        obj = unreal.EditorAssetLibrary.load_asset(path)
    else:
        # run filesystem-only checks
        ...

"""
import logging
from typing import Any, TYPE_CHECKING

from .errors import UnrealAPIError

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    import unreal


def _detectUnreal() -> tuple[bool, str | None]:
    """Return ``(available, version_prefix)`` for the Unreal Python API.

    Catches all exceptions (not just ``ImportError``) because IDE stubs may
    import successfully but crash with ``NameError`` during module
    initialization.

    Returns:
        A tuple of ``(True, "5.5.4")`` when inside Unreal, or
        ``(False, None)`` when running standalone.

    """
    try:
        import unreal  # noqa: F401
        ver = unreal.SystemLibrary.get_engine_version()
        return True, ver[:5]
    except Exception:
        return False, None


HAS_UNREAL: bool
UNREAL_VERSION: str | None
HAS_UNREAL, UNREAL_VERSION = _detectUnreal()


# ── Asset class name constants ────────────────────────────────────────────── #
ASSET_CLASS_STATIC_MESH = "StaticMesh"
ASSET_CLASS_TEXTURE_2D  = "Texture2D"
ASSET_CLASS_MATERIAL    = "Material"
ASSET_CLASS_NIAGARA     = "NiagaraSystem"
ASSET_CLASS_SKELETON    = "Skeleton"
ASSET_CLASS_ANIM        = "AnimSequence"


# ── Path helpers ──────────────────────────────────────────────────────────── #

def getContentDir() -> str | None:
    """Return the absolute disk path to the project's Content directory.

    Returns ``None`` when running outside Unreal.

    Example::

        >>> getContentDir()
        'C:/MyProject/Content/'   # only inside the Editor
    """
    if not HAS_UNREAL:
        return None
    return unreal.Paths.project_content_dir()


def getProjectDir() -> str | None:
    """Return the absolute disk path to the project root directory.

    Returns ``None`` when running outside Unreal.

    Example::

        >>> getProjectDir()
        'C:/MyProject/'   # only inside the Editor
    """
    if not HAS_UNREAL:
        return None
    return unreal.Paths.project_dir()


def getSelectedAssets() -> list:
    """
    Return the list of assets currently selected in the Content Browser.

    Returns an empty list when running outside Unreal or when no assets are
    selected.  Inside the Editor, each element is an ``unreal.Object``.

    Example::

        assets = getSelectedAssets()
        for asset in assets:
            print(asset.get_path_name())
    """
    if not HAS_UNREAL:
        return []
    return list(unreal.EditorUtilityLibrary.get_selected_assets())


def isEditor() -> bool:
    """Return True if we are running inside the Unreal Editor (not a cooked game).

    In this framework "unreal importable" already implies we are in the Editor,
    but ``unreal.is_editor()`` provides a precise confirmation for contexts
    where the unreal module might theoretically be available in a game process.
    """
    if not HAS_UNREAL:
        return False
    return unreal.is_editor()


def logEnvStatus() -> None:
    """Print a formatted banner showing the current runtime environment.

    Called once by ``ValidationRunner.validate_directory()`` so students can
    see at a glance whether Unreal introspection rules will run or be skipped.

    Example output (standalone)::

        ╔══════════════════════════════════════════════════════════════════════╗
        ║  Validation Framework — Environment Status                          ║
        ╠══════════════════════════════════════════════════════════════════════╣
        ║  Unreal Engine  : NOT AVAILABLE (standalone Python)                 ║
        ║  Unreal version : —                                                 ║
        ║  Unreal rules   : will be SKIPPED                                   ║
        ╚══════════════════════════════════════════════════════════════════════╝

    Example output (inside Editor)::

        ╔══════════════════════════════════════════════════════════════════════╗
        ║  Validation Framework — Environment Status                          ║
        ╠══════════════════════════════════════════════════════════════════════╣
        ║  Unreal Engine  : AVAILABLE                                         ║
        ║  Unreal version : 5.5.0-37670630+++UE5+Release-5.5                 ║
        ║  Project dir    : C:/MyProject/                                     ║
        ║  Content dir    : C:/MyProject/Content/                             ║
        ║  Unreal rules   : ACTIVE                                            ║
        ╚══════════════════════════════════════════════════════════════════════╝
    """
    width = 72
    inner = width - 4  # space between "║  " and "  ║"

    def _row(text: str) -> str:
        return f"║  {text:<{inner}}║"

    border_top = "╔" + "═" * (width - 2) + "╗"
    border_mid = "╠" + "═" * (width - 2) + "╣"
    border_bot = "╚" + "═" * (width - 2) + "╝"

    print(border_top)
    print(_row("Validation Framework — Environment Status"))
    print(border_mid)

    if HAS_UNREAL:
        print(_row("Unreal Engine  : AVAILABLE"))
        print(_row(f"Unreal version : {UNREAL_VERSION or 'unknown'}"))
        proj = getProjectDir()
        cont = getContentDir()
        if proj:
            print(_row(f"Project dir    : {proj}"))
        if cont:
            print(_row(f"Content dir    : {cont}"))
        print(_row("Unreal rules   : ACTIVE"))
    else:
        print(_row("Unreal Engine  : NOT AVAILABLE (standalone Python)"))
        print(_row("Unreal version : \u2014"))
        print(_row("Unreal rules   : will be SKIPPED"))

    print(border_bot)


def requireUnreal(msg: str = "") -> None:
    """Raise ``ImportError`` if Unreal is not available.

    Use this at the start of functions that absolutely require Unreal.

    Args:
        msg: Optional custom error message.  When empty, a default message
            is used.

    Raises:
        ImportError: If Unreal Engine is not available in the current
            Python environment.
    
    """
    if not HAS_UNREAL:
        raise ImportError(
            msg or "This feature requires Unreal Engine's Python environment."
        )


def loadUnrealAsset(asset_path: str) -> Any:
    """Load an Unreal Engine asset by its content-browser path.

    Provides a single, audited point for the broad ``except Exception``
    that the Unreal Python C++ bridge requires.  All rule implementations
    should call this helper rather than calling
    ``EditorAssetLibrary.load_asset`` directly.

    Args:
        asset_path: Content-browser path of the asset, e.g.
            ``"/Game/Characters/SK_Hero"``.

    Returns:
        The loaded Unreal asset object.

    Raises:
        UnrealAPIError: If Unreal is unavailable, if the API call raises,
            or if the returned asset is ``None``.
    
    """
    if not HAS_UNREAL:
        raise UnrealAPIError(
            f"Unreal Engine is not available; cannot load '{asset_path}'."
        )
    try:
        import unreal  # noqa: PLC0415 – deferred to avoid top-level ImportError
        obj = unreal.EditorAssetLibrary.load_asset(asset_path)
    except Exception as exc:  # noqa: BLE001 - Unreal bridge safety
        raise UnrealAPIError(
            f"Unreal API error loading '{asset_path}': {exc}"
        ) from exc
    if obj is None:
        raise UnrealAPIError(
            f"Asset '{asset_path}' could not be loaded (EditorAssetLibrary returned None)."
        )
    return obj
