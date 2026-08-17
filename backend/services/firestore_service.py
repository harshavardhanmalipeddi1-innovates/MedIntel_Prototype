import logging
from typing import Dict, Any, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FirestoreService:
    """
    Abstraction layer for Firestore to support testing and decoupling.
    Do not trust client-side rules alone for production.

    When real Firestore is unavailable, an in-memory mock store is used
    so service and API tests can verify persistence behavior.
    """

    _mock_store: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def __init__(self, mock_db=None):
        self.mock_db = mock_db

        if self.mock_db is None and FIREBASE_AVAILABLE:
            try:
                # Initializes with default application credentials.
                # Requires GOOGLE_APPLICATION_CREDENTIALS in env.
                if not firebase_admin._apps:
                    firebase_admin.initialize_app()

                self.db = firestore.client()

            except Exception as e:
                logger.warning(
                    f"Failed to initialize real Firestore client: {e}"
                )
                self.db = None

        else:
            self.db = self.mock_db

    def add_document(
        self,
        collection: str,
        data: Dict[str, Any],
    ) -> str:
        if self.db is None:
            logger.warning(
                f"Firestore disabled. Mock add_document to {collection}."
            )

            collection_store = self._mock_store.setdefault(
                collection,
                {},
            )

            doc_id = data.get("workflow_id")

            if not doc_id:
                doc_id = f"mock-doc-{len(collection_store) + 1}"

            collection_store[doc_id] = dict(data)

            return doc_id

        doc_ref = self.db.collection(collection).document()
        doc_ref.set(data)
        return doc_ref.id

    def get_document(
        self,
        collection: str,
        doc_id: str,
    ) -> Optional[Dict[str, Any]]:
        if self.db is None:
            logger.warning(
                f"Firestore disabled. Mock get_document "
                f"from {collection}/{doc_id}."
            )

            document = self._mock_store.get(
                collection,
                {},
            ).get(doc_id)

            if document is None:
                return None

            return dict(document)

        doc_ref = self.db.collection(collection).document(doc_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()

        return None

    def update_document(
        self,
        collection: str,
        doc_id: str,
        data: Dict[str, Any],
    ) -> None:
        if self.db is None:
            logger.warning(
                f"Firestore disabled. Mock update_document "
                f"{collection}/{doc_id}."
            )

            collection_store = self._mock_store.setdefault(
                collection,
                {},
            )

            existing = collection_store.get(doc_id, {})
            existing.update(data)
            collection_store[doc_id] = existing

            return

        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.update(data)

    def set_document(
        self,
        collection: str,
        doc_id: str,
        data: Dict[str, Any],
    ) -> None:
        if self.db is None:
            logger.warning(
                f"Firestore disabled. Mock set_document "
                f"{collection}/{doc_id}."
            )

            collection_store = self._mock_store.setdefault(
                collection,
                {},
            )

            collection_store[doc_id] = dict(data)

            return

        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.set(data)