import os
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

class VectorDB:
    """
    VectorDB class that handles vector-based storage and retrieval using ChromaDB.
    
    Attributes:
        _client (chromadb.Client): ChromaDB client
        _collection (chromadb.Collection): ChromaDB collection for storing embeddings
        _embedding_function (chromadb.utils.embedding_functions.EmbeddingFunction): Function to generate embeddings
        _db_path (str): Path to the ChromaDB persistence directory
    """
    
    def __init__(self, 
                 collection_name: str = "creations",
                 db_path: str = "datastore/vectordb",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the VectorDB instance.
        
        Args:
            collection_name (str): Name of the collection to use
            db_path (str): Path to the ChromaDB persistence directory
            embedding_model (str): Name of the sentence-transformer model to use for embeddings
        """
        self._db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        try:
            # Initialize ChromaDB client with persistence
            self._client = chromadb.PersistentClient(path=db_path)
            
            # Try to get the collection if it exists, otherwise create it
            try:
                self._collection = self._client.get_collection(name=collection_name)
                logging.info(f"Using existing collection: {collection_name}")
            except ValueError:
                # Initialize embedding function
                try:
                    # Try to use sentence-transformers directly
                    model = SentenceTransformer(embedding_model)
                    self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
                except Exception as e:
                    logging.warning(f"Failed to initialize SentenceTransformer: {e}")
                    # Fall back to default embedding function
                    self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
                
                # Create a new collection
                self._collection = self._client.create_collection(
                    name=collection_name,
                    embedding_function=self._embedding_function,
                    metadata={"description": "Collection for storing AI creations"}
                )
                logging.info(f"Created new collection: {collection_name}")
            
            logging.info(f"VectorDB initialized with collection: {collection_name}")
        
        except Exception as e:
            logging.error(f"Error initializing VectorDB: {e}")
            # Create a fallback in-memory client
            self._client = chromadb.EphemeralClient()
            self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
            self._collection = self._client.create_collection(
                name=collection_name,
                embedding_function=self._embedding_function
            )
            logging.warning(f"Using in-memory fallback for VectorDB")
    
    def add_item(self, 
                 item_id: str,
                 text: str,
                 metadata: Dict[str, Any],
                 tags: List[str] = None) -> None:
        """
        Add an item to the vector database.
        
        Args:
            item_id (str): Unique identifier for the item
            text (str): Text to embed
            metadata (Dict[str, Any]): Metadata for the item
            tags (List[str], optional): Tags for the item
        """
        try:
            # Add tags to metadata if provided
            if tags:
                metadata["tags"] = tags
            
            # Add timestamp to metadata
            metadata["timestamp"] = datetime.now().isoformat()
            
            # Convert any non-string metadata values to strings
            for key, value in metadata.items():
                if not isinstance(value, (str, int, float, bool)):
                    metadata[key] = json.dumps(value)
            
            # Add the item to the collection
            self._collection.add(
                ids=[item_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            # Persist the changes
            self._client.persist()
            
            logging.info(f"Added item {item_id} to vector database")
        
        except Exception as e:
            logging.error(f"Error adding item to vector database: {e}")
    
    def search_by_text(self, 
                       query_text: str, 
                       n_results: int = 5,
                       filter_tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for items by text similarity.
        
        Args:
            query_text (str): Text to search for
            n_results (int): Maximum number of results to return
            filter_tags (List[str], optional): Filter results by tags
            
        Returns:
            List[Dict[str, Any]]: List of matching items
        """
        try:
            # Prepare filter if tags are provided
            where_clause = None
            if filter_tags:
                # Create a filter for items that have any of the specified tags
                where_clause = {"$and": []}
                for tag in filter_tags:
                    where_clause["$and"].append({"tags": {"$contains": tag}})
            
            # Search the collection
            results = self._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )
            
            # Format the results
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i, item_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                    document = results["documents"][0][i] if results["documents"] and results["documents"][0] else ""
                    distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else None
                    
                    # Extract tags from metadata
                    tags = metadata.pop("tags", []) if "tags" in metadata else []
                    if isinstance(tags, str):
                        try:
                            tags = json.loads(tags)
                        except json.JSONDecodeError:
                            tags = [tags]
                    
                    # Format the result
                    formatted_results.append({
                        "id": item_id,
                        "text": document,
                        "metadata": metadata,
                        "tags": tags,
                        "similarity": 1.0 - (distance / 2) if distance is not None else None
                    })
            
            return formatted_results
        
        except Exception as e:
            logging.error(f"Error searching vector database: {e}")
            return []
    
    def search_by_tags(self, tags: List[str], n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for items by tags.
        
        Args:
            tags (List[str]): Tags to search for
            n_results (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching items
        """
        try:
            # Create a filter for items that have any of the specified tags
            where_clause = {"$or": []}
            for tag in tags:
                where_clause["$or"].append({"tags": {"$contains": tag}})
            
            # Search the collection
            results = self._collection.get(
                where=where_clause,
                limit=n_results
            )
            
            # Format the results
            formatted_results = []
            if results["ids"]:
                for i, item_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    document = results["documents"][i] if results["documents"] else ""
                    
                    # Extract tags from metadata
                    tags = metadata.pop("tags", []) if "tags" in metadata else []
                    if isinstance(tags, str):
                        try:
                            tags = json.loads(tags)
                        except json.JSONDecodeError:
                            tags = [tags]
                    
                    # Format the result
                    formatted_results.append({
                        "id": item_id,
                        "text": document,
                        "metadata": metadata,
                        "tags": tags,
                        "similarity": None  # No similarity score for tag-based search
                    })
            
            return formatted_results
        
        except Exception as e:
            logging.error(f"Error searching vector database by tags: {e}")
            return []
    
    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags in the database.
        
        Returns:
            List[str]: List of unique tags
        """
        try:
            # Get all items
            results = self._collection.get()
            
            # Extract tags from metadata
            all_tags = set()
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "tags" in metadata:
                        tags = metadata["tags"]
                        if isinstance(tags, str):
                            try:
                                tags = json.loads(tags)
                            except json.JSONDecodeError:
                                tags = [tags]
                        
                        if isinstance(tags, list):
                            all_tags.update(tags)
            
            return sorted(list(all_tags))
        
        except Exception as e:
            logging.error(f"Error getting all tags: {e}")
            return []
    
    def update_item_tags(self, item_id: str, tags: List[str]) -> bool:
        """
        Update the tags for an item.
        
        Args:
            item_id (str): Unique identifier for the item
            tags (List[str]): New tags for the item
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the item
            results = self._collection.get(ids=[item_id])
            
            if not results["ids"]:
                logging.warning(f"Item {item_id} not found in vector database")
                return False
            
            # Get the existing metadata
            metadata = results["metadatas"][0] if results["metadatas"] else {}
            
            # Update the tags
            metadata["tags"] = tags
            
            # Update the item
            self._collection.update(
                ids=[item_id],
                metadatas=[metadata]
            )
            
            # Persist the changes
            self._client.persist()
            
            logging.info(f"Updated tags for item {item_id}")
            return True
        
        except Exception as e:
            logging.error(f"Error updating item tags: {e}")
            return False
    
    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item from the vector database.
        
        Args:
            item_id (str): Unique identifier for the item
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete the item
            self._collection.delete(ids=[item_id])
            
            # Persist the changes
            self._client.persist()
            
            logging.info(f"Deleted item {item_id} from vector database")
            return True
        
        except Exception as e:
            logging.error(f"Error deleting item: {e}")
            return False
    
    def get_item_count(self) -> int:
        """
        Get the number of items in the vector database.
        
        Returns:
            int: Number of items
        """
        try:
            return self._collection.count()
        except Exception as e:
            logging.error(f"Error getting item count: {e}")
            return 0
