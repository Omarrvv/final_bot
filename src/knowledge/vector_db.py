# src/knowledge/vector_db.py
"""
Vector database module for the Egypt Tourism Chatbot.
Handles embedding storage and semantic search capabilities.
"""
import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

class VectorDB:
    """
    Vector database for semantic search capabilities.
    Stores and searches vector embeddings for tourism content.
    """
    
    def __init__(self, vector_db_uri: Optional[str] = None, 
                dimension: int = 1536, 
                content_path: str = "./data/vectors"):
        """
        Initialize the vector database.
        
        Args:
            vector_db_uri (str, optional): Connection URI for external vector DB
            dimension (int): Dimension of embedding vectors
            content_path (str): Path to store vector files if not using external DB
        """
        self.vector_db_uri = vector_db_uri
        self.dimension = dimension
        self.content_path = content_path
        
        # Initialize external vector DB connection if URI provided
        self.external_db = None
        if vector_db_uri:
            try:
                # This would be replaced with actual vector DB client
                # Example: from pinecone import Pinecone; self.external_db = Pinecone(api_key=...)
                logger.info(f"External vector database connection established: {vector_db_uri}")
            except Exception as e:
                logger.error(f"Failed to connect to external vector database: {str(e)}")
        
        # Initialize in-memory vectors if no external DB
        self.vectors = {}
        if not vector_db_uri:
            # Ensure content path exists
            os.makedirs(content_path, exist_ok=True)
            
            # Load vectors from disk
            self._load_vectors()
            
            logger.info(f"Using file-based vector storage at {content_path}")
        
        logger.info("Vector database initialized")
    
    def _load_vectors(self):
        """Load vector data from disk."""
        try:
            index_path = os.path.join(self.content_path, "index.json")
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    self.vectors = json.load(f)
                
                # Convert string arrays back to numpy arrays
                for collection in self.vectors:
                    for item_id, item_data in self.vectors[collection].items():
                        if "vector" in item_data and isinstance(item_data["vector"], list):
                            item_data["vector"] = np.array(item_data["vector"], dtype=np.float32)
                
                logger.info(f"Loaded {sum(len(items) for items in self.vectors.values())} vectors")
            else:
                self._initialize_collections()
        except Exception as e:
            logger.error(f"Failed to load vectors: {str(e)}")
            self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize empty vector collections."""
        self.vectors = {
            "attractions": {},
            "accommodations": {},
            "restaurants": {},
            "practical_info": {}
        }
        
        logger.info("Initialized empty vector collections")
    
    def _save_vectors(self):
        """Save vector data to disk."""
        if self.external_db:
            # No need to save locally if using external DB
            return
        
        try:
            # Convert numpy arrays to lists for JSON serialization
            serializable = {}
            for collection, items in self.vectors.items():
                serializable[collection] = {}
                for item_id, item_data in items.items():
                    serializable[collection][item_id] = {**item_data}
                    if "vector" in item_data and isinstance(item_data["vector"], np.ndarray):
                        serializable[collection][item_id]["vector"] = item_data["vector"].tolist()
            
            # Save to disk
            index_path = os.path.join(self.content_path, "index.json")
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(serializable, f)
            
            logger.info(f"Saved {sum(len(items) for items in self.vectors.values())} vectors")
        except Exception as e:
            logger.error(f"Failed to save vectors: {str(e)}")
    
    def add_vector(self, collection: str, item_id: str, vector: np.ndarray, metadata: Dict = None) -> bool:
        """
        Add a vector to the database.
        
        Args:
            collection (str): Collection name
            item_id (str): Item identifier
            vector (ndarray): Embedding vector
            metadata (dict, optional): Additional metadata
            
        Returns:
            bool: Success status
        """
        if self.external_db:
            # Use external vector DB
            try:
                # Example: self.external_db.upsert(vectors=[(item_id, vector, metadata)], namespace=collection)
                logger.info(f"Added vector to external DB: {collection}/{item_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to add vector to external DB: {str(e)}")
                return False
        
        # Use in-memory/file storage
        try:
            # Ensure collection exists
            if collection not in self.vectors:
                self.vectors[collection] = {}
            
            # Store vector and metadata
            self.vectors[collection][item_id] = {
                "vector": vector,
                "metadata": metadata or {}
            }
            
            # Save to disk
            self._save_vectors()
            
            logger.info(f"Added vector: {collection}/{item_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add vector: {str(e)}")
            return False
    
    def delete_vector(self, collection: str, item_id: str) -> bool:
        """
        Delete a vector from the database.
        
        Args:
            collection (str): Collection name
            item_id (str): Item identifier
            
        Returns:
            bool: Success status
        """
        if self.external_db:
            # Use external vector DB
            try:
                # Example: self.external_db.delete(ids=[item_id], namespace=collection)
                logger.info(f"Deleted vector from external DB: {collection}/{item_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete vector from external DB: {str(e)}")
                return False
        
        # Use in-memory/file storage
        try:
            # Check if collection and item exist
            if collection in self.vectors and item_id in self.vectors[collection]:
                # Remove item
                del self.vectors[collection][item_id]
                
                # Save to disk
                self._save_vectors()
                
                logger.info(f"Deleted vector: {collection}/{item_id}")
                return True
            
            logger.warning(f"Vector not found for deletion: {collection}/{item_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete vector: {str(e)}")
            return False
    
    def search(self, collection: str, query_vector: np.ndarray, filters: Dict = None, 
               limit: int = 10) -> List[Tuple[str, float]]:
        """
        Search for similar vectors in a collection.
        
        Args:
            collection (str): Collection name
            query_vector (ndarray): Query embedding vector
            filters (dict, optional): Metadata filters
            limit (int): Maximum number of results
            
        Returns:
            list: List of (item_id, similarity_score) tuples
        """
        if self.external_db:
            # Use external vector DB
            try:
                # Example: results = self.external_db.query(vector=query_vector, top_k=limit, 
                #                                         namespace=collection, filter=filters)
                # return [(match["id"], match["score"]) for match in results["matches"]]
                logger.warning("External vector DB search not implemented, falling back to in-memory")
            except Exception as e:
                logger.error(f"Failed to search external DB: {str(e)}")
        
        # Use in-memory search
        try:
            results = []
            
            # Check if collection exists
            if collection not in self.vectors:
                return results
            
            # Compute similarities for each vector in the collection
            for item_id, item_data in self.vectors[collection].items():
                # Apply filters if specified
                if filters and not self._apply_filters(item_data.get("metadata", {}), filters):
                    continue
                
                # Compute cosine similarity
                item_vector = item_data["vector"]
                if isinstance(item_vector, list):
                    item_vector = np.array(item_vector, dtype=np.float32)
                
                # Normalize vectors (if not already normalized)
                query_norm = np.linalg.norm(query_vector)
                item_norm = np.linalg.norm(item_vector)
                
                if query_norm > 0 and item_norm > 0:
                    similarity = np.dot(query_vector, item_vector) / (query_norm * item_norm)
                else:
                    similarity = 0.0
                
                results.append((item_id, float(similarity)))
            
            # Sort by similarity (descending) and limit
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        except Exception as e:
            logger.error(f"Failed to search vectors: {str(e)}")
            return []
    
    def _apply_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Apply metadata filters."""
        if not filters:
            return True
        
        for key, value in filters.items():
            # Handle nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                current = metadata
                for part in parts[:-1]:
                    if part not in current:
                        return False
                    current = current[part]
                
                if parts[-1] not in current or current[parts[-1]] != value:
                    return False
            # Handle direct keys
            elif key not in metadata or metadata[key] != value:
                return False
        
        return True
    
    def search_attractions(self, query: str, embedding_model, filters: Dict = None, 
                          language: str = "en", limit: int = 10) -> List[Tuple[str, float]]:
        """
        Search for attractions using text query.
        
        Args:
            query (str): Text query
            embedding_model: Function to generate embeddings
            filters (dict, optional): Metadata filters
            language (str): Query language
            limit (int): Maximum number of results
            
        Returns:
            list: List of (attraction_id, similarity_score) tuples
        """
        # Generate embedding for query
        query_embedding = embedding_model(query, language)
        
        # Search in attractions collection
        return self.search(
            collection="attractions",
            query_vector=query_embedding,
            filters=filters,
            limit=limit
        )
    
    def index_attraction(self, attraction: Dict, embedding_model) -> bool:
        """
        Index an attraction in the vector database.
        
        Args:
            attraction (dict): Attraction data
            embedding_model: Function to generate embeddings
            
        Returns:
            bool: Success status
        """
        try:
            attraction_id = attraction["id"]
            
            # Extract text for indexing
            en_text = []
            ar_text = []
            
            # Add name
            if "name" in attraction:
                en_text.append(attraction["name"].get("en", ""))
                ar_text.append(attraction["name"].get("ar", ""))
            
            # Add description
            if "description" in attraction:
                en_text.append(attraction["description"].get("en", ""))
                ar_text.append(attraction["description"].get("ar", ""))
            
            # Add history
            if "history" in attraction:
                en_text.append(attraction["history"].get("en", ""))
                ar_text.append(attraction["history"].get("ar", ""))
            
            # Add keywords
            if "keywords" in attraction:
                en_text.extend([k for k in attraction["keywords"] if not any('\u0600' <= c <= '\u06FF' for c in k)])
                ar_text.extend([k for k in attraction["keywords"] if any('\u0600' <= c <= '\u06FF' for c in k)])
            
            # Generate embeddings
            en_embedding = embedding_model(" ".join(en_text), "en")
            ar_embedding = embedding_model(" ".join(ar_text), "ar")
            
            # Prepare metadata
            metadata = {
                "type": attraction.get("type", ""),
                "location": {
                    "city": attraction.get("location", {}).get("city", ""),
                    "region": attraction.get("location", {}).get("region", "")
                }
            }
            
            # Add English vector
            en_success = self.add_vector(
                collection="attractions",
                item_id=f"{attraction_id}_en",
                vector=en_embedding,
                metadata=metadata
            )
            
            # Add Arabic vector
            ar_success = self.add_vector(
                collection="attractions",
                item_id=f"{attraction_id}_ar",
                vector=ar_embedding,
                metadata=metadata
            )
            
            return en_success and ar_success
        except Exception as e:
            logger.error(f"Failed to index attraction: {str(e)}")
            return False
    
    def index_all_attractions(self, attractions: Dict[str, Dict], embedding_model) -> Dict[str, bool]:
        """
        Index all attractions in the vector database.
        
        Args:
            attractions (dict): Dictionary of attraction data
            embedding_model: Function to generate embeddings
            
        Returns:
            dict: Dictionary of attraction IDs to success status
        """
        results = {}
        for attraction_id, attraction in attractions.items():
            results[attraction_id] = self.index_attraction(attraction, embedding_model)
        
        return results
    
    def bulk_add_vectors(self, collection: str, items: List[Tuple[str, np.ndarray, Dict]]) -> List[bool]:
        """
        Add multiple vectors in bulk.
        
        Args:
            collection (str): Collection name
            items (list): List of (item_id, vector, metadata) tuples
            
        Returns:
            list: List of success statuses
        """
        if self.external_db:
            # Use external vector DB
            try:
                # Example: self.external_db.upsert(vectors=[(id, vec, meta) for id, vec, meta in items], 
                #                                namespace=collection)
                logger.info(f"Added {len(items)} vectors to external DB: {collection}")
                return [True] * len(items)
            except Exception as e:
                logger.error(f"Failed to bulk add vectors to external DB: {str(e)}")
                return [False] * len(items)
        
        # Use in-memory/file storage
        results = []
        for item_id, vector, metadata in items:
            result = self.add_vector(collection, item_id, vector, metadata)
            results.append(result)
        
        return results