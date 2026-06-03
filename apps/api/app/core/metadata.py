from app.core.config import get_settings

settings = get_settings()

APP_NAME = settings.service_name
APP_VERSION = settings.version
APP_ENVIRONMENT = settings.environment
APP_COMMIT = settings.commit
