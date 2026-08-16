from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "MedIntel"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


    # Authentication
    # Local research-prototype clinician boundary.
    # Empty defaults intentionally fail closed until .env is configured.
    JWT_SECRET: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CLINICIAN_USERNAME: str = ""
    CLINICIAN_PASSWORD_HASH: str = ""

    # XGBoost model artifacts
    XGB_MODEL_PATH: str = "models/xgboost/model.pkl"
    XGB_FEATURE_COLUMNS_PATH: str = "models/xgboost/feature_columns.json"
    XGB_DISEASE_LABELS_PATH: str = "models/xgboost/disease_labels.json"

    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = "backend/knowledge/diseases"
    KNOWLEDGE_BASE_ENABLED: bool = True

    # Clinical reasoning
    AI_REASONING_ENABLED: bool = False
    AI_PROVIDER: str = "local"
    PRIMARY_REASONING_MODEL: str = "google/medgemma-1.5-4b-it"
    LOCAL_MEDGEMMA_MODEL_ID: str = "google/medgemma-1.5-4b-it"
    MEDGEMMA_DEVICE: str = "auto"
    MEDGEMMA_BASE_URL: str = "http://127.0.0.1:8080"
    MEDGEMMA_MODEL_PATH: str = ""
    MEDGEMMA_TIMEOUT_SECONDS: int = 120
    MEDGEMMA_MAX_RETRIES: int = 1

    # Reasoning policy
    REASONING_PROMPT_VERSION: str = "clinical_reasoning_v1"
    REASONING_MAX_CANDIDATES: int = 5


    # Existing generic model version
    MODEL_VERSION: str = "latest"

    # Differential Diagnosis
    TOP_K: int = 5
    MIN_PROBABILITY: float = 0.10
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.60


settings = Settings()
