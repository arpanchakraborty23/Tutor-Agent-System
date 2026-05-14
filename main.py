import os
import logging
import asyncio
from dotenv import load_dotenv

from livekit import agents, rtc, api
from livekit.agents import AgentServer, AgentSession, room_io, TurnHandlingOptions, JobProcess
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.agents.metrics import EOUMetrics, LLMMetrics, TTSMetrics

from src.services.session import SessionManager
from src.voice_agent.agents import Assistant
from src.prompt.english import english_prompt
from src.utils import (
    build_user_profile_text,
    normalize_participant_attributes,
    parse_json_metadata,
)
from src.services.metrics import ModelMetrics


# Configuration
load_dotenv(".env")
logger = logging.getLogger(__name__)
session_manager = SessionManager()
model_metrics = ModelMetrics()
server = AgentServer()

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

    # Start the agent session with the specified configurations
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SCERATE_KEY")

    req = api.RoomCompositeEgressRequest(
        room_name=ctx.room.name,
        audio_only=True,
        file_outputs=[
            api.EncodedFileOutput(
                file_type=api.EncodedFileType.MP4,
                filepath="recordings/my-room-test.ogg",
                s3=api.S3Upload(
                    bucket=os.getenv("AWS_BUCKET_NAME"),
                    region=os.getenv("AWS_REGION"),
                    access_key=aws_access_key,
                    secret=aws_secret_key,
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
    agent = Assistant()._tutor(
        language="english",
        instructions=english_prompt(user_info=user_info),
        initial_ctx=None,
    )

    session = AgentSession(
        stt="deepgram/nova-3:multi",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        turn_handling=TurnHandlingOptions(
            turn_detection=EnglishModel(),
        ),
    )

    # Initialize session manager with participant context
    session_manager.start(session_id=ctx.room.name, participant_context=participant_context)

    # NOTE: Metrics collection via session.metrics_collected is not directly available in AgentSession API.
    # Metrics tracking is now handled through:
    # 1. Session end event - latency stats retrieved via session_manager.get_latency_stats()
    # 2. Conversation items - logged via on_conversation_item handler
    # 3. Manual tracking - session_manager.track_latency() can be called from within agents

    await session.start(
        room=ctx.room,
        agent=agent,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

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
        except Exception as e:
            logger.error(f"Error logging conversation item: {e}")

    # Handle session shutdown and cleanup
    async def end_handler():
        """Handle session end and perform cleanup."""
        try:
            # Print metrics summary before ending
            model_metrics.print_summary()
            
            # Print latency statistics
            latency_stats = session_manager.get_latency_stats()
            logger.info(f"Session Latency Statistics: {latency_stats}")
            
            # End session and persist conversation to MongoDB
            session_manager.end_session()
            
            logger.info(f"Session for room {ctx.room.name} ended and cleaned up.")
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")

    ctx.add_shutdown_callback(end_handler)

if __name__ == "__main__":
    agents.cli.run_app(server)
