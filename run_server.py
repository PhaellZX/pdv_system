import os
import sys
import uvicorn

# Direct import of the FastAPI application instance from main.py
from main import app

if __name__ == "__main__":
    try:
        # Logging configuration to prevent issues in headless or GUI-only environments
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
        # Passing the 'app' instance directly to Uvicorn runner
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=log_config)
    except Exception as e:
        print(f"FATAL SERVER ERROR: {e}")
    finally:
        input("\nThe server process has terminated. Press Enter to exit...")