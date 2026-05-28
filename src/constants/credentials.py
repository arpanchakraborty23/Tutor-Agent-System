
from dataclasses import dataclass

from livekit.plugins import aws, sarvam, deepgram, cartesia

from src.constants.config import (
    AWSConfig,
    LiveKitConfig,
    MongoConfig,
    ProviderConfig,
)



class ModelEnv:
    livekit_stt_model_en = deepgram.STT(
        model="nova-3",
        language="en-IN",
        api_key=ProviderConfig.deepgram_api_key
    )

    livekit_llm_model_en = sarvam.LLM(
        model="sarvam-105b-32k",
        api_key=ProviderConfig.sarvam_api_key,
        temperature=0.8,
        max_tokens=4096,
    )
    
    livekit_tts_model_en = cartesia.TTS(
        model="sonic-3",
        language="en",
        text_pacing=True,
        speed=1.2,
        volume=1,
        emotion=['Excited',"Amazed","Apologetic","Confident","Curious","Happy","Surprised"],
        api_key=ProviderConfig.Cartesia_api_key,
    )

    livekit_stt_model_hi = deepgram.STT(
        model="nova-3",
        language="hi-Latn",
        api_key=ProviderConfig.deepgram_api_key
    )

    livekit_llm_model_hi = sarvam.LLM(
        model="sarvam-105b-32k",
        api_key=ProviderConfig.sarvam_api_key,
        temperature=0.8,
        max_tokens=4096,
    )

    livekit_tts_model_hi = cartesia.TTS(
        model="sonic-3",
        language="hi",
        text_pacing=True,
        speed=1.2,
        volume=1,
        emotion=['Excited',"Amazed","Apologetic","Confident","Curious","Happy","Surprised"],
        api_key=ProviderConfig.Cartesia_api_key,

    )

    livekit_stt_model_bn = sarvam.STT(
        language="bn-IN",
        mode="transcribe",
        model="saaras:v2.5",
        api_key=ProviderConfig.sarvam_api_key

    )

    livekit_llm_model_bn =   sarvam.LLM(
        model="sarvam-105b-32k",
        api_key=ProviderConfig.sarvam_api_key,
        temperature=0.8,
        max_tokens=4096,
    )

    livekit_tts_model_bn = sarvam.TTS(
        api_key=ProviderConfig.sarvam_api_key,
        target_language_code="bn-IN",
        model="bulbul:v3",
    )


@dataclass(frozen=True)
class Credentials:
    livekit: type[LiveKitConfig] = LiveKitConfig
    aws: type[AWSConfig] = AWSConfig
    mongo: type[MongoConfig] = MongoConfig
    providers: type[ProviderConfig] = ProviderConfig
    models: type[ModelEnv] = ModelEnv
