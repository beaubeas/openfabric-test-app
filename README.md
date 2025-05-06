# 🚀 Creative AI Pipeline

An intelligent end-to-end pipeline that transforms simple text prompts into stunning 3D models through the power of AI.

## 🌟 Overview

This application creates a seamless pipeline that:

1. **Understands** user requests using a local LLM (DeepSeek or Llama)
2. **Expands** prompts creatively to enhance the generation process
3. **Generates** stunning visuals from text using Openfabric's Text-to-Image app
4. **Transforms** 2D images into interactive 3D models using Openfabric's Image-to-3D app
5. **Remembers** creations across sessions with a robust memory system
6. **Tags & Categorizes** creations automatically for better organization
7. **Enables Similarity Search** for finding related content using vector embeddings
8. **Visualizes** results through an intuitive Streamlit web interface

## 📋 Requirements

- Python 3.11+
- Poetry (for dependency management)
- Transformers library (for local LLM)
- Openfabric SDK
- Streamlit (for the web interface)

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd openfabric-test-app
   ```

2. Create Environment & Install dependencies using Poetry:
   ```bash
   poetry env activate
   poetry install --no-root
   ```

3. Configure the app IDs in `config/properties.json` (optional, default values are provided):
   ```json
   {
     "app_ids": [
       "f0997a01-d6d3-a5fe-53d8-561300318557.node3.openfabric.network",
       "69543f29-4d41-4afc-7f29-3d51591f11eb.node3.openfabric.network"
     ]
   }
   ```

## 🚀 Running the Application

### Local Execution

The application consists of two components that need to be run separately:

#### Backend Server

Run the OpenFabric backend server:

```bash
cd openfabirc-test-app
poetry run python ignite.py
```

This will start the server on port 8888, which handles the image generation and 3D model creation.

#### Streamlit Frontend

In a separate terminal, run the Streamlit web interface:

```bash
cd openfabirc-test-app
poetry run streamlit run app.py
```

This will start the Streamlit web application, which provides a user-friendly interface for interacting with the backend server. Streamlit will automatically open a browser window with the application (typically at http://localhost:8501).

### Docker Execution

Build and run the Docker container:

```bash
docker build -t creative-ai-pipeline .
docker run -p 8888:8888 -p 8501:8501 creative-ai-pipeline
```

This will start both the backend server (available at http://localhost:8888) and the Streamlit frontend (available at http://localhost:8501) in a single container.

## 🌐 Using the Web Interface

The Streamlit web interface provides an intuitive way to interact with the application:

1. Enter your prompt in the text area (e.g., "Make me a glowing dragon standing on a cliff at sunset").
2. Click the "Generate" button.
3. Wait for the processing to complete (this may take a while depending on the complexity of the prompt).
4. View the results, including:
   - The original prompt
   - The expanded prompt
   - The generated image
   - The path to the 3D model file
   - Processing time

The interface also includes a "Memory" tab where you can view and search through your past creations.

## 🌐 Using the API

If you prefer to use the API directly, you can access the Swagger UI at:

```
http://localhost:8888/swagger-ui/#/App/post_execution
```

### Example Request

```json
{
  "prompt": "Make me a glowing dragon standing on a cliff at sunset.",
  "attachments": ["string"]
}
```

### Example Response

```json
{
  "message": "{
    \"status\": \"success\",
    \"message\": \"Successfully processed your prompt!\",
    \"details\": {
      \"prompt\": \"Make me a glowing dragon standing on a cliff at sunset.\",
      \"expanded_prompt\": \"Make me a glowing dragon standing on a cliff at sunset., with dramatic lighting, vibrant colors, detailed textures, 4K resolution, professional photography, trending on artstation\",
      \"image_path\": \"output/12345678-1234-5678-1234-567812345678_image.png\",
      \"model_path\": \"output/12345678-1234-5678-1234-567812345678_model.glb\",
      \"processing_time\": \"15.23 seconds\"
    }
  }"
}
```

## 🧠 Memory System

The application features a sophisticated memory system that operates on two levels:

### Short-Term Memory (Session Context)

- Maintains context during a single interaction
- Stores the current prompt, expanded prompt, and generated outputs
- Enables coherent multi-step interactions

### Long-Term Memory (Persistent Storage)

- Stores all creations across sessions in a JSON file
- Includes original prompts, expanded prompts, file paths, and metadata
- Enables searching and retrieval of past creations

### Memory Implementation

The memory system is implemented in `core/memory.py` and provides the following functionality:

- `store_short_term`: Store data in short-term memory
- `retrieve_short_term`: Retrieve data from short-term memory
- `store_long_term`: Store data in long-term memory (persistent)
- `retrieve_long_term`: Retrieve data from long-term memory
- `search_memory`: Search for specific creations based on text queries
- `search_by_tags`: Search for creations based on tags
- `search_by_category`: Search for creations based on category
- `get_all_tags`: Get all unique tags used by a user
- `get_all_categories`: Get all unique categories used by a user
- `update_tags`: Update the tags for a creation

Example of searching memory:

```python
from core.memory import Memory

