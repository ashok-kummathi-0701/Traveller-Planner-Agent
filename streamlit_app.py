import streamlit as st
import os
import asyncio
from app import app, initialize_llm

async def run_travel_plan(input_state):
    return await app.ainvoke(input_state)

def main():
    st.title("Travel Planner Assistant")
    st.write("Plan your perfect trip with our AI-powered travel assistant!")

    # API Key Management
    api_key = st.sidebar.text_input("Enter your Google API Key", type="password")
    if not api_key:
        st.warning("Please enter your Google API key in the sidebar to continue.")
        st.stop()
    
    try:
        # Initialize the LLM with the provided API key
        global llm
        import app
        app.llm = initialize_llm(api_key)
    except Exception as e:
        st.error(f"Error initializing the AI model: {str(e)}")
        st.stop()

    # Initialize session state if needed
    if "travel_plan" not in st.session_state:
        st.session_state.travel_plan = None

    # Create input form
    with st.form("travel_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input("Destination")
            area = st.text_input("Specific Area")
            duration = st.number_input("Duration (days)", min_value=1, max_value=30, value=3)
        
        with col2:
            budget = st.number_input("Budget (INR per person)", min_value=1000, value=7000)
            travel_type = st.selectbox("Travel Type", ["budget", "luxury", "mid-range"])
            interests = st.multiselect(
                "Interests",
                ["sightseeing", "local food", "shopping", "culture", "nature", "adventure"],
                default=["sightseeing", "local food"]
            )

        submit_button = st.form_submit_button("Plan My Trip")

        if submit_button:
            # Prepare input state
            input_state = {
                "travel_input": {
                    "destination": destination,
                    "area": area,
                    "duration_days": duration,
                    "budget": budget,
                    "travel_type": travel_type,
                    "interests": interests
                }
            }

            # Run the travel planning graph
            with st.spinner("Planning your perfect trip..."):
                try:
                    result = asyncio.run(run_travel_plan(input_state))
                    st.session_state.travel_plan = result["summary"]
                except Exception as e:
                    st.error(f"Error generating travel plan: {str(e)}")
                    st.stop()

    # Display results
    if st.session_state.travel_plan:
        st.markdown("## Your Travel Plan")
        st.markdown(st.session_state.travel_plan)

if __name__ == "__main__":
    main()