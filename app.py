from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
import re
import os

class DummyResponse:
    def __init__(self, content: str):
        self.content = content


class DummyLLM:
    """A lightweight offline LLM stub for development when credentials are missing.

    It provides an `invoke(prompt)` method that returns an object with a `.content`
    attribute so existing code (which expects `llm.invoke(prompt).content`) keeps working.
    """
    def invoke(self, prompt: str):
        # Keep responses concise and clearly marked as mock responses.
        summary = "[MOCK RESPONSE] No Google credentials found. This is a placeholder response.\n"
        # Try to produce minimal helpful output depending on prompt keywords
        if "Recommend 2 budget-friendly hotels" in prompt:
            summary += "Hotel A - ₹1200/night (approx)\nHotel B - ₹900/night (approx)"
        elif "Suggest 5 must-visit places" in prompt:
            summary += "1. Place One\n2. Place Two\n3. Place Three\n4. Place Four\n5. Place Five"
        elif "Estimate the total travel cost" in prompt:
            summary += "Hotel: ₹3000, Transport: ₹800, Food: ₹900, Misc: ₹300. Total: ₹5000 (within budget)"
        else:
            # Generic echo for other prompts
            snippet = prompt.strip().replace('\n', ' ')[:200]
            summary += f"Echo: {snippet}..."

        return DummyResponse(summary)


def initialize_llm(api_key=None, allow_fallback=True):
    """Initialize the ChatGoogleGenerativeAI model.

    Behavior:
    - If `api_key` is provided, use it to initialize the model.
    - If no `api_key`, attempt to initialize without it (which uses Application Default
      Credentials / ADC).
    - If initialization fails due to missing credentials and `allow_fallback` is True,
      return a `DummyLLM` so the app remains usable for development/testing.
    """
    # Prefer an explicit API key if provided
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")

    try:
        if api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=api_key,
                temperature=0.3,
            )
        else:
            # Try to initialize using ADC (no key passed)
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.3,
            )
    except Exception as e:
        # If credentials are missing, let callers get a friendly fallback during local dev.
        try:
            # Try to detect the Google credentials exception class if available
            from google.auth.exceptions import DefaultCredentialsError
        except Exception:
            DefaultCredentialsError = None

        if DefaultCredentialsError is not None and isinstance(e, DefaultCredentialsError):
            if allow_fallback:
                # Return mock LLM for offline development
                return DummyLLM()
            raise

        # If it's another error but fallback allowed, return DummyLLM to keep app usable.
        if allow_fallback:
            return DummyLLM()

        # Re-raise if fallback not permitted
        raise


# Initialize LLM with None - will be set later by the Streamlit app or another runner
llm = None

# ==== 1. User Travel Input ====
def get_travel_input(state):
    # Allow the caller (e.g., Streamlit UI) to provide travel input in the incoming
    # `state`. If values are provided, prefer them; otherwise fall back to sane
    # defaults so the graph can still run standalone.
    defaults = {
        "destination": "Hyderabad",
        "area": "HITEC city",
        "duration_days": 3,
        "budget": 7000,  # INR per person
        "travel_type": "budget",
        "interests": ["sightseeing", "local food"],
    }

    incoming = state.get("travel_input") or {}
    # Merge defaults with incoming values; incoming overrides defaults
    merged = defaults.copy()
    merged.update(incoming)

    state["travel_input"] = merged
    return state

# ==== 2. Analyze Preferences ====
def analyze_travel_profile(state):
    global llm
    if llm is None:
        raise ValueError("LLM not initialized. Please set Google API key first.")
        
    t = state["travel_input"]
    prompt = f"""
    You are a smart travel agent. Analyze the following user preferences:
    - Destination: {t['destination']} ({t['area']})
    - Duration: {t['duration_days']} days
    - Budget: ₹{t['budget']} total
    - Travel type: {t['travel_type']}
    - Interests: {", ".join(t['interests'])}

    Give a short summary and note any constraints or considerations.
    """
    state["travel_summary"] = llm.invoke(prompt).content
    return state

# ==== 3. Suggest Hotels ====
def suggest_hotels(state):
    global llm
    if llm is None:
        raise ValueError("LLM not initialized. Please set Google API key first.")
        
    t = state["travel_input"]
    prompt = f"""
    Recommend 2 budget-friendly hotels in or near {t['area']}, {t['destination']} 
    for {t['duration_days']} days stay under ₹{t['budget']} total.

    For each hotel, include:
    - Name
    - Approx. price per night
    - Total cost
    - Reason it's a good choice
    """
    state["hotel_options"] = llm.invoke(prompt).content
    return state

# ==== 4. Places to Visit ====
def suggest_places(state):
    global llm
    if llm is None:
        raise ValueError("LLM not initialized. Please set Google API key first.")
        
    t = state["travel_input"]
    prompt = f"""
    Suggest 5 must-visit places in or near {t['destination']} focusing on:
    - Interests: {", ".join(t['interests'])}
    - Budget constraints (travel type: {t['travel_type']})
    - Located within 10-15 km of {t['area']}

    Include place name and reason to visit.
    """
    state["places_to_visit"] = llm.invoke(prompt).content
    return state

# ==== 5. Cost Estimation ====
def cost_estimator(state):
    global llm
    if llm is None:
        raise ValueError("LLM not initialized. Please set Google API key first.")
        
    prompt = f"""
    Estimate the total travel cost for this 3-day trip to Hyderabad with the following:
    - Hotel: use details below
{state['hotel_options']}

    - Sightseeing: based on these places
{state['places_to_visit']}

    Break down cost for:
    - Hotel stay
    - Transport/local travel
    - Food
    - Entry tickets (if any)
    - Misc

    Give total cost and whether it's within ₹{state['travel_input']['budget']}.
    """
    state["cost_estimate"] = llm.invoke(prompt).content
    return state

# ==== 6. Final Travel Plan ====
def travel_summary(state):
    summary = f"""
    Travel Summary:
{state['travel_summary']}

    Hotel Options:
{state['hotel_options']}

    Places to Visit:
{state['places_to_visit']}

    Cost Estimate:
{state['cost_estimate']}
"""
    state["summary"] = summary
    return state

# ==== BUILD GRAPH ====
graph = StateGraph(dict)
graph.add_node("input", get_travel_input)
graph.add_node("analyze", analyze_travel_profile)
graph.add_node("hotels", suggest_hotels)
graph.add_node("places", suggest_places)
graph.add_node("cost", cost_estimator)
graph.add_node("summary", travel_summary)

graph.set_entry_point("input")
graph.add_edge("input", "analyze")
graph.add_edge("analyze", "hotels")
graph.add_edge("hotels", "places")
graph.add_edge("places", "cost")
graph.add_edge("cost", "summary")
graph.set_finish_point("summary")

# Compile the graph and create an app
app = graph.compile()

