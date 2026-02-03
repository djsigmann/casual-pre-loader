from pathlib import Path


def get_vpk_name(game_path: Path | str) -> str:
    """Find the main *_misc_dir.vpk file for a Source mod."""
    path = Path(game_path)

    misc_vpks = list(path.glob("*_misc_dir.vpk"))
    if misc_vpks:
        return misc_vpks[0].name

    return "tf2_misc_dir.vpk"
