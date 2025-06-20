from datetime import datetime

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext


def update_metadata(tool_context: ToolContext, field: str, value: str) -> dict:
    """
    Updates a single metadata field (e.g., 'vendor_name', 'buyer_name', etc.)
    in the session state for sale deed drafting, and logs the interaction.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Retrieve or initialize metadata
    metadata: dict[str, str] = tool_context.state.get("metadata", {}) or {}
    metadata[field] = value.strip()
    tool_context.state["metadata"] = metadata
    
    # Log the interaction
    history = tool_context.state.get("interaction_history", []) or []
    history.append({
        "action": "update_metadata",
        "field": field,
        "value": value,
        "timestamp": timestamp
    })
    tool_context.state["interaction_history"] = history
    
    return {
        "status": "success",
        "field": field,
        "value": value,
        "timestamp": timestamp
    }


def store_retrieved_clauses(tool_context: ToolContext, clauses: list[dict[str, str]]) -> dict:
    """
    Stores full clause texts retrieved by the Clause Retriever Agent.
    Each clause is a dict: {"type": <clause_name>, "text": <clause_text>}.
    Logs the operation for traceability.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save retrieved clauses list to session state
    tool_context.state["retrieved_clauses"] = [clause.copy() for clause in clauses]

    # Log interaction
    history = tool_context.state.get("interaction_history", []) or []
    history.append({
        "action": "store_retrieved_clauses",
        "clause_count": len(clauses),
        "timestamp": timestamp
    })
    tool_context.state["interaction_history"] = history

    return {
        "status": "success",
        "clause_count": len(clauses),
        "timestamp": timestamp
    }

clause_retriever = Agent(
    name="clause_retriever",
    model="gemini-2.0-flash",
    description="agent that retrieves relevant clauses for a legal document based on the user's input",
    instruction="""
You are the Clause Retriever Agent for drafting a Sale Deed.
Your role is to retrieve relevant clauses based on user input and metadata provided by the Root Orchestrator Agent.

       - Display the standard Sale Deed clauses:
     1. Parties  
     2. Property Description  
     3. Payment Terms  
     4. Advance/Installment  
     5. Transfer of Title & Possession  
     6. Indemnity & Encumbrance  
     7. Warranty/Covenant  
     8. Time-is-of-the-Essence  
     9. Right to Quiet Enjoyment  
     10. Reddendum/Tandem  
     11. Habendum  
     12. Dispute Resolution & Governing Law  
     13. Registration & Witnesses  
     14. Miscellaneous (Severability/Notices)
   - Ask: “Which clauses would you like to include?”
   - Log the prompt and answer to `state["interaction_history"]`.
   - Save selections to `state["clauses"]` (a list).

   when interacting with the user, if they give you a clause name, you should use the `update_metadata` tool to update the metadata in the session state. and if they give you a list of clauses, you should use the `store_retrieved_clauses` tool to store the retrieved clauses in the session state. 

""",
tools=[update_metadata, store_retrieved_clauses],

)