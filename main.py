import logging
import os
from typing import Dict, List, Optional

from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
from openfabric_pysdk.context import AppModel, State
from core.stub import Stub
from core.llm import LLM
from core.memory import Memory
from core.pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configurations for the app
configurations: Dict[str, ConfigClass] = dict()

# Global instances
llm_instance: Optional[LLM] = None
memory_instance: Optional[Memory] = None

# Create output directory
os.makedirs("output", exist_ok=True)

############################################################
# Config callback function
############################################################
def config(configuration: Dict[str, ConfigClass], state: State) -> None:
    """
    Stores user-specific configuration data.

    Args:
        configuration (Dict[str, ConfigClass]): A mapping of user IDs to configuration objects.
        state (State): The current state of the application (not used in this implementation).
    """
    for uid, conf in configuration.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf


############################################################
# Execution callback function
############################################################
def execute(model: AppModel) -> None:
    """
    Main execution entry point for handling a model pass.

    Args:
        model (AppModel): The model object containing request and response structures.
    """
    global llm_instance, memory_instance
    
    # Retrieve input
    request: InputClass = model.request
    
    # Check if prompt is provided
    if not request.prompt:
        response: OutputClass = model.response
        response.message = "Error: No prompt provided. Please provide a prompt to generate an image and 3D model."
        return
    
    # Retrieve user config
    user_id = 'super-user'
    user_config: ConfigClass = configurations.get(user_id, None)
    logging.info(f"Configurations: {configurations}")
    
    # Initialize the Stub with app IDs
    app_ids = user_config.app_ids if user_config else []
    if not app_ids:
        # Use default app IDs if not provided in config
        app_ids = [
            "f0997a01-d6d3-a5fe-53d8-561300318557.node3.openfabric.network",  # Text-to-Image
            "69543f29-4d41-4afc-7f29-3d51591f11eb.node3.openfabric.network"   # Image-to-3D
        ]
    
    stub = Stub(app_ids)
    
    # Initialize LLM and Memory if not already initialized
    if llm_instance is None:
        llm_instance = LLM()
    
    if memory_instance is None:
        memory_instance = Memory()
    
    # Create Pipeline instance
    pipeline = Pipeline(
        stub=stub,
        llm=llm_instance,
        memory=memory_instance
    )
    
    try:
        # Process the prompt through the pipeline
        logging.info(f"Processing prompt: {request.prompt}")
        result = pipeline.process(request.prompt, user_id)
        
        # Check for errors
        if "error" in result:
            response: OutputClass = model.response
            response.message = f"Error: {result['error']}"
            return
        
        # Prepare success response as a JSON object
        import json
        response_message = {
            "status": "success",
            "message": "Successfully processed your prompt!",
            "details": {
                "prompt": result["prompt"],
                "expanded_prompt": result["expanded_prompt"],
                "image_path": result["image_path"],
                "model_path": result["model_path"],
                "processing_time": f"{result['processing_time']:.2f} seconds"
            }
        }
        
        # Prepare response
        response: OutputClass = model.response
        response.message = json.dumps(response_message)
        
    except Exception as e:
        logging.error(f"Error processing prompt: {e}")
        response: OutputClass = model.response
        response.message = f"Error: An unexpected error occurred while processing your prompt: {str(e)}"
