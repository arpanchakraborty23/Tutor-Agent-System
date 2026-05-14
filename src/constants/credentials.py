import os
from dataclasses import dataclass

from livekit.plugins import aws, elevenlabs, sarvam, speechmatics

from src.constants.config import (
    AWSConfig,
    LiveKitConfig,
    MongoConfig,
    ProviderConfig,
)
from src.utils.voice_detaction import known_speakers


class ModelEnv:
    livekit_stt_model_en = speechmatics.STT(
        api_key=ProviderConfig.speechmatics_api_key,
        enable_diarization=True,
        turn_detection_mode=TurnDetectionMode.SMART_TURN,
        speaker_active_format="<{speaker_id}>{text}</{speaker_id}>",
        speaker_passive_format="<PASSIVE><{speaker_id}>{text}</{speaker_id}></PASSIVE>",
        known_speakers=known_speakers,
        language="en",
    )

    livekit_llm_model_en = aws.LLM(
        model="amazon.nova-2-lite-v1:0",
        api_key=AWSConfig.aws_access_key,
        api_secret=AWSConfig.aws_secret_key,
        region=AWSConfig.aws_region or "us-east-1",
    )

    livekit_tts_model_en = elevenlabs.TTS(
        api_key=ProviderConfig.elevenlabs_api_key,
        model="eleven_multilingual_v2",
        enable_ssml_parsing=True,
        preferred_alignment="original",
        language="en",
        voice_id="BiFl9RPgDFLCWOsUHdjs",
    )

    livekit_stt_model_hi = speechmatics.STT(
        api_key=ProviderConfig.speechmatics_api_key,
        enable_diarization=True,
        turn_detection_mode=TurnDetectionMode.SMART_TURN,
        speaker_active_format="<{speaker_id}>{text}</{speaker_id}>",
        speaker_passive_format="<PASSIVE><{speaker_id}>{text}</{speaker_id}></PASSIVE>",
        known_speakers=known_speakers,
        language="hi",
    )

    livekit_llm_model_hi = aws.LLM(
        model="amazon.nova-2-lite-v1:0",
        api_key=AWSConfig.aws_access_key,
        api_secret=AWSConfig.aws_secret_key,
        region=AWSConfig.aws_region or "us-east-1",
    )
    livekit_tts_model_hi = elevenlabs.TTS(
        api_key=ProviderConfig.elevenlabs_api_key,
        model="eleven_multilingual_v2",
        enable_ssml_parsing=True,
        preferred_alignment="original",
        language="hi",
        voice_id="BiFl9RPgDFLCWOsUHdjs",
    )

    livekit_stt_model_bn = speechmatics.STT(
        api_key=ProviderConfig.speechmatics_api_key,
        enable_diarization=True,
        turn_detection_mode=TurnDetectionMode.SMART_TURN,
        speaker_active_format="<{speaker_id}>{text}</{speaker_id}>",
        speaker_passive_format="<PASSIVE><{speaker_id}>{text}</{speaker_id}></PASSIVE>",
        known_speakers=known_speakers,
        language="bn",
    )

    livekit_llm_model_bn = sarvam.LLM(
        model="sarvam-105b-32k",
        api_key=ProviderConfig.sarvam_api_key,
    )

    livekit_tts_model_bn = sarvam.TTS(
        api_key=ProviderConfig.sarvam_api_key,
        target_language_code="bn-IN",
        model="bulbul:v3",
        enable_cached_responses=True,
    )


@dataclass(frozen=True)
class Credentials:
    livekit: type[LiveKitConfig] = LiveKitConfig
    aws: type[AWSConfig] = AWSConfig
    mongo: type[MongoConfig] = MongoConfig
    redis: type[RedisConfig] = RedisConfig
    providers: type[ProviderConfig] = ProviderConfig
    models: type[ModelEnv] = ModelEnv
    mcp: type[McpConfig] = McpConfig