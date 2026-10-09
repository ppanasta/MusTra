"""Entry point for the packaged executable (PyInstaller).

No arguments: open the window.  With arguments: behave like the CLI.
"""

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        from mustra.cli import main as cli_main
        sys.exit(cli_main())
    from mustra.gui import main as gui_main
    gui_main()
