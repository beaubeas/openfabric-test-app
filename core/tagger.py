import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple

class Tagger:
    """
    Tagger class that handles automatic tagging and categorization of creations.
    
    This class analyzes prompts and expanded prompts to extract relevant tags
    and categorize the creations based on their content.
    """
    
    # Predefined categories with associated keywords
    CATEGORIES = {
        "landscape": ["landscape", "mountain", "forest", "beach", "ocean", "sea", "lake", "river", "waterfall", 
                     "sunset", "sunrise", "sky", "clouds", "nature", "outdoor", "scenery", "vista", "panorama"],
        "character": ["character", "person", "man", "woman", "boy", "girl", "hero", "villain", "warrior", 
                     "wizard", "knight", "princess", "king", "queen", "figure", "human", "face", "portrait"],
        "animal": ["animal", "dog", "cat", "bird", "fish", "lion", "tiger", "bear", "wolf", "fox", "horse", 
                  "elephant", "monkey", "pet", "creature", "wildlife"],
        "fantasy": ["fantasy", "dragon", "unicorn", "magic", "magical", "mythical", "myth", "legend", 
                   "fairy", "elf", "dwarf", "orc", "goblin", "wizard", "sorcerer", "spell", "enchanted"],
        "sci-fi": ["sci-fi", "science fiction", "futuristic", "space", "spaceship", "robot", "android", 
                  "cyborg", "alien", "planet", "star", "galaxy", "cosmic", "future", "technology", "tech"],
        "abstract": ["abstract", "geometric", "pattern", "shapes", "colorful", "vibrant", "surreal", 
                    "psychedelic", "non-representational", "expressionist", "minimalist"],
        "architecture": ["architecture", "building", "house", "castle", "palace", "temple", "church", 
                        "cathedral", "skyscraper", "tower", "bridge", "structure", "city", "urban"],
        "vehicle": ["vehicle", "car", "truck", "motorcycle", "bike", "bicycle", "boat", "ship", 
                   "aircraft", "plane", "spaceship", "rocket", "submarine", "train"],
        "object": ["object", "furniture", "chair", "table", "weapon", "sword", "gun", "artifact", 
                  "tool", "instrument", "device", "gadget", "machine", "mechanism"],
        "food": ["food", "fruit", "vegetable", "meat", "dessert", "cake", "cookie", "pie", 
                "meal", "dish", "cuisine", "drink", "beverage"]
    }
    
    # Style keywords
    STYLES = [
        "realistic", "photorealistic", "cartoon", "anime", "manga", "pixel art", "8-bit", "16-bit",
        "3D", "2D", "watercolor", "oil painting", "sketch", "drawing", "digital art", "concept art",
        "illustration", "minimalist", "abstract", "surreal", "impressionist", "expressionist",
        "cyberpunk", "steampunk", "fantasy", "sci-fi", "horror", "gothic", "vintage", "retro",
        "modern", "futuristic", "medieval", "ancient", "victorian", "art deco", "art nouveau"
    ]
    
    # Color keywords
    COLORS = [
        "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "black", "white",
        "gray", "grey", "gold", "silver", "bronze", "copper", "turquoise", "teal", "cyan", "magenta",
        "violet", "indigo", "maroon", "navy", "olive", "lime", "aqua", "azure", "beige", "coral",
        "crimson", "fuchsia", "lavender", "khaki", "ivory", "amber", "emerald", "ruby", "sapphire"
    ]
    
    # Mood keywords
    MOODS = [
        "happy", "sad", "angry", "peaceful", "calm", "serene", "chaotic", "mysterious", "magical",
        "dark", "light", "bright", "gloomy", "melancholic", "nostalgic", "romantic", "dramatic",
        "epic", "heroic", "whimsical", "playful", "serious", "intense", "relaxed", "energetic",
        "dynamic", "static", "ethereal", "dreamy", "nightmarish", "surreal", "realistic", "abstract"
    ]
    
    def __init__(self):
        """
        Initialize the Tagger instance.
        """
        # Compile regex patterns for faster matching
        self._compile_patterns()
        logging.info("Tagger initialized")
    
    def _compile_patterns(self):
        """
        Compile regex patterns for keyword matching.
        """
        # Compile category patterns
        self.category_patterns = {}
        for category, keywords in self.CATEGORIES.items():
            patterns = []
            for keyword in keywords:
                # Create pattern that matches the keyword as a whole word
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                patterns.append(pattern)
            self.category_patterns[category] = patterns
        
        # Compile style patterns
        self.style_patterns = []
        for style in self.STYLES:
            pattern = re.compile(r'\b' + re.escape(style) + r'\b', re.IGNORECASE)
            self.style_patterns.append((style, pattern))
        
        # Compile color patterns
        self.color_patterns = []
        for color in self.COLORS:
            pattern = re.compile(r'\b' + re.escape(color) + r'\b', re.IGNORECASE)
            self.color_patterns.append((color, pattern))
        
        # Compile mood patterns
        self.mood_patterns = []
        for mood in self.MOODS:
            pattern = re.compile(r'\b' + re.escape(mood) + r'\b', re.IGNORECASE)
            self.mood_patterns.append((mood, pattern))
    
    def analyze(self, prompt: str, expanded_prompt: str = None, analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a prompt and expanded prompt to extract tags and categories.
        
        Args:
            prompt (str): The original prompt
            expanded_prompt (str, optional): The expanded prompt
            analysis (Dict[str, Any], optional): Existing analysis from LLM
            
        Returns:
            Dict[str, Any]: Dictionary containing tags, categories, and other metadata
        """
        # Combine prompts for analysis
        text_to_analyze = prompt
        if expanded_prompt:
            text_to_analyze = f"{prompt} {expanded_prompt}"
        
        # Extract categories
        categories = self._extract_categories(text_to_analyze)
        
        # Extract styles
        styles = self._extract_styles(text_to_analyze)
        
        # Extract colors
        colors = self._extract_colors(text_to_analyze)
        
        # Extract moods
        moods = self._extract_moods(text_to_analyze)
        
        # Generate tags
        tags = self._generate_tags(categories, styles, colors, moods, analysis)
        
        # Determine primary category
        primary_category = self._determine_primary_category(categories)
        
        # Prepare result
        result = {
            "tags": tags,
            "categories": list(categories),
            "primary_category": primary_category,
            "styles": list(styles),
            "colors": list(colors),
            "moods": list(moods)
        }
        
        logging.info(f"Analysis result: {result}")
        return result
    
    def _extract_categories(self, text: str) -> Set[str]:
        """
        Extract categories from text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Set[str]: Set of categories
        """
        categories = set()
        
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    categories.add(category)
                    break
        
        return categories
    
    def _extract_styles(self, text: str) -> Set[str]:
        """
        Extract styles from text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Set[str]: Set of styles
        """
        styles = set()
        
        for style, pattern in self.style_patterns:
            if pattern.search(text):
                styles.add(style)
        
        return styles
    
    def _extract_colors(self, text: str) -> Set[str]:
        """
        Extract colors from text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Set[str]: Set of colors
        """
        colors = set()
        
        for color, pattern in self.color_patterns:
            if pattern.search(text):
                colors.add(color)
        
        return colors
    
    def _extract_moods(self, text: str) -> Set[str]:
        """
        Extract moods from text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Set[str]: Set of moods
        """
        moods = set()
        
        for mood, pattern in self.mood_patterns:
            if pattern.search(text):
                moods.add(mood)
        
        return moods
    
    def _generate_tags(self, 
                      categories: Set[str], 
                      styles: Set[str], 
                      colors: Set[str], 
                      moods: Set[str],
                      analysis: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Generate tags from extracted categories, styles, colors, and moods.
        
        Args:
            categories (Set[str]): Set of categories
            styles (Set[str]): Set of styles
            colors (Set[str]): Set of colors
            moods (Set[str]): Set of moods
            analysis (Optional[Dict[str, Any]]): Existing analysis from LLM
            
        Returns:
            List[str]: List of tags
        """
        tags = set()
        
        # Add categories as tags
        tags.update(categories)
        
        # Add styles as tags
        tags.update(styles)
        
        # Add colors as tags (limit to 3 most important)
        tags.update(list(colors)[:3])
        
        # Add moods as tags (limit to 2 most important)
        tags.update(list(moods)[:2])
        
        # Add subject from analysis if available
        if analysis and "subject" in analysis and analysis["subject"] != "unknown":
            tags.add(analysis["subject"])
        
        # Add setting from analysis if available
        if analysis and "setting" in analysis and analysis["setting"] != "unspecified":
            tags.add(analysis["setting"])
        
        return sorted(list(tags))
    
    def _determine_primary_category(self, categories: Set[str]) -> str:
        """
        Determine the primary category from a set of categories.
        
        Args:
            categories (Set[str]): Set of categories
            
        Returns:
            str: Primary category
        """
        if not categories:
            return "uncategorized"
        
        # Priority order for categories
        priority_order = [
            "character", "animal", "fantasy", "sci-fi", "landscape", 
            "architecture", "vehicle", "object", "food", "abstract"
        ]
        
        # Find the highest priority category
        for category in priority_order:
            if category in categories:
                return category
        
        # If no priority category is found, return the first one
        return next(iter(categories))
    
    def suggest_tags(self, prompt: str, n: int = 5) -> List[str]:
        """
        Suggest tags for a prompt.
        
        Args:
            prompt (str): The prompt to suggest tags for
            n (int): Maximum number of tags to suggest
            
        Returns:
            List[str]: List of suggested tags
        """
        # Analyze the prompt
        analysis = self.analyze(prompt)
        
        # Get the tags
        tags = analysis["tags"]
        
        # Limit to n tags
        return tags[:n]
    
    def categorize(self, prompt: str) -> str:
        """
        Categorize a prompt.
        
        Args:
            prompt (str): The prompt to categorize
            
        Returns:
            str: The primary category
        """
        # Analyze the prompt
        analysis = self.analyze(prompt)
        
        # Get the primary category
        return analysis["primary_category"]