memory = Memory()
results = memory.search_memory("super-user", "dragon")
```

### Vector Database for Similarity Search

The application uses ChromaDB for vector-based similarity search, implemented in `core/vector_db.py`:

- Stores embeddings of prompts and expanded prompts
- Enables semantic search beyond simple keyword matching
- Provides fast and efficient similarity-based retrieval
- Supports filtering by tags and metadata

Example of similarity search:

```python
from core.vector_db import VectorDB

vector_db = VectorDB()
results = vector_db.search_by_text("a majestic dragon with fire", n_results=5)
```

### Automatic Tagging and Categorization

The application includes an automatic tagging and categorization system, implemented in `core/tagger.py`:

- Analyzes prompts and expanded prompts to extract relevant tags
- Categorizes creations into predefined categories (landscape, character, animal, etc.)
- Identifies styles, colors, and moods present in the descriptions
- Provides a structured way to organize and browse creations

Example of tagging:

```python
from core.tagger import Tagger

tagger = Tagger()
analysis = tagger.analyze("A red dragon breathing fire in a medieval castle")
# Returns tags, categories, primary_category, styles, colors, and moods
```

### Enhanced Web Interface

The Streamlit web interface has been enhanced with new features:

- **Tabbed Memory Interface**: Browse creations by different views (All, Search, Category, Tag)
- **Similarity Search**: Find creations similar to a text description
- **Category Filtering**: Browse creations by category
- **Tag Filtering**: Browse creations by tags
- **Visual Tags and Categories**: Easily identify and filter by tags and categories
- **Interactive 3D Model Viewer**: View and interact with 3D models directly in the browser

## 🧩 Architecture

The application is structured into several core components:

### 1. LLM Module (`core/llm.py`)

Handles interaction with local language models to:
- Expand user prompts with creative details
- Analyze prompts to extract key elements
- Gracefully handle missing dependencies like 'accelerate'

### 2. Memory Module (`core/memory.py`)

Manages both short-term and long-term memory to:
- Store session context
- Persist creations across sessions
- Enable searching and retrieval

### 3. Pipeline Module (`core/pipeline.py`)

Orchestrates the end-to-end process:
- Expands prompts using the LLM
- Calls the Text-to-Image Openfabric app
- Calls the Image-to-3D Openfabric app
- Stores results in memory
- Dynamically handles different app IDs and response formats

### 4. Stub Module (`core/stub.py`)

Handles communication with Openfabric apps:
- Initializes connections to remote apps
- Fetches manifests and schemas
- Executes calls to apps
- Handles resource resolution errors gracefully

### 5. Main Application (`main.py`)

Serves as the entry point for the backend and:
- Handles API requests
- Initializes components
- Processes user prompts through the pipeline
- Returns responses in JSON format

### 6. Streamlit Interface (`app.py`)

Provides a user-friendly web interface:
- Sends requests to the backend
- Displays results including images and 3D model information
- Provides access to the memory system
- Handles various response formats and errors gracefully

## 🔍 Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - Ensure all required packages are installed with `poetry install`
   - If you encounter issues with the 'accelerate' package, the application will now fall back to loading models without device_map

2. **Model Loading Failures**
   - The application now handles model loading errors gracefully
   - If the LLM fails to load, a fallback prompt expansion mechanism is used

3. **API Connection Issues**
   - Verify Openfabric app IDs are correct
   - Check network connectivity to Openfabric services
   - The application now handles connection errors and resource resolution errors gracefully

4. **JSON Parsing Errors**
   - The application now handles various response formats, including nested JSON and Python dictionary representations
   - If you still encounter JSON parsing errors, check the raw response in the logs

5. **Streamlit Errors**
   - If you encounter `AttributeError: module 'streamlit' has no attribute 'experimental_rerun'`, update to the latest version of Streamlit
   - The application now uses `st.rerun()` instead of the deprecated `st.experimental_rerun()`

## 🔮 Future Enhancements

Potential improvements for future versions:

1. **Enhanced User Interface**
   - Implement drag-and-drop functionality for uploading reference images
   - Add animation controls for 3D models

2. **Voice Interaction**
   - Implement voice-to-text for natural interaction
   - Add text-to-speech for system responses

3. **Enhanced LLM Integration**
   - Support for more local LLM options
   - Fine-tuning capabilities for specific domains

4. **Deployment Improvements**
   - Add Kubernetes deployment configuration
   - Implement CI/CD pipeline for automated testing and deployment

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
