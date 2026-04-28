import logging
import sys
from dataclasses import dataclass, field, fields
from functools import cache
from pathlib import Path
from typing import Annotated, ClassVar, cast

from cappa import Arg, ArgAction, Destructured, Group, Subcommand, command, parse

from core.constants import DESCRIPTION, PROGRAM_AUTHOR, PROGRAM_NAME
from core.util.dep import Dep
from core.version import VERSION

# INFO: This dummy file just allows package maintainers to set whether this application may act as a portable installation.
# They can easily create this file, e.g.
# `touch "${pkgdir}/usr/bin/lib/casual-pre-loader/.noportable"`
_install_dir: Path = Path(__file__).resolve().parent.parent
_may_be_portable: bool = not (_install_dir / '.noportable').is_file()


# The meat and potatoes
@dataclass
class Args:
    if _may_be_portable: # we may only be portable if the application was not packaged with a dummy `.noportable` file
        portable: Annotated[bool, Arg(short='-P', long='--no-portable', action=ArgAction.store_false)] = True
        """Run portably, i.e. keep all userdata in `userdata/` instead of the appropriate user-specific locations depending on the OS."""
    else:
        portable: ClassVar[bool] = False
        """Run portably, i.e. keep all userdata in `userdata/` instead of the appropriate user-specific locations depending on the OS."""

    migrate: Annotated[bool, Arg(short='-M', long='--no-migrate')] = True
    """Migrate userdata from old locations to new ones."""

    verbose: Annotated[bool, Arg(short=True, propagate=True)] = False
    """Increase the verbosity of log messages."""


@dataclass
class FolderConfig:
    """Configuration class for managing folder paths"""

    install_dir: ClassVar[Path] = _install_dir
    """The location the program is installed to"""
    data_dir:    ClassVar[Path] = install_dir / 'data'
    """The location where static data is housed"""

    mod_urls_file:            ClassVar[Path] = data_dir / 'mod_urls.json'
    """Contains URLs to all 'bundled' mods"""
    particle_system_map_file: ClassVar[Path] = data_dir / 'particle_system_map.json'
    """Contains map of particle system"""

    project_dir:  ClassVar[Path]
    """Location of userdata"""
    settings_dir: ClassVar[Path]
    """Location of configuration"""
    temp_dir:     ClassVar[Path]
    """Location of remporary files"""

    # ruff: disable[function-call-in-dataclass-default-argument]
    backup_dir:    Path | Dep[Path] = Dep(lambda project_dir: project_dir / 'backup')
    """Location where sourcemod files are backed up to"""
    log_file:      Path | Dep[Path] = Dep(lambda project_dir: project_dir / 'casual-pre-loader.log')
    """File where logs are stored"""
    mods_dir:      Path | Dep[Path] = Dep(lambda project_dir: project_dir / 'mods')
    """Location where mods are stored"""
    modsinfo_file: Path | Dep[Path] = Dep(lambda project_dir: project_dir / 'modsinfo.json')
    """File that records the last-downloaded version of 'bundled' mods"""

    particles_dir: Path | Dep[Path] = Dep(lambda mods_dir: mods_dir / 'particles')
    """Location where PARTICLE mods are stored"""
    addons_dir:    Path | Dep[Path] = Dep(lambda mods_dir: mods_dir / 'addons')
    """Location where ADDON mods are stored"""

    app_settings_file:   Path | Dep[Path] = Dep(lambda settings_dir: settings_dir / 'app_settings.json')
    """File where main settings are kept"""
    addon_metadata_file: Path | Dep[Path] = Dep(lambda settings_dir: settings_dir / 'addon_metadata.json')
    """File where addon metadata is kept"""

    temp_to_be_processed_dir:  Path | Dep[Path] = Dep(lambda temp_dir: temp_dir / 'to_be_processed')
    """Temp location for particle elements extracted during a mod install, cleared once completed"""
    temp_to_be_referenced_dir: Path | Dep[Path] = Dep(lambda temp_dir: temp_dir / 'to_be_referenced')
    """Vanilla PCFs copied from `backup_dir/particles`, read as the unmodified reference when merging and patching"""
    temp_to_be_patched_dir:    Path | Dep[Path] = Dep(lambda temp_dir: temp_dir / 'to_be_patched')
    """PCFs staged for merging and patching before they are packed"""
    temp_to_be_vpk_dir:        Path | Dep[Path] = Dep(lambda temp_dir: temp_dir / 'to_be_vpk')
    """Final location of all files before being packed into the output VPK"""
    # ruff: enable[function-call-in-dataclass-default-argument]


