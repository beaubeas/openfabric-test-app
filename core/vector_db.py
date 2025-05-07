import os
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions

class VectorDB:

    
    def __init__(self, 
        collection_name: str = "creations",
        db_path: str = "datastore/vectordb",
        embedding_model: str = "all-MiniLM-L6-v2"):

        self._db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        try:
            self._client = chromadb.PersistentClient(path=db_path)
            try:
                self._collection = self._client.get_collection(name=collection_name)
                logging.info(f"Using existing collection: {collection_name}")
            except ValueError:
                try:
                    self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
                except Exception as e:
                    logging.warning(f"Failed to initialize SentenceTransformer: {e}")
                    self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
                
                self._collection = self._client.create_collection(
                    name=collection_name,
                    embedding_function=self._embedding_function,
                    metadata={"description": "Collection for storing AI creations"}
                )
                logging.info(f"Created new collection: {collection_name}")
            
            logging.info(f"VectorDB initialized with collection: {collection_name}")
        
        except Exception as e:
            logging.error(f"Error initializing VectorDB: {e}")
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
        try:
            if tags:
                metadata["tags"] = tags
            
            metadata["timestamp"] = datetime.now().isoformat()
            for key, value in metadata.items():
                if not isinstance(value, (str, int, float, bool)):
                    metadata[key] = json.dumps(value)
            
            self._collection.add(
                ids=[item_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            # Only call persist if it's a PersistentClient
            if hasattr(self._client, 'persist'):
                self._client.persist()
            logging.info(f"Added item {item_id} to vector database")
        
        except Exception as e:
            logging.error(f"Error adding item to vector database: {e}")
    
    def search_by_text(self, 
        query_text: str, 
        n_results: int = 5,
        filter_tags: List[str] = None) -> List[Dict[str, Any]]:

        try:
            where_clause = None
            if filter_tags:
                where_clause = {"$and": []}
                for tag in filter_tags:
                    where_clause["$and"].append({"tags": {"$contains": tag}})
            
            results = self._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )
            
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i, item_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                    document = results["documents"][0][i] if results["documents"] and results["documents"][0] else ""
                    distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else None
                    
                    tags = metadata.pop("tags", []) if "tags" in metadata else []
                    if isinstance(tags, str):
                        try:
                            tags = json.loads(tags)
                        except json.JSONDecodeError:
                            tags = [tags]
                    
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

        try:
            where_clause = {"$or": []}
            for tag in tags:
                where_clause["$or"].append({"tags": {"$contains": tag}})
            
            results = self._collection.get(
                where=where_clause,
                limit=n_results
            )
            
            formatted_results = []
            if results["ids"]:
                for i, item_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    document = results["documents"][i] if results["documents"] else ""
                    tags = metadata.pop("tags", []) if "tags" in metadata else []
                    if isinstance(tags, str):
                        try:
                            tags = json.loads(tags)
                        except json.JSONDecodeError:
                            tags = [tags]
                    
                    formatted_results.append({
                        "id": item_id,
                        "text": document,
                        "metadata": metadata,
                        "tags": tags,
                        "similarity": None
                    })
            
            return formatted_results
        
        except Exception as e:
            logging.error(f"Error searching vector database by tags: {e}")
            return []
    
    def get_all_tags(self) -> List[str]:

        try:
            results = self._collection.get()
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
        try:
            results = self._collection.get(ids=[item_id])
            if not results["ids"]:
                logging.warning(f"Item {item_id} not found in vector database")
                return False
            
            metadata = results["metadatas"][0] if results["metadatas"] else {}
            metadata["tags"] = tags
            self._collection.update(
                ids=[item_id],
                metadatas=[metadata]
            )
            
            # Only call persist if it's a PersistentClient
            if hasattr(self._client, 'persist'):
                self._client.persist()
            
            logging.info(f"Updated tags for item {item_id}")
            return True
        
        except Exception as e:
            logging.error(f"Error updating item tags: {e}")
            return False
    
    def delete_item(self, item_id: str) -> bool:

        try:
            self._collection.delete(ids=[item_id])
            # Only call persist if it's a PersistentClient
            if hasattr(self._client, 'persist'):
                self._client.persist()
            
            logging.info(f"Deleted item {item_id} from vector database")
            return True
        
        except Exception as e:
            logging.error(f"Error deleting item: {e}")
            return False
    
    def get_item_count(self) -> int:
        try:
            return self._collection.count()
        except Exception as e:
            logging.error(f"Error getting item count: {e}")
            return 0
