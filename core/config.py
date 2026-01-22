import logging
import sys
from dataclasses import dataclass, field, fields
from functools import cache
from typing import Annotated, cast

from cappa import Arg, Destructured, Group, Subcommand, command, parse

from core.constants import DESCRIPTION, PROGRAM_AUTHOR, PROGRAM_NAME
from core.folder_setup import FolderConfig
from core.version import VERSION


# The meat and potatoes
@dataclass
class Args:
    verbose: Annotated[bool, Arg(short=True, propagate=True)] = False
    """Increase the verbosity of log messages."""


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

    global config, subcommand

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

    subcommand = cast(_Subcommand, args.subcommand)
    config = Config(**{ # shallowly copy all attrs
        field.name: getattr(args.args, field.name)
        for field in fields(args.args)
    })


def __getattr__(attr):
    match attr:
        case 'config':
            _get_config()
            return config
        case 'subcommand':
            _get_config()
            return subcommand

    raise AttributeError(f"module '{__name__}' has no attribute '{attr}'")
