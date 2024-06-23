import subprocess


def launch() -> None:
    """
    Launch the server app.
    """
    app_module = "fungi.server.api"
    subprocess.run(["uvicorn", f"{app_module}:app", "--reload"])
