from collections.abc import AsyncIterable


from livekit import rtc
from livekit.agents import Agent, ModelSettings, llm, stt
from livekit.agents.llm import ChatContext


class BaseAgent(Agent):
    """
    Extended Agent class with streaming capabilities for LLM, STT, and TTS.
    Optimized for ultra-fast streaming with minimal latency and async TTS.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize streaming agent with session tracking.

        Args:
            publish_interval: Publish to frontend every N tokens (default: 1 for max speed)
        """
        super().__init__(*args, **kwargs)
        self.language = "en"
        self._conversation_summary: str = ""
        self._max_ctx_items = 8

    @property
    def conversation_summary(self) -> str:
        return self._conversation_summary

    async def on_enter(self):
        await self.session.generate_reply()

    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> AsyncIterable[stt.SpeechEvent | str]:
        async def filtered_audio():
            async for frame in audio:
                yield frame

        async for event in Agent.default.stt_node(
            self, filtered_audio(), model_settings
        ):
            if event.alternatives:
                self.language = event.alternatives[0].language or self.language
            yield event

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk]:
        truncated_ctx = self.chat_ctx.truncate(max_items=self._max_ctx_items)
        await self._summarize_truncated_messages(self.chat_ctx, truncated_ctx)

        from livekit.agents.llm import Tool as LLMTool
        
        # Filter tools to only include Tool objects, not Toolset
        filtered_tools = [tool for tool in self.tools if isinstance(tool, LLMTool)]
        
        async for chunk in Agent.default.llm_node(
            self, chat_ctx=truncated_ctx, model_settings=model_settings, tools=filtered_tools
        ):
            yield chunk

    async def _summarize_truncated_messages(
        self, full_ctx: ChatContext, truncated_ctx: ChatContext
    ) -> None:
        if len(full_ctx.items) <= self._max_ctx_items:
            return

        truncated_count = len(full_ctx.items) - len(truncated_ctx.items)
        if truncated_count <= 0:
            return

        summary_ctx = ChatContext()
        summary_ctx.add_message(
            role="system",
            content="Summarize the following conversation briefly, capturing key points and context:",
        )

        for item in full_ctx.items[:truncated_count]:
            if item.type == "message" and item.role in ("user", "assistant"):
                text = (item.text_content or "").strip()
                if text:
                    summary_ctx.add_message(role="user", content=f"{item.role}: {text}")

        if len(summary_ctx.items) <= 1:
            return

        try:
            llm_instance = self.session.llm
            if llm_instance and isinstance(llm_instance, llm.LLM):
                response = await llm_instance.chat(chat_ctx=summary_ctx).collect()
                self._conversation_summary = (
                    response.text.strip() if response.text else ""
                )
        except Exception:
            pass

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        async for frame in Agent.default.tts_node(self, text, model_settings):
            yield frame






