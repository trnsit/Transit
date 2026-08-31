from pydantic_settings import BaseSettings, SettingsConfigDict

# Create the settings class for the app
class Settings(BaseSettings):
    app_name: str
    app_version: str
    debug: bool

    database_url: str

    secret_key: str
    jwt_algorithm: str = 'HS256'

    # Google OAuth Config.
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # GitHub OAuth Config.
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str

    # Ollama Config.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Extra behavioural configuration for this Pydantic model:
    model_config = SettingsConfigDict(env_file='.env') # Tell FastAPI to look in the env file

settings = Settings()
