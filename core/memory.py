import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.vector_db import VectorDB
from core.tagger import Tagger

class Memory:
   
    def __init__(self, 
        memory_file: str = "datastore/memory.json",
        vector_db: Optional[VectorDB] = None,
        tagger: Optional[Tagger] = None):
        self._short_term_memory: Dict[str, Dict] = {}
        self._memory_file = memory_file
        
        # Initialize vector database
        self._vector_db = vector_db if vector_db is not None else VectorDB()
        
        # Initialize tagger
        self._tagger = tagger if tagger is not None else Tagger()
        
        # Create memory file if it doesn't exist
        if not os.path.exists(memory_file):
            os.makedirs(os.path.dirname(memory_file), exist_ok=True)
            with open(memory_file, 'w') as f:
                json.dump({}, f)
    
    def store_short_term(self, user_id: str, data: Dict[str, Any]) -> None:
        if user_id not in self._short_term_memory:
            self._short_term_memory[user_id] = {}
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        
        # Update short-term memory
        self._short_term_memory[user_id].update(data)
        logging.info(f"Stored data in short-term memory for user {user_id}")
    
    def retrieve_short_term(self, user_id: str) -> Dict[str, Any]:
        return self._short_term_memory.get(user_id, {})
    
    def store_long_term(self, user_id: str, data: Dict[str, Any]) -> None:
        # Add timestamp if not already present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Generate a unique ID for the item if not already present
        if 'request_id' not in data:
            data['request_id'] = str(datetime.now().timestamp())
        
        item_id = data['request_id']
        
        # Analyze the prompt and expanded prompt to extract tags and categories
        prompt = data.get('prompt', '')
        expanded_prompt = data.get('expanded_prompt', '')
        existing_analysis = data.get('analysis', {})
        
        # Perform tagging and categorization
        tagging_result = self._tagger.analyze(prompt, expanded_prompt, existing_analysis)
        
        # Add tags and categories to the data
        data['tags'] = tagging_result['tags']
        data['categories'] = tagging_result['categories']
        data['primary_category'] = tagging_result['primary_category']
        data['styles'] = tagging_result['styles']
        data['colors'] = tagging_result['colors']
        data['moods'] = tagging_result['moods']
        
        # Store in vector database
        text_to_embed = f"{prompt} {expanded_prompt}"
        self._vector_db.add_item(
            item_id=item_id,
            text=text_to_embed,
            metadata={
                'user_id': user_id,
                'prompt': prompt,
                'expanded_prompt': expanded_prompt,
                'image_path': data.get('image_path', ''),
                'model_path': data.get('model_path', ''),
                'timestamp': data['timestamp'],
                'primary_category': tagging_result['primary_category']
            },
            tags=tagging_result['tags']
        )
        
        # Load existing data from JSON file
        try:
            with open(self._memory_file, 'r') as f:
                memory_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.warning(f"Error loading memory file: {e}")
            memory_data = {}
        
        # Initialize user data if not exists
        if user_id not in memory_data:
            memory_data[user_id] = []
        
        # Append new data
        memory_data[user_id].append(data)
        
        # Save updated data
        with open(self._memory_file, 'w') as f:
            json.dump(memory_data, f, indent=2)
        
        logging.info(f"Stored data in long-term memory for user {user_id}")
    
    def retrieve_long_term(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            with open(self._memory_file, 'r') as f:
                memory_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.warning(f"Error retrieving memory: {e}")
            return []
        
        user_data = memory_data.get(user_id, [])
        
        # Sort by timestamp (newest first)
        user_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit if specified
        if limit is not None:
            user_data = user_data[:limit]
        
        return user_data
    
    def search_memory(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        # Search using vector database for semantic similarity
        vector_results = self._vector_db.search_by_text(query, n_results=10)
        
        # Filter results by user_id
        filtered_results = []
        for result in vector_results:
            metadata = result.get('metadata', {})
            if metadata.get('user_id') == user_id:
                # Get the full record from the JSON file
                record_id = result.get('id')
                full_record = self._get_record_by_id(user_id, record_id)
                if full_record:
                    # Add similarity score to the record
                    full_record['similarity_score'] = result.get('similarity')
                    filtered_results.append(full_record)
        
        # If no results from vector search, fall back to simple text search
        if not filtered_results:
            logging.info(f"No vector search results, falling back to text search for query: {query}")
            user_data = self.retrieve_long_term(user_id)
            query_lower = query.lower()
            
            for record in user_data:
                # Search in prompt
                if 'prompt' in record and query_lower in record['prompt'].lower():
                    record['similarity_score'] = 0.5  # Arbitrary score for text match
                    filtered_results.append(record)
                    continue
                
                # Search in expanded_prompt
                if 'expanded_prompt' in record and query_lower in record['expanded_prompt'].lower():
                    record['similarity_score'] = 0.4  # Slightly lower score
                    filtered_results.append(record)
                    continue
        
        return filtered_results
    
    def _get_record_by_id(self, user_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            with open(self._memory_file, 'r') as f:
                memory_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.warning(f"Error retrieving memory: {e}")
            return None
        
        user_data = memory_data.get(user_id, [])
        
        for record in user_data:
            if record.get('request_id') == record_id:
                return record
        
        return None
    
    def search_by_tags(self, user_id: str, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        # Search using vector database for tag matches
        vector_results = self._vector_db.search_by_tags(tags, n_results=limit)
        
        # Filter results by user_id
        filtered_results = []
        for result in vector_results:
            metadata = result.get('metadata', {})
            if metadata.get('user_id') == user_id:
                # Get the full record from the JSON file
                record_id = result.get('id')
                full_record = self._get_record_by_id(user_id, record_id)
                if full_record:
                    filtered_results.append(full_record)
        
        # If no results from vector search, fall back to simple tag search
        if not filtered_results:
            logging.info(f"No vector search results, falling back to simple tag search for tags: {tags}")
            user_data = self.retrieve_long_term(user_id)
            
            for record in user_data:
                if 'tags' in record:
                    record_tags = record['tags']
                    # Check if any of the search tags are in the record tags
                    if any(tag in record_tags for tag in tags):
                        filtered_results.append(record)
                        if len(filtered_results) >= limit:
                            break
        
        return filtered_results
    
    def search_by_category(self, user_id: str, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        user_data = self.retrieve_long_term(user_id)
        
        # Filter by category
        filtered_results = []
        for record in user_data:
            if record.get('primary_category') == category or category in record.get('categories', []):
                filtered_results.append(record)
                if len(filtered_results) >= limit:
                    break
        
        return filtered_results
    
    def get_all_tags(self, user_id: str) -> List[str]:
        user_data = self.retrieve_long_term(user_id)
        
        # Extract all tags
        all_tags = set()
        for record in user_data:
            if 'tags' in record and isinstance(record['tags'], list):
                all_tags.update(record['tags'])
        
        return sorted(list(all_tags))
    
    def get_all_categories(self, user_id: str) -> List[str]:
        user_data = self.retrieve_long_term(user_id)
        
        # Extract all categories
        all_categories = set()
        for record in user_data:
            if 'primary_category' in record:
                all_categories.add(record['primary_category'])
            if 'categories' in record and isinstance(record['categories'], list):
                all_categories.update(record['categories'])
        
        return sorted(list(all_categories))
    
    def update_tags(self, user_id: str, record_id: str, tags: List[str]) -> bool:
        try:
            with open(self._memory_file, 'r') as f:
                memory_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.warning(f"Error retrieving memory: {e}")
            return False
        
        user_data = memory_data.get(user_id, [])
        
        # Find and update the record
        for i, record in enumerate(user_data):
            if record.get('request_id') == record_id:
                # Update tags in the record
                record['tags'] = tags
                
                # Update memory data
                memory_data[user_id][i] = record
                
                # Save updated data
                with open(self._memory_file, 'w') as f:
                    json.dump(memory_data, f, indent=2)
                
                # Update vector database
                self._vector_db.update_item_tags(record_id, tags)
                
                logging.info(f"Updated tags for record {record_id}")
                return True
        
        logging.warning(f"Record {record_id} not found for user {user_id}")
        return False
