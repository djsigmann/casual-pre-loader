import logging
import os
import re
import sys
from operator import attrgetter
from pathlib import Path
from zipfile import Path as ZipFilePath

from packaging.version import Version

from core.config import config
from core.constants import BUILD_DIRS, BUILD_FILES, REMOTE_REPO
from core.util.file import copy, delete
from core.util.net import download_file
from core.util.repo import Update
from core.util.repo.github_api import get_releases_with_asset
from core.util.zip import FilterPredicate, extract
from core.version import VERSION

log = logging.getLogger()

"""
This module handles all the logic related to auto-updating.
One can assume that any functions in this file will only run if the application is installed portably.
"""

# TODO: what is needad for auto updates to be fully auto?
# - be able to tell if we were ran with a wrapper script [scripts/run.sh] (simplest method would be to use an envvar)
# - programatically get min python version (pyproject.toml)
# - programatically get dependency information (pyproject.toml)


def check_for_updates() -> tuple[Update, ...]:
    """
    Check the source repository for new releases.

    Returns:
        A tuple of updates sorted by ascending chronological order.
    """

    try: # get the latest version of each minor release that we are behind of
        updates = {}
        current = Version(VERSION)
        platform_name = 'linux' if sys.platform == 'linux' else 'win'

        # sort by descending chronological order, so we only store the latest patch release for every major release
        for update in sorted(get_releases_with_asset(REMOTE_REPO, re.compile(fr'^casual-pre-?loader(-{platform_name})?.*\.zip')), key=attrgetter('version'), reverse=True):
            if update.version > current: # we could opt to break if conditional fails, but we'd probably only save milliseconds at most
                updates.setdefault(update.version.major, update)

        return tuple(update for update in updates.values())[::-1] # reverse the tuple so it's sorted by ascending chronological order

    except Exception:
        log.exception('Error checking for updates')
        return tuple()


def download_updates(updates: tuple[Update, ...] | None = None) -> None:
    """
    Download all available updates.

    Args:
        updates: An optional tuple of updates. If this is not supplied, the output of `check_for_updates()` is used.
    """

    # TODO: update this once we can update multiple at a time

    if updates is None:
        updates = check_for_updates()

    archive_paths: dict = {}
    for update in updates:
        archive_path = config.temp_dir / 'update' / f'{update.release.tag_name}.zip'
        archive_paths[update.release.tag_name] = archive_path

        try:
            log.info(f'Downloading application update ({update.release.tag_name})')
            download_file(update.asset.browser_download_url, archive_path, 30)
        except Exception:
            log.exception(f'Error downloading update {update.release.tag_name}')
            break

    state_file = config.temp_dir / 'update' / 'state.json'
    state: dict = {'args': sys.argv, 'pending': archive_paths}

    import json
    with state_file.open('w') as fd:
        json.dump(state, fd)

    perform_update()


def perform_update() -> None:
    import json

    state_file = config.temp_dir / 'update' / 'state.json'
    try:
        with state_file.open('r') as fd:
            state: dict = json.load(fd)
    except FileNotFoundError:
        log.exception('Could not find state file in temporary dir')

    tag_name = sorted(state['pending'].keys(), key=Version)[0]
    archive_path = Path(state['pending'][tag_name])
    del state['pending'][tag_name]

    match sys.platform:
        case 'win32':
            renamed_runme = config.install_dir.parent / 'RUNME.tmp.bat'

            try:
                extract(archive_path, config.install_dir.parent / '.tmp_update', 0, False, None)
                copy(config.install_dir.parent / 'RUNME.bat', renamed_runme) # INFO: we need to rename RUNME on windows to avoid file lock issues
            except Exception:
                log.exception(f'Error extracting update {tag_name}')

                delete(config.install_dir.parent / '.tmp_update')
                delete(renamed_runme)

            os.chdir('..')

            eexec_args = ('cmd.exe', ['cmd.exe', '/c', '.\\' + renamed_runme.name])
            if not state['pending']:
                eexec_args[1].extend(state['args'][1:])

        case 'linux':
            include = tuple((*BUILD_FILES, *BUILD_DIRS))
            def _filter(root: ZipFilePath) -> FilterPredicate:
                def __filter(path: ZipFilePath) -> bool:
                    rel = path.relative_to(root)
                    return any(map(lambda x: rel.startswith(x), include))

                return __filter

            try:
                extract(archive_path, config.install_dir, 1, False, _filter)
            except Exception:
                log.exception(f'Error extracting update {tag_name}')

            exec_args = (sys.executable, [sys.executable])
            if not state['pending']:
                exec_args[1].extend(state['args'])

    delete(archive_path)

    if state['pending']:
        with state_file.open('w'):
            json.dump(state,fd)

        if config.verbose:
            exec_args[1].append('-v')
    else:
        delete(state_file.parent)
        exec_args[1].append('update')

    os.execve(*exec_args, os.environ) # NOTE: quits the interpreter and re-executes
