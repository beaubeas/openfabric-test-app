import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

class Memory:
    """
    Memory class that handles both short-term (session) and long-term (persistent) memory.
    
    Attributes:
        _short_term_memory (Dict[str, Dict]): In-memory storage for session context
        _memory_file (str): Path to the file for persistent storage
    """
    
    def __init__(self, memory_file: str = "datastore/memory.json"):
        """
        Initialize the Memory instance.
        
        Args:
            memory_file (str): Path to the file for persistent storage
        """
        self._short_term_memory: Dict[str, Dict] = {}
        self._memory_file = memory_file
        
        # Create memory file if it doesn't exist
        if not os.path.exists(memory_file):
            os.makedirs(os.path.dirname(memory_file), exist_ok=True)
            with open(memory_file, 'w') as f:
                json.dump({}, f)
    
    def store_short_term(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Store data in short-term memory.
        
        Args:
            user_id (str): Unique identifier for the user
            data (Dict[str, Any]): Data to store
        """
        if user_id not in self._short_term_memory:
            self._short_term_memory[user_id] = {}
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        
        # Update short-term memory
        self._short_term_memory[user_id].update(data)
        logging.info(f"Stored data in short-term memory for user {user_id}")
    
    def retrieve_short_term(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve data from short-term memory.
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            Dict[str, Any]: Stored data for the user
        """
        return self._short_term_memory.get(user_id, {})
    
    def store_long_term(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Store data in long-term memory (persistent storage).
        
        Args:
            user_id (str): Unique identifier for the user
            data (Dict[str, Any]): Data to store
        """
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        
        # Load existing data
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
        """
        Retrieve data from long-term memory.
        
        Args:
            user_id (str): Unique identifier for the user
            limit (Optional[int]): Maximum number of records to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of stored data for the user
        """
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
        """
        Search for data in long-term memory based on a simple text query.
        
        Args:
            user_id (str): Unique identifier for the user
            query (str): Text to search for
            
        Returns:
            List[Dict[str, Any]]: List of matching records
        """
        user_data = self.retrieve_long_term(user_id)
        query = query.lower()
        
        # Simple text search
        results = []
        for record in user_data:
            # Search in prompt
            if 'prompt' in record and query in record['prompt'].lower():
                results.append(record)
                continue
            
            # Search in expanded_prompt
            if 'expanded_prompt' in record and query in record['expanded_prompt'].lower():
                results.append(record)
                continue
            
            # Search in description
            if 'description' in record and query in record['description'].lower():
                results.append(record)
                continue
        
        return results
