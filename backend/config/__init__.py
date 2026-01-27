from enum import Enum

from pydantic import BaseModel, PositiveInt

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, YamlConfigSettingsSource, DotEnvSettingsSource

class SecuritySettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: PositiveInt = 30

class OAPISettings(BaseModel):
    oapi_path: str

class EnvEnum(str, Enum):
    dev = 'dev'
    prod = 'prod'

class Settings(BaseSettings):
    name: str
    env: EnvEnum = EnvEnum.prod

    security: SecuritySettings
    oapi: OAPISettings

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
            DotEnvSettingsSource(settings_cls, env_file="config/.env", env_nested_delimiter="-"),
            env_settings
        )

config = Settings()
