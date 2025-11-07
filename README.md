# Traveller Agent — Project Overview

This repository contains a small interactive travel-planning demo that combines a state-based workflow (LangGraph) with a conversational LLM interface (Google Generative AI via LangChain adapters). The app generates a short, budget-aware travel plan including hotel suggestions, must-visit places, and a simple cost estimate.

Key goals
- Demonstrate how to orchestrate multiple LLM-driven steps (analyze profile, suggest hotels, list places, estimate cost) using a state graph.
- Provide a simple Streamlit UI for interactive input and quick experimentation.
- Keep development friction low by providing a safe offline/mock mode when cloud credentials are not present.

Architecture and components
- `app.py` — The LangGraph workflow definition and node implementations. Also includes `initialize_llm()` and a `DummyLLM` fallback used during local development.
- `streamlit_app.py` — Streamlit-based user interface. It auto-detects credentials when available and runs the compiled graph to produce the travel plan.
- `requirements.txt` — Python dependencies required to run the project.

How it works (high level)
1. The Streamlit UI collects travel preferences (destination, area, duration, budget, interests).
2. The UI initializes the LLM client using `initialize_llm()` in `app.py`. If no credentials are found, the app falls back to `DummyLLM` (mock responses).
3. The LangGraph workflow runs a sequence of nodes:
	- `get_travel_input` (merges UI-provided inputs with defaults)
	- `analyze_travel_profile` (LLM analyzes preferences)
	- `suggest_hotels` (LLM recommends hotels)
	- `suggest_places` (LLM lists places to visit)
	- `cost_estimator` (LLM provides a simple cost breakdown)
	- `travel_summary` (aggregates the outputs)
4. The Streamlit UI displays the aggregated travel plan.

Running the project (quick)
1. (Optional) Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the Streamlit app:

```powershell
python -m streamlit run "d:/New folder/Traveller Agent/streamlit_app.py"
```

Credentials and mock mode
- The app looks for credentials in this order: `GOOGLE_API_KEY` env var, Streamlit `st.secrets`, then ADC via `GOOGLE_APPLICATION_CREDENTIALS`.
- If no credentials are available, the app uses `DummyLLM` and shows a clear mock-mode warning in the UI. Mock responses are intentionally labeled and suitable for UI testing and development.

Providing credentials (examples)
- Environment variable (PowerShell):

```powershell
$env:GOOGLE_API_KEY = "YOUR_API_KEY"
```

- Application Default Credentials (PowerShell):

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account.json"
```

- Streamlit secrets (`.streamlit/secrets.toml`):

```toml
GOOGLE_API_KEY = "YOUR_API_KEY"
```

Development tips
- The `DummyLLM` provides quick, deterministic placeholder text so you can iterate on the UI and workflow without incurring API usage or needing credentials.
- If you want deterministic tests, consider adding a small smoke-test script that runs the graph with the `DummyLLM` and asserts keys exist in the final state.

Future improvements

Here are practical next steps to make this project more robust, testable, and production-ready. They are ordered roughly from low to higher effort.

- Pin dependency versions in `requirements.txt` and optionally add a `constraints.txt` for reproducible installs.
- Add automated smoke tests that run the compiled graph in `DummyLLM` mode and assert the presence and shape of keys in the final state.
- Convert prompts and model outputs to structured JSON (or a simple schema) to make downstream parsing deterministic and safe. Consider using a lightweight schema validator (Pydantic) to validate responses.
- Improve prompt engineering and add a small response-parsing layer that extracts structured fields (hotel list, places list, cost breakdown).
- Add retry/backoff and basic rate-limit handling around LLM calls to improve resilience.
- Add caching for repeated requests (e.g., same destination/area) to reduce API usage during development and testing.
- Add logging and observability: structured logs for node inputs/outputs and a debug mode that records prompts and raw responses locally.
- Add unit tests and CI (GitHub Actions) that install deps in a matrix, run linting, and execute the smoke tests.
- Add a Dockerfile and simple deployment guide (Streamlit Cloud, Azure App Service, or a container registry) for easy hosting.
- Add user authentication and session management if you want personalized saved plans or rate-limited access.
- Consider replacing textual prompts with small functions that return structured dicts when possible, and centralize prompt templates in a single file for maintainability.

If you'd like, I can start on any one of these items (for example: pinning dependencies and adding a smoke-test script that runs the graph with `DummyLLM`). Tell me which one to prioritize and I'll implement it next.