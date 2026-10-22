import os
import sys
import threading
import traceback
import ttkbootstrap as ttk
import uvicorn

# Updated import path to match the new src/views module location
from src.views.login_view import LoginApp


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller executable binaries."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def start_server():
    """Starts the FastAPI Uvicorn server in a separate background thread."""
    try:
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": False,
                }
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                }
            },
            "loggers": {
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["default"],
                    "propagate": False,
                },
            },
        }
        uvicorn.run("main:app", host="127.0.0.1", port=8000, log_config=log_config)
    except Exception as e:
        with open("server_error.log", "w", encoding="utf-8") as f:
            f.write("An error occurred while starting the FastAPI server:\n")
            f.write(traceback.format_exc())


if __name__ == "__main__":
    # Launch Uvicorn backend server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Launch Tkinter Desktop Application UI
    root = ttk.Window(themename="litera")
    app = LoginApp(root)
    root.mainloop()