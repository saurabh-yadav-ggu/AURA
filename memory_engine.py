import os
import datetime
import uuid
import json
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai
from google.genai import types

load_dotenv()

class AURAMemoryEngine:
    def __init__(self):
        # Initialize Google GenAI client
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        self.embedding_model = "gemini-embedding-001"
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "AURA")
        
        # Connect to index
        self.index = self.pc.Index(self.index_name, host=os.getenv("PINECONE_HOST"))

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using gemini-embedding-001 coerced to 768 dimensions"""
        response = self.gemini_client.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY",
                output_dimensionality=768
            )
        )
        # Guarantee it returns exactly 768 dimensions to match the Pinecone index
        values = response.embeddings[0].values
        return values[:768]

    def _generate_memory_id(self) -> str:
        return f"mem_{uuid.uuid4().hex}"

    def store_memory(self, 
                    content: str, 
                    memory_type: str, 
                    metadata: Dict[str, Any], 
                    importance_score: float = 1.0) -> str:
        """
        Base method to store a memory into Pinecone.
        memory_type: 'conversation', 'screen', 'task', 'workflow', etc.
        """
        # Prepare metadata
        full_metadata = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "memory_type": memory_type,
            "importance_score": importance_score,
            "content": content,
            **metadata
        }
        
        # Clean up metadata for Pinecone (must be flat strings/numbers/lists)
        for k, v in full_metadata.items():
            if isinstance(v, (dict, bool)):
                full_metadata[k] = json.dumps(v)
            if v is None:
                full_metadata[k] = ""
                
        # Get embedding
        vector = self._get_embedding(content)
        memory_id = self._generate_memory_id()
        
        # Upsert to Pinecone
        self.index.upsert(
            vectors=[{
                "id": memory_id,
                "values": vector,
                "metadata": full_metadata
            }]
        )
        print(f"[MEMORY] Stored {memory_type} memory: {memory_id}")
        return memory_id

    def store_conversation(self, user_msg: str, ai_response: str, project_context: str = ""):
        """Stores episodic conversational memory"""
        content = f"User: {user_msg}\nAURA: {ai_response}"
        metadata = {
            "project_context": project_context,
            "activity_type": "conversation",
            "tags": ["dialogue", "interaction"]
        }
        # A lightweight way to determine importance could go here
        importance = 1.5 if len(user_msg) > 50 else 1.0
        return self.store_memory(content, "conversation", metadata, importance_score=importance)

    def store_screen_observation(self, ocr_text: str, app_name: str, window_title: str):
        """Stores visual memory from screen understanding"""
        content = f"App: {app_name}\nTitle: {window_title}\nOn Screen: {ocr_text}"
        metadata = {
            "application_name": app_name,
            "window_title": window_title,
            "activity_type": "screen_observation",
            "tags": ["visual", "ocr", app_name]
        }
        return self.store_memory(content, "screen", metadata, importance_score=1.2)

    def store_task_context(self, task_description: str, status: str = "ongoing"):
        """Stores active tasks and workflows"""
        metadata = {
            "activity_type": "task",
            "status": status,
            "tags": ["workflow", "goal"]
        }
        return self.store_memory(task_description, "task", metadata, importance_score=2.0)

    def retrieve_context(self, query: str, top_k: int = 5, filter_type: Optional[str] = None) -> List[Dict]:
        """
        Semantic search for contextual memory retrieval.
        Returns a list of relevant past memories.
        """
        query_vector = self._get_embedding(query)
        
        filter_dict = {}
        if filter_type:
            filter_dict["memory_type"] = {"$eq": filter_type}
            
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        memories = []
        for match in results.matches:
            memories.append({
                "id": match.id,
                "score": match.score,
                "content": match.metadata.get("content", ""),
                "memory_type": match.metadata.get("memory_type", ""),
                "timestamp": match.metadata.get("timestamp", ""),
                "application": match.metadata.get("application_name", ""),
            })
            
        return memories

    def get_assistant_context_prompt(self, current_query: str) -> str:
        """
        Builds a comprehensive system prompt prefix injected with retrieved long-term memory.
        """
        relevant_memories = self.retrieve_context(current_query, top_k=7)
        
        if not relevant_memories:
            return ""
            
        context_str = "--- LONG TERM MEMORY CONTEXT ---\n"
        context_str += "The following are relevant past interactions, screen observations, and tasks:\n\n"
        
        for mem in relevant_memories:
            date_str = mem['timestamp'][:10] if mem['timestamp'] else "Past"
            mem_type = mem['memory_type'].upper()
            context_str += f"[{date_str}] ({mem_type} MEMORY): {mem['content']}\n"
            
        context_str += "--------------------------------\n"
        context_str += "Use this memory context to deeply personalize your response and maintain continuity.\n"
        return context_str

if __name__ == "__main__":
    # Quick test
    engine = AURAMemoryEngine()
    print("Memory Engine Initialized!")
