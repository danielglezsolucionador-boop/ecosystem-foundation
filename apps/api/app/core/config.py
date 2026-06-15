from dataclasses import dataclass
from functools import lru_cache
from os import environ
from typing import Mapping

VALID_ENVIRONMENTS = {"local", "staging", "production"}


@dataclass(frozen=True)
class Settings:
    service_name: str
    environment: str
    version: str
    commit: str
    cors_origins: tuple[str, ...]
    debug: bool
    database_url: str
    database_url_source: str
    anthropic_api_key: str | None
    cerebro_llm_model: str
    cerebro_llm_enabled: bool

    @classmethod
    def from_mapping(cls, values: Mapping[str, str] | None = None) -> "Settings":
        source = environ if values is None else values
        environment = resolve_environment(source)

        if environment not in VALID_ENVIRONMENTS:
            allowed = ", ".join(sorted(VALID_ENVIRONMENTS))
            raise RuntimeError(
                "Invalid ECOSYSTEM_API_ENVIRONMENT. "
                f"Expected one of: {allowed}."
            )

        database_url, database_url_source = resolve_database_url(source)

        return cls(
            service_name=env_value(
                source,
                "ECOSYSTEM_API_SERVICE_NAME",
                "ecosystem-foundation-api",
            ),
            environment=environment,
            version=env_value(source, "ECOSYSTEM_API_VERSION", "0.1.0"),
            commit=resolve_commit(source),
            cors_origins=parse_csv(
                env_value(source, "ECOSYSTEM_API_CORS_ORIGINS", "http://localhost:5173")
            ),
            debug=parse_bool(env_value(source, "ECOSYSTEM_API_DEBUG", "false")),
            database_url=database_url,
            database_url_source=database_url_source,
            anthropic_api_key=optional_env_value(source, "ANTHROPIC_API_KEY"),
            cerebro_llm_model=env_value(source, "CEREBRO_LLM_MODEL", "claude-sonnet-4-6"),
            cerebro_llm_enabled=parse_bool(env_value(source, "CEREBRO_LLM_ENABLED", "true")),
        )


def env_value(source: Mapping[str, str], key: str, default: str) -> str:
    value = source.get(key)
    if value is None:
        return default

    value = value.strip()
    return value if value else default


def optional_env_value(source: Mapping[str, str], key: str) -> str | None:
    value = source.get(key)
    if value is None:
        return None

    value = value.strip()
    return value or None


def resolve_environment(source: Mapping[str, str]) -> str:
    explicit_environment = optional_env_value(source, "ECOSYSTEM_API_ENVIRONMENT")
    if explicit_environment:
        return explicit_environment.lower()

    vercel_environment = optional_env_value(source, "VERCEL_ENV")
    if vercel_environment == "production":
        return "production"
    if vercel_environment == "preview":
        return "staging"

    return "local"


def resolve_commit(source: Mapping[str, str]) -> str:
    vercel_commit = optional_env_value(source, "VERCEL_GIT_COMMIT_SHA")
    if vercel_commit:
        return vercel_commit[:7]

    return env_value(source, "ECOSYSTEM_API_COMMIT", "unknown")


def resolve_database_url(source: Mapping[str, str]) -> tuple[str, str]:
    ecosystem_url = optional_env_value(source, "ECOSYSTEM_API_DATABASE_URL")
    if ecosystem_url:
        return ecosystem_url, "ECOSYSTEM_API_DATABASE_URL"

    database_url = optional_env_value(source, "DATABASE_URL")
    if database_url:
        return database_url, "DATABASE_URL"

    return "sqlite:///./var/ecosystem_foundation.db", "default"


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings.from_mapping()
