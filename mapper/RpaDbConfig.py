from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Set up logging
from log_config import get_logger

log = get_logger()


# Configuration class for the development environment
class DevConfig:
    def __init__(self):
        log.info("Setting up sqlite DB")
        self.DB_NAME = 'lld_gpt.db'
        self.DATABASE_URI = f'sqlite:///{self.DB_NAME}'


# enable this for dev config
config = DevConfig()
