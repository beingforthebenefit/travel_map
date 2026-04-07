from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    stadia_api_key: str = ""
    data_dir: str = "/data"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    max_upload_mb: int = 20
    nominatim_user_agent: str = "travel_map/1.0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
