from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    SLEEP_LONG: list[int] = [30, 90]
    SLEEP_RANDOM: list[int] = [3, 5]

    RANDOM_TAPS_COUNT: list[int] = [10, 19]
    SLEEP_BETWEEN_TAP: list[int] = [5, 10]     # token lifetime 60sec!

    APPLY_DAILY_BOOST: bool = True

    USE_PROXY_FROM_FILE: bool = False

settings = Settings()


