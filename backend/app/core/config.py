from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://sizehive:sizehive@localhost:55432/sizehive"
    cors_origins: list[str] = ["http://localhost:5173"]

    awin_feed_url: str | None = None

    # --- Accounts -------------------------------------------------------
    #: Where login links point. The token is appended as ?token=…
    frontend_base_url: str = "http://localhost:5173"
    login_token_ttl_minutes: int = 20
    session_ttl_days: int = 30
    #: Send the session cookie only over HTTPS. Must be True in production;
    #: False by default so the plain-HTTP dev setup works.
    session_cookie_secure: bool = False

    # --- Mail -----------------------------------------------------------
    #: Without smtp_host, mail is written to the log instead of being sent.
    #: That keeps login and the notification run fully usable in dev.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True
    mail_from: str = "sizehive <noreply@sizehive.local>"


settings = Settings()
