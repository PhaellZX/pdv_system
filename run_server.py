import uvicorn
import sys
import os
# Importamos o 'app' diretamente do nosso arquivo 'main'
from main import app

if __name__ == "__main__":
    try:
        # Configuração de log que evita erros em ambientes sem console
        log_config = {
            "version": 1, "disable_existing_loggers": False,
            "formatters": {"default": {"()": "uvicorn.logging.DefaultFormatter", "fmt": "%(levelprefix)s %(message)s", "use_colors": False}},
            "handlers": {"default": {"formatter": "default", "class": "logging.StreamHandler", "stream": "ext://sys.stderr"}},
            "loggers": {"uvicorn.error": {"level": "INFO"}, "uvicorn.access": {"level": "INFO", "handlers": ["default"], "propagate": False}},
        }
        # Passamos o objeto 'app' diretamente para o uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=log_config)
    except Exception as e:
        print(f"ERRO FATAL NO SERVIDOR: {e}")
    finally:
        input("\nO servidor foi encerrado. Pressione Enter para fechar...")