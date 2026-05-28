from __future__ import annotations

from livekit.agents import ChatContext, inference
from livekit.agents.llm import FallbackAdapter as LLMFallBack
from livekit.agents.stt import FallbackAdapter as STTFallBack
from livekit.agents.tts import FallbackAdapter as TTSFallBack
from livekit.plugins import deepgram, sarvam, silero

from . import BaseAgent
from src.constants import ProviderConfig, get_models

# Model Configuration
english_models = get_models(language="en")
hindi_models = get_models(language="hi")
bengali_models = get_models(language="bn")


class ExiaEnglish(BaseAgent):
    def __init__(self, *, vad: silero.VAD = None, chat_ctx: ChatContext = None) -> None:
        self._vad = vad
        super().__init__(
            instructions="You are a helpful voice AI assistant.",
            stt=STTFallBack(
                stt=[
                    english_models.stt,
                    inference.STT(model="assemblyai/universal-streaming"),
                    deepgram.STT(
                        model="nova-3",
                        language="en-IN",
                        enable_diarization=True,
                        api_key=ProviderConfig.deepgram_api_key,
                    ),
                ]
            ),
            llm=LLMFallBack(
                llm=[
                    english_models.llm,
                    inference.LLM(model="openai/gpt-4.1-mini")
                ]
            ),
            tts=TTSFallBack(
                tts=[
                    english_models.tts,
                    inference.TTS(model="elevenlabs/eleven_multilingual_v2"),
                    sarvam.TTS(
                        target_language_code="en-IN",
                        api_key=ProviderConfig.sarvam_api_key
                    ),
                ]
            ),
            chat_ctx=chat_ctx,
            vad=vad,
        )


class ExiaHindi(BaseAgent):
    def __init__(self, *, vad: silero.VAD = None, chat_ctx: ChatContext = None) -> None:
        self._vad = vad
        super().__init__(
            instructions=hindi_models.instructions,
            stt=STTFallBack(
                stt=[
                    hindi_models.stt,
                    deepgram.STT(
                        model="nova-3",
                        language="hi-IN",
                        enable_diarization=True,
                        api_key=ProviderConfig.deepgram_api_key,
                    ),
                ]
            ),
            llm=LLMFallBack(
                llm=[
                    hindi_models.llm,
                    inference.LLM(model="openai/gpt-4.1-mini"),
        
                ]
            ),
            tts=TTSFallBack(
                tts=[
                    hindi_models.tts,
                    sarvam.TTS(
                        target_language_code="hi-IN",
                        api_key=ProviderConfig.sarvam_api_key
                    ),
                ]
            ),
            chat_ctx=chat_ctx,
            vad=vad,
        )


class ExiaBengali(BaseAgent):
    def __init__(self, *, vad: silero.VAD = None, chat_ctx: ChatContext = None) -> None:
        self._vad = vad
        super().__init__(
            instructions=bengali_models.instructions,
            stt=STTFallBack(
                stt=[
                    bengali_models.stt,
                    deepgram.STT(
                        model="nova-3",
                        language="bn-IN",
                        enable_diarization=True,
                        api_key=ProviderConfig.deepgram_api_key,
                    ),
                ]
            ),
            llm=LLMFallBack(
                llm=[
                    bengali_models.llm,
                    inference.LLM(model="openai/gpt-4.1-mini"),
                ]
            ),
            tts=TTSFallBack(
                tts=[
                    bengali_models.tts,
                    sarvam.TTS(
                        target_language_code="bn-IN",
                        api_key=ProviderConfig.sarvam_api_key,
                    ),
                ]
            ),
            chat_ctx=chat_ctx,
            vad=vad,
        )
