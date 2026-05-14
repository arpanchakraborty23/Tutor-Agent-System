import os
import logging
import asyncio

from livekit import agents, rtc, api
from livekit.agents import AgentServer, AgentSession, room_io,  JobProcess, metrics, MetricsCollectedEvent,  SessionUsageUpdatedEvent
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.agents.metrics import EOUMetrics, LLMMetrics, TTSMetrics, STTMetrics, VADMetrics, InterruptionMetrics

from src.voice_agent import ExiaHindi, ExiaEnglish, ExiaBengali
from src.constants import Credentials
from src.services.session import SessionManager
from src.utils import (
    build_user_profile_text,
    normalize_participant_attributes,
    parse_json_metadata,
)
from src.voice_agent import MetricsCollector


# Configuration
livekit_config = Credentials.livekit
aws_config = Credentials.aws


logger = logging.getLogger(__name__)
session_manager = SessionManager()
metrics_collector = MetricsCollector()

# Agent Server Setup
server = AgentServer(
    api_key=livekit_config.livekit_api_key,
    api_secret=livekit_config.livekit_api_secret,
    ws_url=livekit_config.livekit_url
)

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):

    ctx.log_context_fields = {
        "room_name": ctx.room.name,
    }

    await ctx.connect()
    participant = await ctx.wait_for_participant()

    # Build the runtime context 
    participant_metadata = parse_json_metadata(participant.metadata)
    participant_attributes = normalize_participant_attributes(
        getattr(participant, "attributes", None)
    )
    participant_context = {
        "identity": participant.identity,
        "name": participant.name,
        **participant_metadata,
    }
    logger.info("Participant context: %s", participant_context)

    # Conversation Recording
    req = api.RoomCompositeEgressRequest(
        room_name=ctx.room.name,
        audio_only=True,
        file_outputs=[
            api.EncodedFileOutput(
                file_type=api.EncodedFileType.MP4,
                filepath=f"recordings/{participant.identity}-{participant.name}.mp4",
                s3=api.S3Upload(
                    bucket=aws_config.aws_recording_bucket,
                    region=aws_config.aws_region,
                    access_key=aws_config.aws_access_key,
                    secret=aws_config.aws_secret_key,
                ),
            )
        ],
    )

    # Do not block the agent session if egress/recording setup fails.
    try:
        lkapi = api.LiveKitAPI()
        await lkapi.egress.start_room_composite_egress(req)
    except Exception as e:
        logger.warning(f"Egress start failed, continuing without recording: {e}")

    user_info = build_user_profile_text(participant_context)


    agent_setup = {
        "en": ExiaEnglish,
        "bn": ExiaBengali,
        "hi": ExiaHindi
    }


    agent = agent_setup['en']

    session = AgentSession(
        vad=silero.VAD.load(),
        turn_handling={
            "endpointing": {
                "mode": "dynamic",
                "min_delay": 0.5,
                "max_delay": 1.5,
            },
            "interruption":{
                "mode":"adaptive",
                "min_duration":0.4,
                "resume_false_interruption":True   
            },
            "preemptive_generation":{
                "enabled":True,
                "preemptive_tts":True,
            }
        }
    )

    # Initialize session manager with participant context
    session_manager.start(session_id=ctx.room.name, participant_context=participant_context)


    await session.start(
        room=ctx.room,
        agent=agent,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        m = ev.metrics

        if isinstance(m, STTMetrics):
            metrics_collector.collect_stt(m)
        elif isinstance(m, VADMetrics):
            metrics_collector.collect_vad(m)
        elif isinstance(m, EOUMetrics):
            metrics_collector.collect_eou(m)
        elif isinstance(m, LLMMetrics):
            metrics_collector.collect_llm(m)
        elif isinstance(m, TTSMetrics):
            metrics_collector.collect_tts(m)
        elif isinstance(m, InterruptionMetrics):
            metrics_collector.collect_interruption(m)

    @session.on("session_usage_updated")
    def _on_session_usage_updated(ev: SessionUsageUpdatedEvent):
        metrics_collector.update_session_usage(ev)

    # Event handler for conversation items
    @session.on("conversation_item_added")
    def on_conversation_item(event):
        """Handle conversation items (covers both user and agent messages)."""
        try:
            item = event.item
            if hasattr(item, 'content') and item.content:
                # Determine speaker based on item type or role
                speaker = "USER" if hasattr(item, 'role') and item.role == 'user' else "AGENT"
                
                # Log conversation entry
                log_entry = {
                    "role": speaker.lower(),
                    "message": item.content,
                    "speaker": speaker
                }
                session_manager.session_log(log_entry)
            
            if event.item.metrics:
                metrics_collector.add_turn_latency(event.item.role, event.item.metrics)

        except Exception as e:
            logger.error(f"Error logging conversation item: {e}")

    # Handle session shutdown and cleanup
    async def end_handler():
        """Handle session end and perform cleanup."""
        try:
            
            # End session and persist conversation to MongoDB
            session_manager.end_session()
            
            logger.info(f"Session for room {ctx.room.name} ended and cleaned up.")
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")

    ctx.add_shutdown_callback(end_handler)

if __name__ == "__main__":
    agents.cli.run_app(server)
