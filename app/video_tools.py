import logging
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

logger = logging.getLogger(__name__)

# HARDCODED CONSTANTS
BUCKET_NAME = "revelis-assets-d020ad"
PROJECT_ID = "qwiklabs-gcp-02-1a0a1ffea9f5"


async def generate_video_preview(prompt: str, tool_context: ToolContext) -> dict:
    """Generate a short video preview for items in Revelis's domain (such as a cinematic slow-motion pour of a signature cocktail or a rotating celebration cake showcase).

    Args:
        prompt: Detailed description of the video preview concept to generate.
        tool_context: ADK ToolContext injected automatically by the framework.

    Returns:
        A dictionary containing the video_url and status.
    """
    try:
        client = genai.Client(
            vertexai=True, project=PROJECT_ID, location="global"
        )

        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        if not interaction or not interaction.output_video or not interaction.output_video.data:
            logger.error("Model did not return video data")
            return {"status": "error", "error": "Model did not return video data"}

        video_bytes = interaction.output_video.data
        mime_type = "video/mp4"

        filename = f"preview_{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save artifact in ADK tool_context for Playground / UI Artifacts panel
        artifact_part = types.Part.from_bytes(
            data=video_bytes, mime_type=mime_type
        )
        try:
            await tool_context.save_artifact(
                filename="preview.mp4", artifact=artifact_part
            )
        except Exception as ae:
            logger.warning(f"save_artifact failed: {ae}")

        # 2. Upload exact video bytes to public Cloud Storage bucket with content_type="video/mp4"
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        logger.info(f"Successfully generated video preview: {public_url}")
        return {
            "status": "success",
            "video_url": public_url,
        }

    except Exception as e:
        logger.exception("Error generating video preview")
        return {"status": "error", "error": str(e)}