# create a class that inherits all config dataclasess, initialize it using a union of an instance of each
# based on https://github.com/omni-us/jsonargparse/pull/796
@dataclass
class Config(Args, FolderConfig):
    pass


def _log_start(config: Config) -> None:
    logging.info(f'Version {VERSION} on {sys.platform} {"(portable)" if config.portable else ""}')
    logging.info(f'Application files are located in {config.install_dir}')
    logging.info(f'Project files are written to {config.project_dir}')
    logging.info(f'Settings files are in {config.settings_dir}')
    logging.info(f'Log is written to {config.log_file}')

    logging.debug('DEBUG OUTPUT HAS BEEN ENABLED')


def _perform_migrations(config: Config) -> None:
    if config.migrate:
        import core.migrations

        core.migrations.migrate()


@command
@dataclass
class Gui:
    """Opens the GUI (default)"""
    def __call__(self, config: Config) -> int:
        from main import gui

        _log_start(config)
        _perform_migrations(config)

        return gui()


_Subcommand = Gui


config: Config
subcommand: _Subcommand


@cache
def _get_config() -> None:
    """
    Parses CLI args and globally sets the relevant `Config` instance and subcommand, only runs once per execution without being manually called.
    """

    global Config, FolderConfig, config, subcommand

    @command(
        name=PROGRAM_NAME,
        default_long=True,
        epilog='Licensed under the terms of the GNU GPLv3 or any later version  \n'
        f'Copyright (c) 2026 {PROGRAM_AUTHOR}, {PROGRAM_NAME} contributors  \n'
        'For a full list of contributors, run `git shortlog -snei --group=author --group=trailer:co-authored-by`'
    )
    @dataclass
    class Cli:
        __doc__  = DESCRIPTION

        args: Destructured[Args]

        subcommand: Annotated[_Subcommand | None, Subcommand()] = field(default_factory=Gui)
        """Subcommand to run instead of opening the gui"""

    args = parse(
        Cli,
        version=Arg(
            f'{PROGRAM_NAME} {VERSION}',
            short='-V',
            long=True,
            help="Print the version string and exit.",
            group=Group(1, 'Help', section=2),
        ),
    )

    # NOTE: This is some fucking cursed-ass metaprogramming bullshit - but it works, but it works...
    # Perhaps weakly-typed dynamic languages *can* give one *too* much freedom...

    if args.args.portable:
        @dataclass
        class FolderConfig(FolderConfig):
            project_dir:  ClassVar[Path] = _install_dir / 'userdata' / 'data'
            settings_dir: ClassVar[Path] = _install_dir / 'userdata' / 'config'
            temp_dir:     ClassVar[Path] = _install_dir / 'userdata' / 'temp'
    else:
        import platformdirs

        @dataclass
        class FolderConfig(FolderConfig):
            project_dir  = platformdirs.user_data_path(PROGRAM_NAME, PROGRAM_AUTHOR)
            settings_dir = platformdirs.user_config_path(PROGRAM_NAME, PROGRAM_AUTHOR)
            temp_dir     = platformdirs.user_cache_path(PROGRAM_NAME, PROGRAM_AUTHOR)

    @dataclass
    class Config(Args, FolderConfig):
        pass

    subcommand = cast(_Subcommand, args.subcommand)
    config = Config(**{ # shallowly copy all attrs
        field.name: getattr(args.args, field.name)
        for field in fields(args.args)
    })


def __getattr__(attr):
    match attr:
        case 'Config':
            _get_config()
            return Config
        case 'FolderConfig':
            _get_config()
            return FolderConfig
        case 'config':
            _get_config()
            return config
        case 'subcommand':
            _get_config()
            return subcommand

    raise AttributeError(f"module '{__name__}' has no attribute '{attr}'")
