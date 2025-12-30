import logging
import socket
import tempfile
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from core.folder_setup import folder_setup
from core.util.file import move

log = logging.getLogger()


Reporthook = Callable[[int, float, float], None]


def download_file(url: str, path: Path, timeout: Optional[int] = None, reporthook: Optional[Reporthook] = None, noclobber: Optional[bool] = False) -> None:
    """
    Download a file to a temporary location, then move it into the destination.

    Args:
        url: URL to download.
        path: Path to move the downloaded file to. Parent directories are created as needed.
        timeout: Timeout in seconds.
        reporthook: Function to call when reporting download progress.
        noclobber: Throw an error if the destination exists (i.e. do not overwrite files).
    """

    folder_setup.temp_dir.mkdir(parents=True, exist_ok=True)
    tmp_file = tempfile.NamedTemporaryFile(prefix=path.name[:128], suffix='.part', dir=folder_setup.temp_dir, delete_on_close=False)
    tmp_path = Path(tmp_file.name)

    old_timeout = socket.getdefaulttimeout()

    try:
        socket.setdefaulttimeout(timeout)

        log.debug(f'downloading {url} -> {tmp_path}')
        urllib.request.urlretrieve(url, tmp_path, reporthook)

        tmp_file.close()
        move(tmp_path, path, noclobber=noclobber)
    except Exception as e:
        raise Exception(f'Error downloading file\n{url} -> {path}') from e
    finally:
        socket.setdefaulttimeout(old_timeout)

        try: # cleanup the tempfile
            with tmp_file:
                pass
        except ValueError:
            pass


def download_file_to_dir(url: str, dir: Path, timeout: Optional[int] = None, reporthook: Optional[Reporthook] = None, noclobber: Optional[bool] = False) -> Path:
    """
    Download a file to a temporary location, then move it into the destination, retaining its original filename.

    Args:
        url: URL to download.
        dir: Directory to download the file to. Parent directories are created as needed.
        timeout: Timeout in seconds.
        reporthook: Function to call when reporting download progress.
        noclobber: Throw an error if the destination exists (i.e. do not overwrite files).

    Returns:
        The final output Path.
    """

    path = dir / Path(urllib.parse.urlparse(url).path).name
    download_file(url, path, timeout, reporthook, noclobber)
    return path

def download_reporthook(
    set_value: Optional[Callable[[int], None]] = None,
    process: Optional[Callable[[None], None]] = None,
    was_canceled: Optional[Callable[[None], bool]] = None
) -> Reporthook:
    """
    Accepts multiple optional callbacks and returns a function using them that is compaticle with the `reporthook` argument of `urllib.request.urlretrieve()`.

    Args:
        set_value: Callback to update progress value.
        process: Callback to process progress updates.
        was_canceled: Callback to check if the operation was canceled.

    Returns:
        A function that is compatible with the `reporthook` argument of `urllib.request.urlretrieve()'.
    """

    def func(block_num: int, block_size: float, total_size: float) -> None:
        if was_canceled and was_canceled():
            raise Exception('Download cancelled by user')

        if set_value and total_size > 0:
            percent = int((block_num * block_size / total_size) * 100)
            set_value(min(percent, 99))

            if process:
                process()

    return func
