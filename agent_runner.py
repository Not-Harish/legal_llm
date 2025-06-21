import asyncio
import json
import ast
import re
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from root_agent.agent import root_agent
from utils import add_user_query_to_history, call_agent_async

# Constants
APP_NAME = "Customer Support"
USER_ID = "aiwithbrandon"

# In-memory session service and initial state
session_service = InMemorySessionService()
initial_state = {
    "metadata": {"name": "joshua"},
    "clauses": [],
    "retrieved_clauses": [],
    "draft": [],
    "interaction_history": []
}

# Session and runner setup
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    state=initial_state
)
SESSION_ID = session.id

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# --- Formatter: Recursively flatten nested JSON/dict into readable string ---
def flatten_legal_json(doc):
    lines = []

    def recurse(obj, indent=0):
        prefix = "  " * indent
        if isinstance(obj, dict):
            for k, v in obj.items():
                lines.append(f"{prefix}{k}:")
                recurse(v, indent + 1)
        elif isinstance(obj, list):
            for item in obj:
                recurse(item, indent + 1)
        else:
            lines.append(f"{prefix}{obj}")

    recurse(doc)
    return "\n".join(lines)

def extract_all_values_as_messages(result) -> list[str]:
    import json
    import ast
    import re

    messages = []

    if result is None:
        return ["⚠️ No response from agent."]

    result = str(result).strip()

    # Remove markdown code wrapper if exists
    if result.startswith("```"):
        result = re.sub(r"^```(?:json)?\n?", "", result)
        result = re.sub(r"\n?```$", "", result)

    # Decode unicode escape
    try:
        result = bytes(result, "utf-8").decode("unicode_escape")
    except Exception:
        pass

    # Try JSON or Python-style dict
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(result)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    if isinstance(v, str):
                        messages.append(v.strip())
                    else:
                        messages.append(flatten_legal_json(v))
                return messages
        except Exception:
            continue

    # Fallback: single message
    return [result.strip()]

# --- Universal output processor ---
def force_flatten_output(result) -> str:
    import json
    import ast
    import re

    if result is None:
        return "⚠️ No response from agent."

    # Ensure it's a string
    result = str(result).strip()

    # Step 0: Remove Markdown-style code block (```json ... ```)
    if result.startswith("```"):
        result = re.sub(r"^```(?:json)?\n?", "", result)
        result = re.sub(r"\n?```$", "", result)

    # Step 1: Try parsing as actual JSON
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict):
            if "response" in parsed:
                return str(parsed["response"])
            return flatten_legal_json(parsed)
    except Exception:
        pass

    # Step 2: Try parsing as Python literal (dict with single quotes)
    try:
        parsed = ast.literal_eval(result)
        if isinstance(parsed, dict):
            if "response" in parsed:
                return str(parsed["response"])
            return flatten_legal_json(parsed)
    except Exception:
        pass

    # Step 3: Decode escaped newlines, tabs, unicode (e.g., \\n → \n)
    try:
        result = bytes(result, "utf-8").decode("unicode_escape")
    except Exception:
        pass

    # Step 4: Strip off top-level key like 'sale_deed_draft:'
    if result.lower().startswith("sale_deed_draft:"):
        result = result.split(":", 1)[1].strip()

    # Step 5: Final polish - spacing, punctuation, newlines
    result = result.replace("\\n", "\n").replace("\\t", "\t")
    result = re.sub(r'\\+', '', result)                         # remove backslashes
    result = re.sub(r'\s{2,}', ' ', result)                     # collapse multiple spaces
    result = re.sub(r'(?<=[.,])(?=[^\s])', ' ', result)         # fix punctuation spacing
    result = re.sub(r'\n{3,}', '\n\n', result)                  # reduce excess newlines

    return result.strip()




# --- Main callable function ---
def run_agent_for_input(user_input: str) -> list[str]:
    import json, ast, re

    async def async_task():
        add_user_query_to_history(session_service, APP_NAME, USER_ID, SESSION_ID, user_input)
        response = await call_agent_async(runner, USER_ID, SESSION_ID, user_input)
        return response

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(async_task())

    if result is None:
        return ["⚠️ No response from the agent."]

    result = str(result).strip()

    # Remove ```json or ``` if present
    if result.startswith("```"):
        result = re.sub(r"^```(?:json)?\n?", "", result)
        result = re.sub(r"\n?```$", "", result)

    # Try JSON or dict
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(result)
            if isinstance(parsed, dict):
                return [str(v).strip() if isinstance(v, str) else flatten_legal_json(v) for v in parsed.values()]
        except Exception:
            continue

    # Fallback to just the raw string
    return [result.strip()]


