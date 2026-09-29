from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str | None = None

    postgres_connection_string: str | None = None
    postgres_database_name: str | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    postgres_username: str | None = None
    postgres_password: str | None = None

    events_provider_url: str
    events_provider_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        if self.postgres_connection_string:
            url = self.postgres_connection_string

            if url.startswith("postgres://"):
                return "postgresql+asyncpg://" + url[len("postgres://"):]

            if url.startswith("postgresql://"):
                return "postgresql+asyncpg://" + url[len("postgresql://"):]

            return url

        if all(
            [
                self.postgres_database_name,
                self.postgres_host,
                self.postgres_port,
                self.postgres_username,
                self.postgres_password,
            ]
        ):
            return (
                "postgresql+asyncpg://"
                f"{self.postgres_username}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}"
                f"/{self.postgres_database_name}"
            )

        raise ValueError("PostgreSQL configuration is incomplete")


settings = Settings()
