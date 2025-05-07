import logging
from typing import Dict, Any

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. LLM functionality will be limited.")

class LLM:
    
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-6.7b-instruct", 
        device: str = "cpu"):

        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.generator = None
        
        # Initialize the model if transformers is available
        if TRANSFORMERS_AVAILABLE:
            try:
                logging.info(f"Loading model {model_name}...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                try:
                    # Try to load the model with device_map
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_name, 
                        device_map=device,
                        trust_remote_code=True
                    )
                except Exception as e:
                    if "device_map" in str(e) or "accelerate" in str(e):
                        # If the error is related to device_map or accelerate, try without it
                        logging.warning(f"Failed to load model with device_map, trying without: {e}")
                        self.model = AutoModelForCausalLM.from_pretrained(
                            model_name,
                            trust_remote_code=True
                        )
                    else:
                        # Re-raise the exception if it's not related to device_map
                        logging.error(f"Failed to load model due to non-device_map error: {e}")
                        raise
                try:
                    # Try to create the pipeline with device_map
                    self.generator = pipeline(
                        "text-generation", 
                        model=self.model, 
                        tokenizer=self.tokenizer,
                        device_map=device
                    )
                except Exception as e:
                    if "device_map" in str(e) or "accelerate" in str(e):
                        # If the error is related to device_map or accelerate, try without it
                        logging.warning(f"Failed to create pipeline with device_map, trying without: {e}")
                        self.generator = pipeline(
                            "text-generation", 
                            model=self.model, 
                            tokenizer=self.tokenizer
                        )
                    else:
                        # Re-raise the exception if it's not related to device_map
                        logging.error(f"Failed to create pipeline due to non-device_map error: {e}")
                        raise
                logging.info(f"Model {model_name} loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load model {model_name}: {e}")
                # Fallback to a simpler approach if model loading fails
                self.model = None
                self.tokenizer = None
                self.generator = None
    
    def expand_prompt(self, prompt: str, max_length: int = 500) -> str:
        if not TRANSFORMERS_AVAILABLE or self.generator is None:
            # Fallback if transformers is not available or model loading failed
            logging.warning("Using fallback prompt expansion due to missing model")
            return self._fallback_expand_prompt(prompt)
        
        try:
            # Create a system prompt to guide the model
            system_prompt = (
                "You are a creative assistant that expands user prompts into detailed, "
                "vivid descriptions for image generation. Add specific details about "
                "lighting, colors, mood, style, and composition. Make the description "
                "detailed but coherent."
            )
            
            # Combine system prompt and user prompt
            input_text = f"{system_prompt}\n\nUser prompt: {prompt}\n\nExpanded prompt:"
            
            # Generate expanded prompt
            result = self.generator(
                input_text,
                max_length=len(input_text) + max_length,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            
            # Extract the generated text
            expanded_text = result[0]['generated_text']
            
            # Remove the input text to get only the expansion
            expanded_prompt = expanded_text[len(input_text):].strip()
            
            logging.info(f"Expanded prompt: {expanded_prompt}")
            return expanded_prompt
        
        except Exception as e:
            logging.error(f"Error expanding prompt: {e}")
            return self._fallback_expand_prompt(prompt)
    
    def _fallback_expand_prompt(self, prompt: str) -> str:
        # Add some basic enhancements to the prompt
        expanded = f"{prompt}, with dramatic lighting, vibrant colors, detailed textures, 4K resolution, professional photography, trending on artstation"
        logging.info(f"Using fallback expansion: {expanded}")
        return expanded
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        if not TRANSFORMERS_AVAILABLE or self.generator is None:
            # Fallback if transformers is not available or model loading failed
            return {
                "subject": prompt.split()[0] if prompt.split() else "unknown",
                "style": "default",
                "mood": "neutral",
                "colors": ["default"],
                "setting": "unspecified"
            }
        
        try:
            # Create a system prompt for analysis
            system_prompt = (
                "You are an AI that analyzes image prompts. Extract the following elements "
                "from the prompt: subject, style, mood, colors, and setting. Return the "
                "analysis as a structured list."
            )
            
            # Combine system prompt and user prompt
            input_text = f"{system_prompt}\n\nPrompt to analyze: {prompt}\n\nAnalysis:"
            
            # Generate analysis
            result = self.generator(
                input_text,
                max_length=len(input_text) + 300,
                num_return_sequences=1,
                temperature=0.2,
                top_p=0.9,
                do_sample=True
            )
            
            # Extract the generated text
            analysis_text = result[0]['generated_text']
            
            # Remove the input text to get only the analysis
            analysis = analysis_text[len(input_text):].strip()
            
            # Parse the analysis (simple parsing, could be improved)
            parsed = {}
            for line in analysis.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed[key.strip().lower()] = value.strip()
            
            # Ensure all expected keys are present
            result = {
                "subject": parsed.get("subject", "unknown"),
                "style": parsed.get("style", "default"),
                "mood": parsed.get("mood", "neutral"),
                "colors": [c.strip() for c in parsed.get("colors", "default").split(',')],
                "setting": parsed.get("setting", "unspecified")
            }
            
            logging.info(f"Prompt analysis: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error analyzing prompt: {e}")
            return {
                "subject": prompt.split()[0] if prompt.split() else "unknown",
                "style": "default",
                "mood": "neutral",
                "colors": ["default"],
                "setting": "unspecified"
            }
