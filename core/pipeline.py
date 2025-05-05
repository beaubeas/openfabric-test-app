import base64
import logging
import os
import time
from typing import Dict, Any, Optional, Tuple, List
import uuid

from core.llm import LLM
from core.memory import Memory
from core.stub import Stub


class Pipeline:
    """
    Pipeline class that handles the end-to-end process from user prompt to 3D model generation.
    
    Attributes:
        llm (LLM): The LLM instance for prompt expansion
        memory (Memory): The Memory instance for storing results
        stub (Stub): The Stub instance for calling Openfabric apps
        text_to_image_app_id (str): The ID of the Text-to-Image app
        image_to_3d_app_id (str): The ID of the Image-to-3D app
        output_dir (str): Directory to store output files
    """
    
    def __init__(self, 
                 stub: Stub,
                 llm: Optional[LLM] = None,
                 memory: Optional[Memory] = None,
                 text_to_image_app_id: str = None,
                 image_to_3d_app_id: str = None,
                 output_dir: str = "output"):
        """
        Initialize the Pipeline instance.
        
        Args:
            stub (Stub): The Stub instance for calling Openfabric apps
            llm (Optional[LLM]): The LLM instance for prompt expansion
            memory (Optional[Memory]): The Memory instance for storing results
            text_to_image_app_id (str): The ID of the Text-to-Image app
            image_to_3d_app_id (str): The ID of the Image-to-3D app
            output_dir (str): Directory to store output files
        """
        self.llm = llm if llm is not None else LLM()
        self.memory = memory if memory is not None else Memory()
        self.stub = stub
        # Get app IDs from the stub's connections if not provided
        if text_to_image_app_id is None or image_to_3d_app_id is None:
            app_ids = list(stub._connections.keys())
            
            if len(app_ids) >= 2:
                self.text_to_image_app_id = app_ids[0]
                self.image_to_3d_app_id = app_ids[1]
                logging.info(f"Using app IDs from connections")
            else:
                # Fallback to default app IDs
                self.text_to_image_app_id = text_to_image_app_id
                self.image_to_3d_app_id = image_to_3d_app_id
                logging.info(f"Using fallback app IDs")
        else:
            self.text_to_image_app_id = text_to_image_app_id
            self.image_to_3d_app_id = image_to_3d_app_id
            logging.info(f"Using provided app IDs")
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def process(self, prompt: str, user_id: str = "super-user") -> Dict[str, Any]:
        """
        Process a user prompt through the entire pipeline.
        
        Args:
            prompt (str): The user's prompt
            user_id (str): Unique identifier for the user
            
        Returns:
            Dict[str, Any]: Dictionary containing the results
        """
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Step 1: Expand the prompt using LLM
        logging.info(f"[{request_id}] Expanding prompt: {prompt}")
        expanded_prompt = self.llm.expand_prompt(prompt)
        
        # Analyze the prompt
        prompt_analysis = self.llm.analyze_prompt(prompt)
        
        # Store in short-term memory
        self.memory.store_short_term(user_id, {
            "request_id": request_id,
            "prompt": prompt,
            "expanded_prompt": expanded_prompt,
            "analysis": prompt_analysis
        })
        
        # Step 2: Generate image from expanded prompt
        logging.info(f"[{request_id}] Generating image from prompt")
        image_data, image_path = self._generate_image(expanded_prompt, user_id, request_id)
        
        if image_data is None:
            error_msg = "Failed to generate image from prompt"
            logging.error(f"[{request_id}] {error_msg}")
            return {"error": error_msg, "request_id": request_id}
        
        # Update short-term memory
        self.memory.store_short_term(user_id, {
            "image_path": image_path
        })
        
        # Step 3: Generate 3D model from image
        logging.info(f"[{request_id}] Generating 3D model from image")
        model_data, model_path = self._generate_3d_model(image_data, user_id, request_id)
        
        if model_data is None:
            error_msg = "Failed to generate 3D model from image"
            logging.error(f"[{request_id}] {error_msg}")
            return {"error": error_msg, "request_id": request_id, "image_path": image_path}
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare result
        result = {
            "request_id": request_id,
            "prompt": prompt,
            "expanded_prompt": expanded_prompt,
            "image_path": image_path,
            "model_path": model_path,
            "processing_time": processing_time,
            "analysis": prompt_analysis
        }
        
        # Store in long-term memory
        self.memory.store_long_term(user_id, result)
        
        logging.info(f"[{request_id}] Pipeline completed in {processing_time:.2f} seconds")
        return result
    
    def _generate_image(self, prompt: str, user_id: str, request_id: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Generate an image from a prompt using the Text-to-Image app.
        
        Args:
            prompt (str): The prompt to generate an image from
            user_id (str): Unique identifier for the user
            request_id (str): Unique identifier for the request
            
        Returns:
            Tuple[Optional[bytes], Optional[str]]: Tuple containing the image data and path
        """
        try:
            # Prepare the input for the Text-to-Image app
            input_data = {"prompt": prompt}
            
            # Call the Text-to-Image app
            logging.info(f"[{request_id}] Calling Text-to-Image app")
            app_id = self.text_to_image_app_id
            if not app_id.endswith(".node3.openfabric.network"):
                app_id = app_id + ".node3.openfabric.network"
            
            result = self.stub.call(app_id, input_data, user_id)
            
            # Check if the result contains the image
            if not result or "result" not in result:
                logging.error(f"[{request_id}] Text-to-Image app returned invalid result: {result}")
                return None, None
            
            # Get the image data
            image_data = result.get("result")
            
            # Save the image to a file
            image_filename = f"{request_id}_image.png"
            image_path = os.path.join(self.output_dir, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            logging.info(f"[{request_id}] Image saved to {image_path}")
            return image_data, image_path
            
        except Exception as e:
            logging.error(f"[{request_id}] Error generating image: {e}")
            return None, None
    
    def _generate_3d_model(self, image_data: bytes, user_id: str, request_id: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Generate a 3D model from an image using the Image-to-3D app.
        
        Args:
            image_data (bytes): The image data to generate a 3D model from
            user_id (str): Unique identifier for the user
            request_id (str): Unique identifier for the request
            
        Returns:
            Tuple[Optional[bytes], Optional[str]]: Tuple containing the model data and path
        """
        try:
            # Encode the image as base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            # Prepare the input for the Image-to-3D app
            input_data = {"input_image": image_base64}
            
            # Call the Image-to-3D app
            logging.info(f"[{request_id}] Calling Image-to-3D app")
            app_id = self.image_to_3d_app_id
            if not app_id.endswith(".node3.openfabric.network"):
                app_id = app_id + ".node3.openfabric.network"
            
            result = self.stub.call(app_id, input_data, user_id)
            
            # Check if the result contains the 3D model
            if not result:
                logging.error(f"[{request_id}] Image-to-3D app returned invalid result: {result}")
                return None, None
            
            # Get the 3D model data (prefer generated_object over video_object)
            if "generated_object" in result and result["generated_object"]:
                model_data = result.get("generated_object")
                logging.info(f"[{request_id}] Using generated_object from Image-to-3D app")
            elif "video_object" in result and result["video_object"]:
                model_data = result.get("video_object")
                logging.info(f"[{request_id}] Using video_object from Image-to-3D app")
            else:
                logging.error(f"[{request_id}] Image-to-3D app result missing generated_object and video_object")
                return None, None
            
            # Save the 3D model to a file with appropriate extension
            if "generated_object" in result and result["generated_object"]:
                model_filename = f"{request_id}_model.glb"
            else:
                model_filename = f"{request_id}_model.mp4"  # Assuming video is MP4 format
            
            model_path = os.path.join(self.output_dir, model_filename)
            
            # Write the data to the file
            with open(model_path, "wb") as f:
                f.write(model_data)
            
            logging.info(f"[{request_id}] 3D model saved to {model_path}")
            return model_data, model_path
            
        except Exception as e:
            logging.error(f"[{request_id}] Error generating 3D model: {e}")
            return None, None
    
    def get_recent_creations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent creations for a user.
        
        Args:
            user_id (str): Unique identifier for the user
            limit (int): Maximum number of creations to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of recent creations
        """
        return self.memory.retrieve_long_term(user_id, limit)
    
    def search_creations(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for creations based on a query.
        
        Args:
            user_id (str): Unique identifier for the user
            query (str): Text to search for
            
        Returns:
            List[Dict[str, Any]]: List of matching creations
        """
        return self.memory.search_memory(user_id, query)
