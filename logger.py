import os
from logging import handlers, Formatter, getLogger, DEBUG
from datetime import datetime


class CustomTimedRotatingFileHandler(handlers.TimedRotatingFileHandler):
    def rotation_filename(self, default_name: str) -> str:
        # Add date suffix before file extension
        base, ext = os.path.splitext(default_name)
        date_suffix = datetime.now().strftime("%Y-%m-%d")
        return f"{base}_{date_suffix}{ext}"


# Base filename
filename = "./app.log"

# Create logger
logger = getLogger("applog")
logger.setLevel(DEBUG)

# Formatter
formatter = Formatter("[%(asctime)s] %(module)-10s| %(levelname)8s| %(message)s")

# Custom handler with weekly rotation on Friday
handler = CustomTimedRotatingFileHandler(
    filename=filename,
    when="w5",           # Rotate every Friday
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

handler.setFormatter(formatter)
logger.addHandler(handler)
