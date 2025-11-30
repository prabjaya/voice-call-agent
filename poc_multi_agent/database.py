"""
MongoDB Database for Multi-Agent POC
Stores call sessions, collected data, and conversation history
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

logger = logging.getLogger(__name__)

class CallDatabase:
    """MongoDB database for storing call data"""
    
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/multi_agent_poc")
        self.client = None
        self.db = None
        self.calls_collection = None
        self.collected_data_collection = None
        self.init_database()
    
    def init_database(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(self.mongodb_url)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database name from URL or use default
            if 'mongodb+srv://' in self.mongodb_url or 'mongodb://' in self.mongodb_url:
                # Extract database name from connection string
                if '/' in self.mongodb_url.split('@')[-1]:
                    db_part = self.mongodb_url.split('@')[-1].split('/')[1].split('?')[0]
                    db_name = db_part if db_part else 'multi_agent_poc'
                else:
                    db_name = 'multi_agent_poc'
            else:
                db_name = 'multi_agent_poc'
            
            self.db = self.client[db_name]
            
            # Initialize collections
            self.calls_collection = self.db.calls
            self.collected_data_collection = self.db.collected_data
            
            # Create indexes
            self.calls_collection.create_index("call_sid", unique=True)
            self.calls_collection.create_index("agent_type")
            self.calls_collection.create_index("created_at")
            
            self.collected_data_collection.create_index("call_sid")
            self.collected_data_collection.create_index("agent_type")
            
            logger.info(f"✅ MongoDB connected - Database: {db_name}")
            
        except (ConnectionFailure, Exception) as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            logger.warning("Using in-memory storage (data will not persist)")
            self._use_memory_fallback()
    
    def _use_memory_fallback(self):
        """Use in-memory storage when MongoDB is not available"""
        self.client = None
        self.db = None
        self.calls_collection = None
        self.collected_data_collection = None
        self._memory_calls = {}
        self._memory_collected = []
        logger.info("In-memory storage initialized")
    
    def save_call(self, call_sid: str, session: Dict[str, Any]) -> bool:
        """Save or update call session"""
        try:
            call_document = {
                "call_sid": call_sid,
                "agent_type": session.get("agent_type"),
                "stage": session.get("stage"),
                "language": session.get("language"),
                "history": session.get("history", []),
                "data": session.get("data", {}),
                "updated_at": datetime.utcnow()
            }
            
            # Memory fallback
            if self.calls_collection is None:
                if call_sid not in self._memory_calls:
                    call_document["created_at"] = datetime.utcnow()
                self._memory_calls[call_sid] = call_document
                return True
            
            # Add created_at for new documents
            existing = self.calls_collection.find_one({"call_sid": call_sid})
            if not existing:
                call_document["created_at"] = datetime.utcnow()
            
            # Upsert
            self.calls_collection.replace_one(
                {"call_sid": call_sid},
                call_document,
                upsert=True
            )
            
            logger.info(f"💾 Call saved: {call_sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving call {call_sid}: {str(e)}")
            return False
    
    def get_call(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Retrieve call session"""
        try:
            # Memory fallback
            if self.calls_collection is None:
                return self._memory_calls.get(call_sid)
            
            call_doc = self.calls_collection.find_one({"call_sid": call_sid})
            if call_doc:
                call_doc.pop('_id', None)
                return call_doc
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving call {call_sid}: {str(e)}")
            return None
    
    def save_collected_data(self, call_sid: str, agent_type: str, data: Dict[str, Any]) -> bool:
        """Save successfully collected data"""
        try:
            collected_document = {
                "call_sid": call_sid,
                "agent_type": agent_type,
                "data": data,
                "collected_at": datetime.utcnow()
            }
            
            # Memory fallback
            if self.collected_data_collection is None:
                self._memory_collected.append(collected_document)
                return True
            
            self.collected_data_collection.insert_one(collected_document)
            logger.info(f"✅ Data collected for {call_sid}: {data}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving collected data: {str(e)}")
            return False
    
    def get_all_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all calls"""
        try:
            # Memory fallback
            if self.calls_collection is None:
                return list(self._memory_calls.values())[:limit]
            
            cursor = self.calls_collection.find().sort("created_at", -1).limit(limit)
            calls = []
            for doc in cursor:
                doc.pop('_id', None)
                calls.append(doc)
            return calls
            
        except Exception as e:
            logger.error(f"Error getting calls: {str(e)}")
            return []
    
    def get_collected_data(self, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all collected data"""
        try:
            # Memory fallback
            if self.collected_data_collection is None:
                if agent_type:
                    return [d for d in self._memory_collected if d.get("agent_type") == agent_type]
                return self._memory_collected
            
            query = {"agent_type": agent_type} if agent_type else {}
            cursor = self.collected_data_collection.find(query).sort("collected_at", -1)
            
            data = []
            for doc in cursor:
                doc.pop('_id', None)
                data.append(doc)
            return data
            
        except Exception as e:
            logger.error(f"Error getting collected data: {str(e)}")
            return []
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get call analytics"""
        try:
            # Memory fallback
            if self.calls_collection is None:
                total = len(self._memory_calls)
                completed = sum(1 for c in self._memory_calls.values() if c.get("stage") == "completed")
                return {
                    "total_calls": total,
                    "completed_calls": completed,
                    "success_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%"
                }
            
            total_calls = self.calls_collection.count_documents({})
            completed_calls = self.calls_collection.count_documents({"stage": "completed"})
            
            # Agent breakdown
            agent_pipeline = [
                {"$group": {"_id": "$agent_type", "count": {"$sum": 1}}}
            ]
            agent_results = list(self.calls_collection.aggregate(agent_pipeline))
            agent_breakdown = {result["_id"]: result["count"] for result in agent_results}
            
            # Language breakdown
            language_pipeline = [
                {"$group": {"_id": "$language", "count": {"$sum": 1}}}
            ]
            language_results = list(self.calls_collection.aggregate(language_pipeline))
            language_breakdown = {result["_id"]: result["count"] for result in language_results}
            
            return {
                "total_calls": total_calls,
                "completed_calls": completed_calls,
                "success_rate": f"{(completed_calls/total_calls*100):.1f}%" if total_calls > 0 else "0%",
                "agent_breakdown": agent_breakdown,
                "language_breakdown": language_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {}
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
