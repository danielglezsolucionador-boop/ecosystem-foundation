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

    @classmethod
    def from_mapping(cls, values: Mapping[str, str] | None = None) -> "Settings":
        source = environ if values is None else values
        environment = source.get("ECOSYSTEM_API_ENVIRONMENT", "local").strip().lower()

        if environment not in VALID_ENVIRONMENTS:
            allowed = ", ".join(sorted(VALID_ENVIRONMENTS))
            raise RuntimeError(
                "Invalid ECOSYSTEM_API_ENVIRONMENT. "
                f"Expected one of: {allowed}."
            )

        return cls(
            service_name=source.get(
                "ECOSYSTEM_API_SERVICE_NAME",
                "ecosystem-foundation-api",
            ).strip(),
            environment=environment,
            version=source.get("ECOSYSTEM_API_VERSION", "0.1.0").strip(),
            commit=source.get("ECOSYSTEM_API_COMMIT", "unknown").strip(),
            cors_origins=parse_csv(
                source.get("ECOSYSTEM_API_CORS_ORIGINS", "http://localhost:5173")
            ),
            debug=parse_bool(source.get("ECOSYSTEM_API_DEBUG", "false")),
        )


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings.from_mapping()

