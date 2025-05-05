import streamlit as st
import requests
import json
import os
from PIL import Image
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Creative AI Pipeline",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define API URL
API_URL = "http://localhost:8888/execution"

# Define CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4F8BF9;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #4F8BF9;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .highlight {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success {
        color: #28a745;
        font-weight: bold;
    }
    .error {
        color: #dc3545;
        font-weight: bold;
    }
    .info-box {
        background-color: #e6f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .memory-item {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #4F8BF9;
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.markdown('<h1 class="main-header">🚀 Creative AI Pipeline</h1>', unsafe_allow_html=True)
st.markdown("""
This application transforms simple text prompts into stunning 3D models through the power of AI.
""")

# Sidebar
st.sidebar.markdown('<h2 class="sub-header">About</h2>', unsafe_allow_html=True)
st.sidebar.markdown("""
This application creates a seamless pipeline that:

1. **Understands** user requests using a local LLM
2. **Expands** prompts creatively
3. **Generates** stunning visuals from text
4. **Transforms** 2D images into 3D models
5. **Remembers** creations across sessions
""")

# Function to send request to API
def send_request(prompt):
    payload = {
        "prompt": prompt,
        "attachments": ["string"]
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            st.error(f"Error: Server returned status code {response.status_code}")
        
        response.raise_for_status()
        
        # Handle the response
        try:
            # Check if the response text starts with a single quote and contains a JSON string
            if response.text.startswith("{'message': '") and response.text.endswith("'}"):
                # Extract the JSON string from the response
                json_str = response.text.split("'message': '", 1)[1].rsplit("'}", 1)[0]
                try:
                    # Parse the JSON string
                    message_json = json.loads(json_str)
                    
                    # Return the response with the parsed message
                    return {"response": {"message": message_json}}
                except json.JSONDecodeError:
                    pass
            
            # If the above approach doesn't work, try the standard JSON parsing
            try:
                # Parse the response as JSON
                response_json = response.json()
                
                # Check if the response has a 'message' field that contains a JSON string
                if "message" in response_json and isinstance(response_json["message"], str):
                    try:
                        # Try to parse the message as JSON
                        message_json = json.loads(response_json["message"])
                        
                        # Return the response with the parsed message
                        return {"response": {"message": message_json}}
                    except json.JSONDecodeError:
                        # If the message is not valid JSON, return it as is
                        pass
                
                # Return the response as is
                return response_json
            except json.JSONDecodeError:
                # Try to handle the raw response
                if response.text:
                    return {"response": {"message": f"Raw response: {response.text}"}}
                else:
                    return None
        except Exception as e:
            st.error(f"Error processing response: {str(e)}")
            return {"response": {"message": f"Error: {str(e)}"}}
    except requests.exceptions.RequestException as e:
        st.error(f"Error sending request: {e}")
        return None

# Function to load memory data
def load_memory():
    memory_file = "datastore/memory.json"
    if os.path.exists(memory_file):
        try:
            with open(memory_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# Function to format timestamp
def format_timestamp(timestamp_str):
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

# Main app
tab1, tab2 = st.tabs(["Create", "Memory"])

# Create tab
with tab1:
    st.markdown('<h2 class="sub-header">Create New</h2>', unsafe_allow_html=True)
    
    # Input form
    with st.form("prompt_form"):
        prompt = st.text_area("Enter your prompt:", 
                              placeholder="Example: Make me a glowing dragon standing on a cliff at sunset.",
                              height=100)
        submitted = st.form_submit_button("Generate")
    
    # Process form submission
    if submitted and prompt:
        with st.spinner("Processing your request... This may take a while."):
            # Send request to API
            result = send_request(prompt)
            
            if result and "response" in result and "message" in result["response"]:
                # Get the message from the response
                message = result["response"]["message"]
                
                # Check if the message is already a dictionary (parsed JSON)
                if isinstance(message, dict):
                    message_json = message
                else:
                    # Try to parse the message as JSON
                    try:
                        message_json = json.loads(message)
                    except json.JSONDecodeError:
                        message_json = None
                
                # Handle the message based on its type
                if message_json and message_json.get("status") == "success":
                    st.success("Successfully processed your prompt!")
                    
                    # Display the details
                    details = message_json.get("details", {})
                    
                    st.markdown('<div class="highlight">', unsafe_allow_html=True)
                    st.markdown("**Original Prompt:**")
                    st.write(details.get("prompt", ""))
                    st.markdown("**Expanded Prompt:**")
                    st.write(details.get("expanded_prompt", ""))
                    st.markdown("**Processing Time:**")
                    st.write(details.get("processing_time", ""))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Get image and model paths
                    image_path = details.get("image_path")
                    model_path = details.get("model_path")
                elif isinstance(message, str) and message.startswith("Raw response:"):
                    # Handle raw response
                    st.warning("Response is not in JSON format.")
                    
                    # Display the message
                    st.markdown('<div class="highlight">', unsafe_allow_html=True)
                    st.write(message)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Try to extract image and model paths from the message
                    lines = message.split('\n') if '\n' in message else []
                    image_path = None
                    model_path = None
                    
                    for line in lines:
                        if "Image saved to:" in line:
                            image_path = line.split(":", 1)[1].strip()
                        elif "3D model saved to:" in line:
                            model_path = line.split(":", 1)[1].strip()
                else:
                    # If the message is an error or unknown format, display it as is
                    st.error(f"Error or unknown format: {message}")
                    image_path = None
                    model_path = None
                
                # Display image if available
                if image_path and os.path.exists(image_path):
                    st.markdown("**Generated Image:**")
                    image = Image.open(image_path)
                    st.image(image, use_container_width=True)
                
                # Display 3D model info if available
                if model_path and os.path.exists(model_path):
                    st.markdown("**3D Model Generated:**")
                    st.markdown(f'<div class="info-box">3D model saved at: {model_path}</div>', unsafe_allow_html=True)
                    st.info("Note: To view the 3D model, you'll need a compatible viewer.")
            else:
                st.error("Unexpected response format or no response received.")

# Memory tab
with tab2:
    st.markdown('<h2 class="sub-header">Memory</h2>', unsafe_allow_html=True)
    
    if st.button("Refresh Memory"):
        st.rerun()
    
    # Load memory data
    memory_data = load_memory()
    
    if not memory_data:
        st.info("No memory data found. Create something first!")
    else:
        # Search box
        search_query = st.text_input("Search memory:", placeholder="Enter keywords to search...")
        
        # Display memory items
        for user_id, items in memory_data.items():
            st.markdown(f"**User ID:** {user_id}")
            
            # Filter items based on search query
            if search_query:
                filtered_items = []
                for item in items:
                    if (search_query.lower() in item.get("prompt", "").lower() or 
                        search_query.lower() in item.get("expanded_prompt", "").lower()):
                        filtered_items.append(item)
                items_to_display = filtered_items
            else:
                items_to_display = items
            
            if not items_to_display:
                st.info(f"No matching items found for user {user_id}.")
                continue
            
            # Sort items by timestamp (newest first)
            items_to_display.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Display items
            for item in items_to_display:
                with st.expander(f"{item.get('prompt', 'Unknown prompt')} ({format_timestamp(item.get('timestamp', ''))})"):
                    st.markdown('<div class="memory-item">', unsafe_allow_html=True)
                    
                    # Create columns for display
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Original Prompt:**")
                        st.write(item.get("prompt", ""))
                        st.markdown("**Expanded Prompt:**")
                        st.write(item.get("expanded_prompt", ""))
                        
                        # Display processing time if available
                        if "processing_time" in item:
                            st.markdown("**Processing Time:**")
                            st.write(f"{item['processing_time']:.2f} seconds")
                    
                    # Display image if available
                    image_path = item.get("image_path")
                    if image_path and os.path.exists(image_path):
                        with col2:
                            st.markdown("**Generated Image:**")
                            image = Image.open(image_path)
                            st.image(image, use_container_width=True)
                    
                    # Display 3D model info if available
                    model_path = item.get("model_path")
                    if model_path and os.path.exists(model_path):
                        st.markdown("**3D Model:**")
                        st.markdown(f'<div class="info-box">3D model saved at: {model_path}</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 Creative AI Pipeline")
