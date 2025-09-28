import uuid
from google.adk.sessions.base_session_service import BaseSessionService, ListSessionsResponse
from google.adk.sessions.session import Session
from pymongo.collection import Collection
from typing import Optional
from datetime import datetime


class MongoSessionService(BaseSessionService):
    """A session service that persists session state in MongoDB."""

    def _init_(self, collection: Collection):
        self.collection = collection
        print("MongoSessionService initialized.")

    async def get_session(
        self, *, app_name: str, user_id: str, session_id: str, config=None
    ) -> Optional[Session]:
        query = {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
        }

        session_doc = self.collection.find_one(query)

        if session_doc:
            return Session(
                id=session_doc["session_id"],
                app_name=session_doc["app_name"],
                user_id=session_doc["user_id"],
                state=session_doc.get("state", {}),
                events=[],
                last_update_time=session_doc.get("last_update_time", 0.0),
            )
        return None

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: Optional[str] = None,
        state: Optional[dict] = None,
    ) -> Session:
        session_id = session_id or str(uuid.uuid4())

    
        doc = {
            "session_id": session_id,
            "app_name": app_name,
            "user_id": user_id,
            "state": state or {},
            "last_update_time": datetime.utcnow().timestamp(),
        }

        self.collection.update_one(
            {"session_id": session_id, "user_id": user_id, "app_name": app_name},
            {"$set": doc},
            upsert=True,
        )
        

        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=doc["state"],
            events=[],
            last_update_time=doc["last_update_time"],
        )

    async def list_sessions(
        self, *, app_name: str, user_id: str
    ) -> ListSessionsResponse:
        query = {"app_name": app_name, "user_id": user_id}
        sessions = []

        for doc in self.collection.find(query):
            sessions.append(
                Session(
                    id=doc["session_id"],
                    app_name=doc["app_name"],
                    user_id=doc["user_id"],
                    state=doc.get("state", {}),
                    events=[],
                    last_update_time=doc.get("last_update_time", 0.0),
                )
            )

        return ListSessionsResponse(sessions=sessions)

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        self.collection.delete_one(
            {
                "app_name": app_name,
                "user_id": user_id,
                "session_id": session_id,
            }
        )