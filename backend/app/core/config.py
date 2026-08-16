from pydantic_settings import BaseSettings, SettingsConfigDict

# Create the settings class for the app
class Settings(BaseSettings):
    app_name: str
    app_version: str
    debug: bool

    database_url: str

    # Extra behavioural configuration for this Pydantic model:
    model_config = SettingsConfigDict(env_file='.env') # Tell FastAPI to look in the env file

settings = Settings()
