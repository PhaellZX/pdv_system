import uvicorn
import threading
import tkinter as tk
import ttkbootstrap as ttk
from login_app import LoginApp
import sys
import os
import traceback

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_server():
    try:
        log_config = {
            "version": 1, "disable_existing_loggers": False,
            "formatters": {"default": {"()": "uvicorn.logging.DefaultFormatter", "fmt": "%(levelprefix)s %(message)s", "use_colors": False}},
            "handlers": {"default": {"formatter": "default", "class": "logging.StreamHandler", "stream": "ext://sys.stderr"}},
            "loggers": {"uvicorn.error": {"level": "INFO"}, "uvicorn.access": {"level": "INFO", "handlers": ["default"], "propagate": False}},
        }
        uvicorn.run("main:app", host="127.0.0.1", port=8000, log_config=log_config)
    except Exception as e:
        with open("server_error.log", "w") as f:
            f.write("Ocorreu um erro ao iniciar o servidor FastAPI:\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    root = ttk.Window(themename="litera")
    app = LoginApp(root, resource_path_func=resource_path)
    root.mainloop()