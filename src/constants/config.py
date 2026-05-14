import os

from dotenv import load_dotenv

load_dotenv()


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def required_env(name: str) -> str:
    value = env(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class LiveKitConfig:
    livekit_url = env("LIVEKIT_URL")
    livekit_api_key = env("LIVEKIT_API_KEY")
    livekit_api_secret = env("LIVEKIT_API_SECRET")
    livekit_agent_name = env("LIVEKIT_AGENT_NAME", "Exia")


class AWSConfig:
    aws_access_key = env("AWS_ACCESS_KEY_ID")
    aws_secret_key = env("AWS_SECRET_ACCESS_KEY")
    aws_region = env("AWS_REGION")


class MongoConfig:
    mongodb_uri = env("MONGODB_URI")
    mongodb_name = env("MONGODB_DATABASE_NAME")
    mongodb_session_collection = env("MONGODB_COLLECTION_NAME")
    mongodb_user_collection = env("MONGODB_USER_COLLECTION")



class ProviderConfig:
    aws_bedrock_api_key = env("AWS_BEDROCK_API_KEY")
    sarvam_api_key = env("SARVAM_API_KEY")
    deepgram_api_key = env("DEEPGRAM_API_KEY")
    Cartesia_api_key= env("CARTESIA_API_KEY")


