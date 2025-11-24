"""Data Manager singleton

Manages all data model operations with a unified public API.
"""

from typing import Dict, Any, Optional, Union, Type
from .models import RequestModel, ResponseItem, DataModelType
from .config import load_config, DataManagerConfig
from .storage import SQLiteBackend


class DataManager:
    """
    Singleton data manager for handling all data model operations.

    Public API:
    - record(model_type, data_value, associated_case=None)
    - retrieve(model_type, case_key)
    - explore(model_type)
    - models()
    """

    _instance: Optional['DataManager'] = None
    _test_config: Optional[DataManagerConfig] = None  # For testing with custom config

    def __new__(cls):
        """Singleton pattern - only one instance globally"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[DataManagerConfig] = None):
        """Initialize DataManager (only once per configuration)

        Args:
            config: Optional custom DataManagerConfig (primarily for testing)

        Note: When test_config changes, this will reinitialize even if _initialized=True
        """
        # Determine which config to use
        if config:
            current_config = config
        elif DataManager._test_config:
            current_config = DataManager._test_config
        else:
            current_config = load_config()

        # Check if we need to reinitialize (for test isolation)
        # This handles the case where _test_config changes between tests
        if self._initialized and hasattr(self, 'config'):
            # Compare database paths - if they differ, we need to reinitialize
            current_db_path = current_config.storage.database_path
            previous_db_path = self.config.storage.database_path
            if current_db_path == previous_db_path:
                # Same database path, skip reinitialization
                return
            # Different database path (test isolation), force reinitialization
            self._initialized = False

        if self._initialized:
            return

        # Load configuration (use provided config or load from file)
        self.config = current_config

        # Initialize storage backend
        if self.config.storage.backend == "sqlite":
            self.storage = SQLiteBackend(
                db_path=self.config.storage.database_path,
                timeout=self.config.storage.database_timeout,
                check_same_thread=self.config.storage.check_same_thread
            )
        else:
            raise ValueError(f"Unsupported storage backend: {self.config.storage.backend}")

        self._initialized = True

    # Public API
    # =========================================================================

    def record(
        self,
        model_type: Union[str, DataModelType],
        data_value: Dict[str, Any],
        associated_case: Optional[RequestModel] = None
    ) -> str:
        """
        Record a data model instance.

        Args:
            model_type: Type of model (str or DataModelType enum)
            data_value: Python dict with model data (original python objects)
            associated_case: Optional associated RequestModel instance

        Returns:
            ID of the created record

        Raises:
            ValueError: If model_type is invalid or association is missing/invalid
        """
        # Normalize model_type
        if isinstance(model_type, DataModelType):
            model_name = model_type.value
        else:
            model_name = model_type

        # Validate and create appropriate model instance
        if model_name == DataModelType.REQUEST.value:
            return self._record_request(data_value)

        elif model_name == DataModelType.RESPONSE_ITEM.value:
            if not associated_case or not isinstance(associated_case, RequestModel):
                raise ValueError(
                    f"ResponseItem requires associated_case to be RequestModel instance"
                )
            return self._record_response_item(data_value, associated_case)

        else:
            raise ValueError(f"Unknown model type: {model_name}")

    def retrieve(
        self,
        model_type: Union[str, DataModelType],
        case_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a data model instance by ID.

        Args:
            model_type: Type of model (str or DataModelType enum)
            case_key: Unique identifier (UUID) of the record

        Returns:
            Dictionary representation of the model, or None if not found

        Raises:
            ValueError: If model_type is invalid
        """
        # Normalize model_type
        if isinstance(model_type, DataModelType):
            model_name = model_type.value
        else:
            model_name = model_type

        if model_name == DataModelType.REQUEST.value:
            return self.storage.get_request(case_key)

        elif model_name == DataModelType.RESPONSE_ITEM.value:
            return self.storage.get_response_item(case_key)

        else:
            raise ValueError(f"Unknown model type: {model_name}")

    def explore(self, model_type: Union[str, DataModelType]) -> Dict[str, Any]:
        """
        Explore a model type - get report with available case keys.

        Args:
            model_type: Type of model (str or DataModelType enum)

        Returns:
            Dictionary with:
            - total: Total count
            - by_agent: Count per agent
            - sample_keys: Sample case keys for retrieve()

        Raises:
            ValueError: If model_type is invalid
        """
        # Normalize model_type
        if isinstance(model_type, DataModelType):
            model_name = model_type.value
        else:
            model_name = model_type

        # Get statistics
        stats = self.storage.get_stats(model_name)

        # Get sample keys
        if model_name == DataModelType.REQUEST.value:
            sample_keys = self.storage.list_requests(limit=5)
        elif model_name == DataModelType.RESPONSE_ITEM.value:
            sample_keys = self.storage.list_response_items(limit=5)
        else:
            raise ValueError(f"Unknown model type: {model_name}")

        return {
            "model_type": model_name,
            "total": stats.get("total", 0),
            "by_agent": stats.get("by_agent", {}),
            "sample_keys": sample_keys
        }

    def models(self) -> list:
        """
        Get list of available data models.

        Returns:
            List of DataModelType enum values
        """
        return [member.value for member in DataModelType]

    def delete(
        self,
        model_type: Union[str, DataModelType],
        case_key: str,
        cascade: bool = True
    ) -> int:
        """
        Delete a record by ID.

        Args:
            model_type: Type of model (str or DataModelType enum)
            case_key: Unique identifier (UUID) of the record
            cascade: If True, delete associated records (for REQUEST and QUERY)

        Returns:
            Number of records deleted (including cascaded records)

        Raises:
            ValueError: If model_type is invalid
        """
        # Normalize model_type
        if isinstance(model_type, DataModelType):
            model_name = model_type.value
        else:
            model_name = model_type

        if model_name == DataModelType.REQUEST.value:
            return self.storage.delete_request(case_key, cascade=cascade)
        elif model_name == DataModelType.RESPONSE_ITEM.value:
            return 1 if self.storage.delete_response_item(case_key) else 0
        else:
            raise ValueError(f"Unknown model type: {model_name}")

    def delete_all(self) -> int:
        """
        Delete all records from all tables.

        Returns:
            Total number of records deleted
        """
        return self.storage.delete_all()

    def smart_query(self, query_arg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Smart query method with multiple use cases.

        Args:
            query_arg: Query argument supporting three patterns:
                - None/empty: Return statistics {model1: count1, model2: count2}
                - Dict like {'request_model': 5}: Return latest 5 cases for each model
                - Dict like {'request_model': 'uuid-string'}: Return cascaded related instances
                  - REQUEST ID → returns associated RESPONSE_ITEMs

        Returns:
            Dictionary with results based on query_arg:
            - Statistics: {model1: count, model2: count}
            - Latest N cases: {model: [case_dict1, case_dict2, ...]}
            - Cascaded lookup: {model_name: [associated_instances]}
        """
        # Use case 1: Empty query - return statistics
        if query_arg is None or (isinstance(query_arg, dict) and len(query_arg) == 0):
            return self._smart_query_statistics()

        # Validate dict format
        if not isinstance(query_arg, dict):
            raise ValueError(
                f"Invalid query_arg: {query_arg}. "
                f"Expected None, empty dict, dict with {{model: count}} format, or dict with {{model: id_str}} format"
            )

        # Use case 2 & 3: Dict query - return latest N cases OR cascaded related instances
        return self._smart_query_dict(query_arg)

    # Private methods
    # =========================================================================

    def _smart_query_statistics(self) -> Dict[str, Any]:
        """Use case 1: Return statistics for all models"""
        stats = {}
        for model_type in DataModelType:
            model_stats = self.storage.get_stats(model_type.value)
            stats[model_type.value] = model_stats.get("total", 0)
        return stats

    def _smart_query_dict(self, query_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle dict-format queries.

        Distinguishes between two patterns:
        - {'model': int} → Return latest N cases (Use case 2)
        - {'model': str} → Return cascaded related instances (Use case 3 & 4)
        """
        results = {}

        for model_name, value in query_dict.items():
            # Validate model name exists
            if model_name not in [m.value for m in DataModelType]:
                raise ValueError(f"Unknown model type: {model_name}")

            # Determine if this is a "latest N" query or "cascaded lookup" query
            if isinstance(value, int):
                # Use case 2: Return latest N cases for this model
                if model_name == DataModelType.REQUEST.value:
                    case_ids = self.storage.list_requests(limit=value)
                    cases = [self.retrieve(DataModelType.REQUEST, cid) for cid in case_ids]
                    results[model_name] = cases

                elif model_name == DataModelType.RESPONSE_ITEM.value:
                    case_ids = self.storage.list_response_items(limit=value)
                    cases = [self.retrieve(DataModelType.RESPONSE_ITEM, cid) for cid in case_ids]
                    results[model_name] = cases

            elif isinstance(value, str):
                # Use case 3 & 4: Return cascaded related instances
                case_id = value

                if model_name == DataModelType.REQUEST.value:
                    # REQUEST ID → return associated RESPONSE_ITEMs
                    request_case = self.retrieve(DataModelType.REQUEST, case_id)
                    if request_case:
                        item_ids = self.storage.list_response_items(request_id=case_id)
                        items = [self.retrieve(DataModelType.RESPONSE_ITEM, iid) for iid in item_ids]
                        results[model_name] = items
                    else:
                        results[model_name] = {
                            "error": f"REQUEST ID '{case_id}' not found",
                            "searched_model": DataModelType.REQUEST.value
                        }

                elif model_name == DataModelType.RESPONSE_ITEM.value:
                    # RESPONSE_ITEM has no cascade - return error
                    results[model_name] = {
                        "error": "RESPONSE_ITEM is a leaf node - no cascade available",
                        "searched_model": DataModelType.RESPONSE_ITEM.value
                    }

            else:
                raise ValueError(
                    f"Invalid value type for model '{model_name}': {type(value).__name__}. "
                    f"Expected int (for latest N) or str (for cascaded lookup)"
                )

        return results

    def _record_request(self, data_value: Dict[str, Any]) -> str:
        """Create and store RequestModel"""
        # Build kwargs, excluding keys that should use dataclass defaults
        kwargs = {}

        # Only add keys that are explicitly provided (not None)
        for key in ['request_id', 'agent_name', 'timestamp', 'url', 'method',
                    'headers', 'body', 'raw_response', 'http_status', 'response_type',
                    'execution_time_ms', 'success', 'error_message', 'created_at']:
            if key in data_value:
                value = data_value[key]
                # For optional fields, only add if not None
                if key in ['timestamp', 'raw_response', 'error_message', 'created_at']:
                    if value is not None:
                        kwargs[key] = value
                # For request_id, only add if not empty string
                elif key == 'request_id':
                    if value and value != '':
                        kwargs[key] = value
                # For response_type, only add if provided (default "real_call" will be used)
                elif key == 'response_type':
                    if value is not None:
                        kwargs[key] = value
                # For other fields, always add if key is present
                else:
                    kwargs[key] = value

        # Create model instance - defaults will be used for missing keys
        request = RequestModel(**kwargs)

        # Store and return ID
        return self.storage.insert_request(request)

    def _record_response_item(self, data_value: Dict[str, Any], request: RequestModel) -> str:
        """Create and store ResponseItem"""
        # Build kwargs, excluding keys that should use dataclass defaults
        kwargs = {'request_id': request.request_id}  # Always set the FK

        # Only add keys that are explicitly provided (not None)
        for key in ['item_id', 'agent_name', 'timestamp', 'title', 'content',
                    'source_url', 'source_name', 'category', 'key_entities',
                    'relevance_score', 'significance', 'agent_metadata', 'created_at']:
            if key in data_value:
                value = data_value[key]
                # For optional fields, only add if not None
                if key in ['timestamp', 'category', 'relevance_score', 'significance', 'created_at']:
                    if value is not None:
                        kwargs[key] = value
                # For item_id, only add if not empty string
                elif key == 'item_id':
                    if value and value != '':
                        kwargs[key] = value
                # For other fields, always add if key is present
                else:
                    kwargs[key] = value

        # Create model instance - defaults will be used for missing keys
        item = ResponseItem(**kwargs)

        # Store and return ID
        return self.storage.insert_response_item(item)


# Global singleton instance
_data_manager: Optional[DataManager] = None


def get_data_manager() -> DataManager:
    """Get the global DataManager singleton instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager
