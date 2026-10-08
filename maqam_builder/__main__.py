import sys

from .cli import main

if len(sys.argv) > 1:
    sys.exit(main())

from .gui import main as gui_main  # noqa: E402  (no arguments: open the window)

gui_main()
