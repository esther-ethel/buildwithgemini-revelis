# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from app.a2ui_utils import a2ui_callback
from app.firestore_tools import (
    add_itinerary_item,
    add_menu_item,
    get_itinerary,
    get_menu_items,
)
from app.image_tools import generate_concept_image
from app.logistics_tools import validate_and_generate_event_logistics
from app.video_tools import generate_video_preview
from app.weather_tools import get_destination_weather

# Memory Bank & Agent Engine constants
MEMORY_BANK_ID = "21721401962528768"
PROJECT_ID = "qwiklabs-gcp-02-1a0a1ffea9f5"
LOCATION = "us-central1"

# Load Agent Engine resource name from deployment_metadata.json if present
metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_resource_name = None
if metadata_file.exists():
    try:
        with open(metadata_file) as f:
            metadata = json.load(f)
            agent_engine_resource_name = metadata.get("remote_agent_runtime_id")
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        import logging

        logging.warning(f"Failed to add session to memory: {e}")
    return None


def memory_bank_service_builder():
    """Builds VertexAiMemoryBankService for deployed container memory service."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Revelis, an AI Autonomous Event Intelligence & Boutique Celebration Concierge. "
        "You manage itineraries, destination weather forecasts, schedule logistics, visual concept collateral, "
        "bespoke culinary/cocktail menus, and short video previews (cinematic cocktail pours, rotating cake showcases) for luxury celebrations. "
        "You remember the user's stated preferences, guest profiles, anti-preferences (dislikes), "
        "dietary restrictions, and celebration themes across conversations using your Memory Bank. "
        "You have access to a sandboxed Python runtime environment to compute per-person expense splits, "
        "tax/tip calculations, deposit milestones, and budget allocations deterministically whenever mathematical or financial calculations are needed.\n\n"
        "MEMORY BANK & EVENT CONSTRAINTS:\n"
        "Always pay strict attention to and store/recall the following key event details:\n"
        "1. Guest of Honor / Bride's Name (e.g., Sarah, Jessica)\n"
        "2. Celebration Destination & Dates (e.g., Scottsdale, Cabo, Miami)\n"
        "3. Headcount / Party Size (e.g., 8 guests)\n"
        "4. Aesthetic Themes & Vibe (e.g., Desert Disco, Coastal Cowgirl, Minimalist Glam)\n"
        "5. Anti-Preferences & Dislikes (e.g., hated colors, prohibited activities, disliked spirits/flavors)\n"
        "6. Dietary Restrictions & Allergies for all guests (e.g., Gluten-Free, Peanut Allergy, Dairy-Free, Vegan)\n"
    ),
    workflow_description="Analyze the user request and return structured A2UI components whenever presenting event itineraries, custom menus, celebration cakes, video previews, or logistics.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows or Image. "
        "Never nest a Card inside a Card. "
        "Use ONLY these supported components: Card, Column, Row, Text, Divider, List, Icon, and Image. Do NOT use Table or Heading (unsupported). "
        "Render event itineraries as structured tables using Rows and Columns of Text components (using 'body' usageHint and bold column headers). "
        "Render custom menus and celebration cakes as Cards containing Text components and an Image component. "
        "When including an Image component for bespoke cakes, signature cocktails, or decor concepts, ALWAYS set its URL to the exact public Cloud Storage HTTPS URL (https://storage.googleapis.com/...) returned by the generate_concept_image tool, formatted like {\"Image\": {\"url\": {\"literalString\": \"https://storage.googleapis.com/...\"}}}. "
        "When generating video previews for items like cocktail pours or celebration cake showcases, ALWAYS call generate_video_preview and include its public Cloud Storage HTTPS URL in a Text component formatted like {\"Text\": {\"text\": {\"literalString\": \"📹 Video Preview: https://storage.googleapis.com/...\"}, \"usageHint\": \"body\"}}. "
        "Never point an Image at a bare filename, artifact path, or non-https URL. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in <a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        get_weather,
        get_destination_weather,
        get_current_time,
        get_itinerary,
        add_itinerary_item,
        get_menu_items,
        add_menu_item,
        validate_and_generate_event_logistics,
        generate_concept_image,
        generate_video_preview,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
