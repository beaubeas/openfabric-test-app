import streamlit as st
import requests
import json
import os
import base64
from PIL import Image
from datetime import datetime
import time
from typing import List, Dict, Any, Optional

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
    .tag {
        display: inline-block;
        background-color: #e9ecef;
        color: #495057;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
        font-size: 0.8rem;
    }
    .tag:hover {
        background-color: #dee2e6;
        cursor: pointer;
    }
    .category {
        display: inline-block;
        background-color: #cfe2ff;
        color: #0d6efd;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .category:hover {
        background-color: #b6d4fe;
        cursor: pointer;
    }
    .similarity-score {
        color: #6c757d;
        font-size: 0.8rem;
        margin-left: 0.5rem;
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .model-viewer-container {
        width: 100%;
        height: 400px;
        margin-bottom: 1rem;
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
6. **Tags & Categorizes** creations automatically
7. **Enables Similarity Search** for finding related content
8. **Visualizes 3D Models** directly in the browser
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
        try:
            # Check if the response text starts with a single quote and contains a JSON string
            if response.text.startswith("{'message': '") and response.text.endswith("'}"):
                json_str = response.text.split("'message': '", 1)[1].rsplit("'}", 1)[0]
                try:
                    message_json = json.loads(json_str)                    
                    return {"response": {"message": message_json}}
                except json.JSONDecodeError:
                    pass
            
            try:
                response_json = response.json()
                if "message" in response_json and isinstance(response_json["message"], str):
                    try:
                        message_json = json.loads(response_json["message"])
                        return {"response": {"message": message_json}}
                    except json.JSONDecodeError:
                        pass
                
                return response_json
            except json.JSONDecodeError:
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

def load_memory():
    memory_file = "datastore/memory.json"
    if os.path.exists(memory_file):
        try:
            with open(memory_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def extract_all_tags(memory_data, user_id):
    all_tags = set()
    if user_id in memory_data:
        for item in memory_data[user_id]:
            if "tags" in item and isinstance(item["tags"], list):
                all_tags.update(item["tags"])
    return sorted(list(all_tags))

def extract_all_categories(memory_data, user_id):
    all_categories = set()
    if user_id in memory_data:
        for item in memory_data[user_id]:
            if "primary_category" in item:
                all_categories.add(item["primary_category"])
            if "categories" in item and isinstance(item["categories"], list):
                all_categories.update(item["categories"])
    return sorted(list(all_categories))

def filter_by_tags(items, selected_tags):
    if not selected_tags:
        return items
    
    filtered_items = []
    for item in items:
        if "tags" in item and isinstance(item["tags"], list):
            if any(tag in item["tags"] for tag in selected_tags):
                filtered_items.append(item)
    
    return filtered_items

def filter_by_category(items, selected_category):
    if not selected_category or selected_category == "All":
        return items
    
    filtered_items = []
    for item in items:
        if item.get("primary_category") == selected_category:
            filtered_items.append(item)
            continue
        
        if "categories" in item and isinstance(item["categories"], list):
            if selected_category in item["categories"]:
                filtered_items.append(item)
    
    return filtered_items

def similarity_search(items, query):
    if not query:
        return items
    query_lower = query.lower()
    results = []
    
    for item in items:
        score = 0
        
        if "prompt" in item and query_lower in item["prompt"].lower():
            score += 0.8
        
        if "expanded_prompt" in item and query_lower in item["expanded_prompt"].lower():
            score += 0.6
        
        if "tags" in item and isinstance(item["tags"], list):
            for tag in item["tags"]:
                if query_lower in tag.lower():
                    score += 0.4
                    break
        
        if score > 0:
            item_copy = item.copy()
            item_copy["similarity_score"] = min(score, 1.0)  # Cap at 1.0
            results.append(item_copy)
    
    results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)    
    return results

# Function to format timestamp
def format_timestamp(timestamp_str):
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

# Function to display a 3D model
def display_3d_model(model_path):
    try:
        if os.path.exists(model_path) and model_path.lower().endswith(('.glb', '.gltf')):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                with open(model_path, "rb") as file:
                    model_bytes = file.read()
                    st.download_button(
                        label="Download 3D Model",
                        data=model_bytes,
                        file_name=os.path.basename(model_path),
                        mime="application/octet-stream",
                        key=f"download_button_{os.path.basename(model_path)}"
                    )
            
            with col2:
                st.markdown(f'<div class="info-box">Path: {model_path}</div>', unsafe_allow_html=True)
            
            with open(model_path, "rb") as file:
                model_bytes = file.read()
                model_base64 = base64.b64encode(model_bytes).decode("utf-8")
                model_data_url = f"data:application/octet-stream;base64,{model_base64}"
            
            html_code = f"""
            <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
            <model-viewer src="{model_data_url}"
                          alt="3D Model"
                          ar
                          auto-rotate
                          camera-controls
                          style="width: 100%; height: 500px;">
            </model-viewer>
            """
            
            st.components.v1.html(html_code, height=500)
            
            return True
        else:
            st.info(f"3D model file exists but is not in a supported format for in-browser viewing: {model_path}")
            st.markdown(f'<div class="info-box">3D model saved at: {model_path}</div>', unsafe_allow_html=True)
            return False
    except Exception as e:
        st.error(f"Error displaying 3D model: {str(e)}")
        st.markdown(f'<div class="info-box">3D model saved at: {model_path}</div>', unsafe_allow_html=True)
        return False

def display_memory_item(item, title=None):
    if title is None:
        title = f"{item.get('prompt', 'Unknown prompt')} ({format_timestamp(item.get('timestamp', ''))})"
    
    with st.expander(title):
        st.markdown('<div class="memory-item">', unsafe_allow_html=True)        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original Prompt:**")
            st.write(item.get("prompt", ""))
            st.markdown("**Expanded Prompt:**")
            st.write(item.get("expanded_prompt", ""))
            
            if "processing_time" in item:
                st.markdown("**Processing Time:**")
                st.write(f"{item['processing_time']:.2f} seconds")
            
            if "tags" in item and item["tags"]:
                st.markdown("**Tags:**")
                tags_html = ""
                for tag in item["tags"]:
                    tags_html += f'<span class="tag">{tag}</span>'
                st.markdown(tags_html, unsafe_allow_html=True)
            
            if "primary_category" in item:
                st.markdown("**Category:**")
                st.markdown(f'<span class="category">{item["primary_category"]}</span>', unsafe_allow_html=True)
        
        image_path = item.get("image_path")
        if image_path and os.path.exists(image_path):
            with col2:
                st.markdown("**Generated Image:**")
                image = Image.open(image_path)
                st.image(image, use_container_width=True)
        
        model_path = item.get("model_path")
        if model_path and os.path.exists(model_path):
            st.markdown("**3D Model:**")
            display_3d_model(model_path)
        
        st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Create", "Memory"])

with tab1:
    st.markdown('<h2 class="sub-header">Create New</h2>', unsafe_allow_html=True)
    
    with st.form("prompt_form"):
        prompt = st.text_area("Enter your prompt:", 
            placeholder="Example: Make me a glowing dragon standing on a cliff at sunset.",
            height=100)
        submitted = st.form_submit_button("Generate")
    
    if submitted and prompt:
        with st.spinner("Processing your request... This may take a while."):
            result = send_request(prompt)
            
            if result and "response" in result and "message" in result["response"]:
                message = result["response"]["message"]
                if isinstance(message, dict):
                    message_json = message
                else:
                    try:
                        message_json = json.loads(message)
                    except json.JSONDecodeError:
                        message_json = None
                if message_json and message_json.get("status") == "success":
                    st.success("Successfully processed your prompt!")
                    details = message_json.get("details", {})                    
                    st.markdown('<div class="highlight">', unsafe_allow_html=True)
                    st.markdown("**Original Prompt:**")
                    st.write(details.get("prompt", ""))
                    st.markdown("**Expanded Prompt:**")
                    st.write(details.get("expanded_prompt", ""))
                    st.markdown("**Processing Time:**")
                    st.write(details.get("processing_time", ""))
                    st.markdown('</div>', unsafe_allow_html=True)                    
                    image_path = details.get("image_path")
                    model_path = details.get("model_path")
                elif isinstance(message, str) and message.startswith("Raw response:"):
                    st.warning("Response is not in JSON format.")
                    st.markdown('<div class="highlight">', unsafe_allow_html=True)
                    st.write(message)
                    st.markdown('</div>', unsafe_allow_html=True)
                    lines = message.split('\n') if '\n' in message else []
                    image_path = None
                    model_path = None
                    
                    for line in lines:
                        if "Image saved to:" in line:
                            image_path = line.split(":", 1)[1].strip()
                        elif "3D model saved to:" in line:
                            model_path = line.split(":", 1)[1].strip()
                else:
                    st.error(f"Error or unknown format: {message}")
                    image_path = None
                    model_path = None
                if image_path and os.path.exists(image_path):
                    st.markdown("**Generated Image:**")
                    image = Image.open(image_path)
                    st.image(image, use_container_width=True)
                if model_path and os.path.exists(model_path):
                    st.markdown("**3D Model Generated. Plz check memory tab.**")
            else:
                st.error("Unexpected response format or no response received.")

with tab2:
    st.markdown('<h2 class="sub-header">Memory</h2>', unsafe_allow_html=True)    
    if st.button("Refresh Memory"):
        st.rerun()
    
    memory_data = load_memory()
    
    if not memory_data:
        st.info("No memory data found. Create something first!")
    else:
        memory_tabs = st.tabs(["All Creations", "Search", "Browse by Category", "Browse by Tag"])
        
        for user_id, items in memory_data.items():
            all_tags = extract_all_tags(memory_data, user_id)
            all_categories = extract_all_categories(memory_data, user_id)
            
            # All Creations tab
            with memory_tabs[0]:
                st.markdown(f"**User ID:** {user_id}")
                sorted_items = sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)
                for item in sorted_items:
                    display_memory_item(item)
            
            with memory_tabs[1]:
                st.markdown(f"**User ID:** {user_id}")
                st.markdown('<div class="filter-section">', unsafe_allow_html=True)
                search_query = st.text_input("Search by similarity:", 
                    placeholder="Enter a description of what you're looking for...",
                    key=f"similarity_search_{user_id}")
                
                if st.button("Search", key=f"search_button_{user_id}"):
                    if search_query:
                        search_results = similarity_search(items, search_query)
                        if search_results:
                            st.success(f"Found {len(search_results)} results")
                            for item in search_results:
                                similarity_score = item.get("similarity_score")
                                title = f"{item.get('prompt', 'Unknown prompt')} ({format_timestamp(item.get('timestamp', ''))})"
                                if similarity_score:
                                    title += f" - Similarity: {similarity_score:.2f}"
                                
                                display_memory_item(item, title=title)
                        else:
                            st.info("No matching items found.")
                    else:
                        st.warning("Please enter a search query.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Browse by Category tab
            with memory_tabs[2]:
                st.markdown(f"**User ID:** {user_id}")
                st.markdown('<div class="filter-section">', unsafe_allow_html=True)
                category_options = ["All"] + all_categories
                selected_category = st.selectbox("Select Category:", 
                    category_options,
                    key=f"category_select_{user_id}")
                
                # Filter items by category
                filtered_items = filter_by_category(items, selected_category)
                filtered_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                st.markdown(f"Showing {len(filtered_items)} items in category: **{selected_category}**")
                st.markdown('</div>', unsafe_allow_html=True)
                for item in filtered_items:
                    display_memory_item(item)
            
            # Browse by Tag tab
            with memory_tabs[3]:
                st.markdown(f"**User ID:** {user_id}")
                st.markdown('<div class="filter-section">', unsafe_allow_html=True)
                selected_tags = st.multiselect("Select Tags:", 
                    all_tags,
                    key=f"tag_select_{user_id}")
                
                # Filter items by tags
                filtered_items = filter_by_tags(items, selected_tags)
                filtered_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                st.markdown(f"Showing {len(filtered_items)} items with selected tags")
                st.markdown('</div>', unsafe_allow_html=True)
                for item in filtered_items:
                    display_memory_item(item)
