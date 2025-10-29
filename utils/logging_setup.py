import logging
import sys

def setup_logging():
    """
    Налаштовує базову конфігурацію логування для проєкту.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.info("Логування успішно налаштовано.")

def get_logger(name: str) -> logging.Logger:
    """
    Повертає екземпляр логера з вказаним ім'ям.

    Args:
        name: Ім'я логера (зазвичай __name__).

    Returns:
        Екземпляр логера.
    """
    return logging.getLogger(name)
