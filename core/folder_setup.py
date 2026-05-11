from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import core.are_we_portable
from core.constants import PROGRAM_AUTHOR, PROGRAM_NAME


@dataclass
class FolderConfig:
    """Configuration class for managing folder paths"""

    # INFO: This file just allows package maintainers to set whether this application should act as if it is a portable installation.
    # They can easily modify this file and set these values, e.g.
    # `printf '%s\n' 'portable = False' >core/are_we_portable.py`
    # This will make the application use paths outside the installation location.
    portable: bool = core.are_we_portable.portable

    install_dir: Path = Path(__file__).resolve().parent.parent
    data_dir:    Path = install_dir / 'data'

    mod_urls_file:            Path = data_dir / 'mod_urls.json'
    particle_system_map_file: Path = data_dir / 'particle_system_map.json'

    if portable:
        # default portable values
        project_dir:  Path = install_dir / 'userdata' / 'data'
        settings_dir: Path = install_dir / 'userdata' / 'config'
        temp_dir:     Path = install_dir / 'userdata' / 'temp'
    else:
        import platformdirs

        # default non-portable values
        project_dir:  Path = platformdirs.user_data_path(PROGRAM_NAME, PROGRAM_AUTHOR)
        settings_dir: Path = platformdirs.user_config_path(PROGRAM_NAME, PROGRAM_AUTHOR)
        temp_dir:     Path = platformdirs.user_cache_path(PROGRAM_NAME, PROGRAM_AUTHOR)

    backup_dir:    Path = lambda self: self.project_dir / 'backup'                # ty: ignore[invalid-assignment]
    log_file:      Path = lambda self: self.project_dir / 'casual-pre-loader.log' # ty: ignore[invalid-assignment]
    modsinfo_file: Path = lambda self: self.project_dir / 'modsinfo.json'         # ty: ignore[invalid-assignment]

    mods_dir:      Path = lambda self: self.project_dir / 'mods'   # ty: ignore[invalid-assignment]
    particles_dir: Path = lambda self: self.mods_dir / 'particles' # ty: ignore[invalid-assignment]
    addons_dir:    Path = lambda self: self.mods_dir / 'addons'    # ty: ignore[invalid-assignment]

    app_settings_file:   Path = lambda self: self.settings_dir / 'app_settings.json'   # ty: ignore[invalid-assignment]
    addon_metadata_file: Path = lambda self: self.settings_dir / 'addon_metadata.json' # ty: ignore[invalid-assignment]

    temp_to_be_processed_dir:  Path = lambda self: self.temp_dir / 'to_be_processed'  # ty: ignore[invalid-assignment]
    temp_to_be_referenced_dir: Path = lambda self: self.temp_dir / 'to_be_referenced' # ty: ignore[invalid-assignment]
    temp_to_be_patched_dir:    Path = lambda self: self.temp_dir / 'to_be_patched'    # ty: ignore[invalid-assignment]
    temp_to_be_vpk_dir:        Path = lambda self: self.temp_dir / 'to_be_vpk'        # ty: ignore[invalid-assignment]

    def __getattribute__(self, attr):
        value = super().__getattribute__(attr)

        if isinstance(value, Callable) and attr in self.__dict__:
            return value(self)
        return value


folder_setup = FolderConfig() # create a default instance for import
