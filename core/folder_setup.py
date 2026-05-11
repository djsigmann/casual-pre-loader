from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from core.constants import PROGRAM_AUTHOR, PROGRAM_NAME


@dataclass
class FolderConfig:
    """Configuration class for managing folder paths"""

    install_dir: ClassVar[Path] = Path(__file__).resolve().parent.parent
    """The location the program is installed to"""
    data_dir:    ClassVar[Path] = install_dir / 'data'
    """The location where static data is housed"""

    mod_urls_file:            ClassVar[Path] = data_dir / 'mod_urls.json'
    """Contains URLs to all 'bundled' mods"""
    particle_system_map_file: ClassVar[Path] = data_dir / 'particle_system_map.json'
    """Contains map of particle system"""

    # INFO: This dummy file just allows package maintainers to set whether this application may act as a portable installation.
    # They can easily create this file, e.g.
    # `touch "${pkgdir}/usr/bin/lib/casual-pre-loader/.noportable"`
    portable: ClassVar[bool] = not (install_dir / '.noportable').is_file()
    """Is this program running portably, i.e. where do we write data to?"""

    project_dir:  ClassVar[Path]
    """Location of userdata"""
    settings_dir: ClassVar[Path]
    """Location of configuration"""
    temp_dir:     ClassVar[Path]
    """Location of remporary files"""
    if portable:
        project_dir  = install_dir / 'userdata' / 'data'
        settings_dir = install_dir / 'userdata' / 'config'
        temp_dir     = install_dir / 'userdata' / 'temp'
    else:
        import platformdirs

        project_dir  = platformdirs.user_data_path(PROGRAM_NAME, PROGRAM_AUTHOR)
        settings_dir = platformdirs.user_config_path(PROGRAM_NAME, PROGRAM_AUTHOR)
        temp_dir     = platformdirs.user_cache_path(PROGRAM_NAME, PROGRAM_AUTHOR)

    backup_dir:    Path = lambda self: self.project_dir / 'backup'                # ty: ignore[invalid-assignment]
    """Location where sourcemod files are backed up to"""
    log_file:      Path = lambda self: self.project_dir / 'casual-pre-loader.log' # ty: ignore[invalid-assignment]
    """File where logs are stored"""
    modsinfo_file: Path = lambda self: self.project_dir / 'modsinfo.json'         # ty: ignore[invalid-assignment]
    """File that records the last-downloaded version of 'bundled' mods"""

    mods_dir:      Path = lambda self: self.project_dir / 'mods'   # ty: ignore[invalid-assignment]
    """Location where mods are stored"""
    particles_dir: Path = lambda self: self.mods_dir / 'particles' # ty: ignore[invalid-assignment]
    """Location where PARTICLE mods are stored"""
    addons_dir:    Path = lambda self: self.mods_dir / 'addons'    # ty: ignore[invalid-assignment]
    """Location where ADDON mods are stored"""

    app_settings_file:   Path = lambda self: self.settings_dir / 'app_settings.json'   # ty: ignore[invalid-assignment]
    """File where main settings are kept"""
    addon_metadata_file: Path = lambda self: self.settings_dir / 'addon_metadata.json' # ty: ignore[invalid-assignment]
    """File where addon metadata is kept"""

    # TODO: add attr docstrings (@cueki)
    temp_to_be_processed_dir:  Path = lambda self: self.temp_dir / 'to_be_processed'  # ty: ignore[invalid-assignment]
    temp_to_be_referenced_dir: Path = lambda self: self.temp_dir / 'to_be_referenced' # ty: ignore[invalid-assignment]
    temp_to_be_patched_dir:    Path = lambda self: self.temp_dir / 'to_be_patched'    # ty: ignore[invalid-assignment]
    temp_to_be_vpk_dir:        Path = lambda self: self.temp_dir / 'to_be_vpk'        # ty: ignore[invalid-assignment]

    def __getattribute__(self, attr):
        value = super().__getattribute__(attr)

        if isinstance(value, Callable) and attr in self.__dict__:
            return value(self)
        return value


folder_setup: FolderConfig

def __getattr__(attr):
    global folder_setup

    match attr:
        case 'folder_setup':
            folder_setup = FolderConfig()
            return folder_setup

    raise AttributeError(f"module '{__name__}' has no attribute '{attr}'")
