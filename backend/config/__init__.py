from enum import Enum

from pydantic import BaseModel, PositiveInt

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, YamlConfigSettingsSource, DotEnvSettingsSource

class SecuritySettings(BaseModel):
    secretkey: str
    algorithm: str
    access_token_expire_minutes: PositiveInt = 30

class Postgres(BaseModel):
    username: str
    password: str
    url: str
    database: str

class OAPISettings(BaseModel):
    oapi_path: str

class EnvEnum(str, Enum):
    dev = 'dev'
    prod = 'prod'

class Settings(BaseSettings):
    name: str
    env: EnvEnum = EnvEnum.prod
    domain: str

    security: SecuritySettings
    oapi: OAPISettings
    postgres: Postgres

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlConfigSettingsSource(settings_cls, yaml_file="config/config.yaml"),
            DotEnvSettingsSource(settings_cls, env_file=".env", env_nested_delimiter="_", case_sensitive=False),
            env_settings
        )

config = Settings()
