import logging
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

logger = logging.getLogger(__name__)

# HARDCODED CONSTANTS
# On Agent Engine / Platform runtime, GOOGLE_CLOUD_PROJECT evaluates to project NUMBER,
# which breaks Firestore/GCS if dynamic. Hardcode project ID and bucket name string.
BUCKET_NAME = "revelis-assets-d020ad"
PROJECT_ID = "qwiklabs-gcp-02-1a0a1ffea9f5"


async def generate_concept_image(prompt: str, tool_context: ToolContext) -> str:
    """Generate visual concept collateral (bespoke cakes, signature cocktails, decor mood boards) for an event.

    Args:
        prompt: Detailed description of the image concept to generate (e.g. 'A 3-tier elderflower celebration cake with edible rose gold leaf').
        tool_context: ADK ToolContext injected automatically by the framework.

    Returns:
        Confirmation message containing the public Cloud Storage HTTPS URL of the generated image asset.
    """
    try:
        client = genai.Client(
            vertexai=True, project=PROJECT_ID, location="global"
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image", contents=prompt
        )

        if not response.candidates or not response.candidates[0].content.parts:
            return "Failed to generate image concept: No candidates returned."

        part = response.candidates[0].content.parts[0]
        if not part.inline_data:
            return "Failed to generate image concept: Model did not return inline image data."

        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"
        ext = "jpg" if "jpeg" in mime_type else "png"

        filename = f"concept_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact in ADK tool_context for Playground / UI Artifacts panel
        artifact_part = types.Part.from_bytes(
            data=image_bytes, mime_type=mime_type
        )
        await tool_context.save_artifact(
            filename=filename, artifact=artifact_part
        )

        # 2. Upload exact image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated concept image. Public GCS URL: {public_url}"

    except Exception as e:
        logger.exception("Error generating concept image")
        return f"Error generating concept image: {str(e)}"
