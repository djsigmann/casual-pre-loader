from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from packaging.version import Version


class Asset(Protocol):
    """An abstract class representing a release's asset."""
    name: str
    browser_download_url: str
    digest: str


class Release(Protocol):
    """An abstract class representing a repository's release"""
    tag_name: str
    assets: Iterable[Asset]

@dataclass(frozen=True)
class Update:
    asset: Asset
    release: Release
    version: Version
