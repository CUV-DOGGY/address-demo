import logging

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(name)s-%(levelname)s-%(message)s")
)

# Configure only app.* loggers so third-party URLs cannot expose API keys.
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)
app_logger.propagate = False

if not app_logger.handlers:
    app_logger.addHandler(console_handler)
