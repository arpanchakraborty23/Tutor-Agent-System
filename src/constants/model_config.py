from dataclasses import dataclass
from typing import ClassVar, Literal

from .credentials import ModelEnv

SupportedLanguage = Literal["en", "hi", "bn"]


@dataclass(frozen=True)
class LanguageModelConfig:
    """Voice model settings for one supported language."""
    code: str
    name: str
    stt: object
    llm: object
    tts: object
    greeting: str
    instructions: str


class ModelConfig:
    """Central model configuration for the voice agent."""

    DEFAULT_LANGUAGE: ClassVar[str] = "en"

    _LANGUAGE_MODELS: ClassVar[dict[str, LanguageModelConfig]] = {
        "en": LanguageModelConfig(
            code="en",
            name="English",
            stt=ModelEnv.livekit_stt_model_en,
            llm=ModelEnv.livekit_llm_model_en,
            tts=ModelEnv.livekit_tts_model_en,
            greeting="Hello, I am Kavya. How can I help you?",
            instructions="Respond in clear, concise English.",
        ),
        "hi": LanguageModelConfig(
            code="hi",
            name="Hindi",
            stt=ModelEnv.livekit_stt_model_hi,
            llm=ModelEnv.livekit_llm_model_hi,
            tts=ModelEnv.livekit_tts_model_hi,
            greeting="Namaste, main Kavya hoon. Main aapki kaise madad kar sakti hoon?",
            instructions="Respond in natural Hindi unless the user asks for another language.",
        ),
        "bn": LanguageModelConfig(
            code="bn",
            name="Bengali",
            stt=ModelEnv.livekit_stt_model_bn,
            llm=ModelEnv.livekit_llm_model_bn,
            tts=ModelEnv.livekit_tts_model_bn,
            greeting="Nomoskar, ami Kavya. Ami apnake ki bhabe sahajyo korte pari?",
            instructions="Respond in natural Bengali unless the user asks for another language.",
        ),
    }

    @classmethod
    def normalize_language(cls, language: str | None) -> str:
        if not language:
            return cls.DEFAULT_LANGUAGE

        code = language.strip().lower().replace("_", "-").split("-", maxsplit=1)[0]
        return code or cls.DEFAULT_LANGUAGE

    @classmethod
    def get_language_model(cls, language: str | None = None) -> LanguageModelConfig:
        code = cls.normalize_language(language)
        return cls._LANGUAGE_MODELS.get(code, cls._LANGUAGE_MODELS[cls.DEFAULT_LANGUAGE])

    @classmethod
    def get_models(cls, language: str | None = None) -> LanguageModelConfig:
        return cls.get_language_model(language)

    @classmethod
    def models(cls) -> dict[str, LanguageModelConfig]:
        return dict(cls._LANGUAGE_MODELS)

    @classmethod
    def supported_languages(cls) -> tuple[str, ...]:
        return tuple(cls._LANGUAGE_MODELS)


def get_models(language: SupportedLanguage = "en") -> LanguageModelConfig:
    return ModelConfig.get_language_model(language=language)


if __name__ == "__main__":
    print(get_models(language="en"))