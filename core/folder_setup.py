import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from valve_parsers import PCFFile

# INFO: This file just allows package maintainers to set whether this application should act as if it is a portable installation.
# They can easily modify this file and set these values, e.g.
# `printf '%s\n' 'portable = False' >core/are_we_portable.py`
# This will make the application use paths outside the installation location.
from core.are_we_portable import portable
from core.constants import PROGRAM_AUTHOR, PROGRAM_NAME
from core.handlers.pcf_handler import get_parent_elements

log = logging.getLogger()


@dataclass
class FolderConfig:
    # configuration class for managing folder paths
    install_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent  # INFO: I'm not too sure if this can break or not, oh well
    portable = portable  # make sure it is accessible via self.portable

    # TODO: allow windows users to use non-portable installs (would allow us to remove this entire platform check)
    if portable:
        # default portable values
        project_dir = install_dir
        settings_dir = project_dir
    else:
        import platformdirs

        # default non-portable values
        project_dir = Path(platformdirs.user_data_dir(PROGRAM_NAME, PROGRAM_AUTHOR))
        settings_dir = Path(platformdirs.user_config_dir(PROGRAM_NAME, PROGRAM_AUTHOR))

        shutil.copytree(install_dir / "backup", project_dir / "backup", dirs_exist_ok=True)

    base_default_pcf: Optional[PCFFile] = field(default=None)
    base_default_parents: Optional[set[str]] = field(default=None)

    data_dir = install_dir / 'data'
    backup_dir = project_dir / 'backup'

    mods_dir = project_dir / 'mods'
    particles_dir = mods_dir / 'particles'
    addons_dir = mods_dir / 'addons'

    temp_dir = project_dir / 'temp'
    temp_download_dir = temp_dir  / 'download'
    temp_to_be_processed_dir = temp_dir / 'to_be_processed'
    temp_to_be_referenced_dir = temp_dir /  'to_be_referenced'
    temp_to_be_patched_dir = temp_dir /  'to_be_patched'
    temp_to_be_vpk_dir = temp_dir /  'to_be_vpk'

    modsinfo_file = project_dir / 'modsinfo.json'

    def initialize_pcf(self):
        if self.temp_to_be_referenced_dir.exists():
            default_base_path = self.temp_to_be_referenced_dir / "disguise.pcf"
            if default_base_path.exists():
                self.base_default_pcf = PCFFile(default_base_path).decode()
                self.base_default_parents = get_parent_elements(self.base_default_pcf)

    def cleanup_temp_folders(self) -> None:
        # anything put in temp/ will be gone !!!!!
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.base_default_pcf = None
            self.base_default_parents = None

    def get_temp_path(self, filename: str) -> Path:
        return self.temp_dir / filename

    def get_output_path(self, filename: str) -> Path:
        return self.temp_to_be_processed_dir / filename

    def get_backup_path(self, filename: str) -> Path:
        return self.backup_dir / filename

    def get_game_files_path(self, filename: str) -> Path:
        return self.temp_to_be_referenced_dir / filename


# create a default instance for import
folder_setup = FolderConfig()
