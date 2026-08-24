"""Entrada compatível para usuários do TurboTaskManager."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from eqo.cli.interface import main  # noqa: E402

if __name__ == "__main__":
    main()
