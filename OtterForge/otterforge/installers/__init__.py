from .base import InstallerAdapter
from .inno_setup import InnoSetupAdapter
from .nsis import NSISAdapter
from .wix import WixAdapter
from .appimage import AppImageAdapter
from .pkgbuild import PkgBuildAdapter
from .registry import InstallerRegistry

__all__ = [
    "InstallerAdapter",
    "InstallerRegistry",
    "InnoSetupAdapter",
    "NSISAdapter",
    "WixAdapter",
    "AppImageAdapter",
    "PkgBuildAdapter",
]
