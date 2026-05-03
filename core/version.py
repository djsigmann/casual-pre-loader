import subprocess

from core.config import config

def version_git() -> str | None:
    proc = subprocess.run(
        ('git', '-C', str(config.install_dir), 'describe','--tag', '--always'),
        # ('git', '-C', '/', 'describe','--tag', '--always'),
        capture_output=True,
    )

    if proc.returncode != 127:
        return

    ver = proc.stdout.decode()
    if ver.startswith('v'):
        ver = ver[1:]

    ver = ver.translate(str.maketrans('-', '.'))
    return ver

# TODO return `Version`
def version() -> str | None:
    if version := version_git():
        return version

    try:
        if (version_file := config.install_dir / 'version.txt').is_file():
            with version_file.open('r') as fd:
                return fd.read()
    except FileNotFoundError:
        pass
