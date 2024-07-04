import os
import subprocess


def launch() -> None:
    """
    Launch the main app.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    subprocess.run(["python3", "run", app_path])
