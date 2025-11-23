"""Data Manager configuration loader

Loads configuration from config/data_manager.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class StorageConfig:
    """Storage backend configuration (from YAML)"""
    backend: str
    database_path: str
    database_timeout: float
    check_same_thread: bool


@dataclass
class DataManagerConfig:
    """Complete data manager configuration (from YAML)"""
    storage: StorageConfig
    models: Dict[str, Dict[str, Any]]
    cascade_request_delete: bool
    cascade_query_delete: bool
    retention_enabled: bool
    logging_level: str
    log_all_operations: bool


def create_test_config(db_path: str) -> DataManagerConfig:
    """
    Create a test DataManagerConfig with specified database path.

    Args:
        db_path: Path to temporary test database

    Returns:
        DataManagerConfig instance for testing
    """
    storage = StorageConfig(
        backend="sqlite",
        database_path=db_path,
        database_timeout=5.0,
        check_same_thread=False
    )

    models = {
        "request_model": {
            "name": "request_model",
            "table": "request_models",
            "description": "Complete raw API request and response log"
        },
        "query_model": {
            "name": "query_model",
            "table": "query_models",
            "description": "Structured query information"
        },
        "response_item": {
            "name": "response_item",
            "table": "response_items",
            "description": "Single search result item"
        }
    }

    return DataManagerConfig(
        storage=storage,
        models=models,
        cascade_request_delete=True,
        cascade_query_delete=True,
        retention_enabled=False,
        logging_level="INFO",
        log_all_operations=False
    )


def load_config(config_path: str = "config/data_manager.yaml") -> DataManagerConfig:
    """
    Load data manager configuration from YAML file.

    Args:
        config_path: Path to config file (relative to project root)

    Returns:
        DataManagerConfig instance

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    # Resolve path relative to project root
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / config_path

    if not config_file.exists():
        raise FileNotFoundError(f"Data manager config file not found: {config_file}")

    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Parse storage config (required)
    if 'storage' not in data:
        raise ValueError("Missing 'storage' section in config")

    storage_data = data['storage']
    if 'backend' not in storage_data:
        raise ValueError("Missing 'storage.backend' in config")
    if 'database' not in storage_data:
        raise ValueError("Missing 'storage.database' section in config")

    database_data = storage_data['database']
    if 'path' not in database_data:
        raise ValueError("Missing 'storage.database.path' in config")
    if 'timeout' not in database_data:
        raise ValueError("Missing 'storage.database.timeout' in config")
    if 'check_same_thread' not in database_data:
        raise ValueError("Missing 'storage.database.check_same_thread' in config")

    storage = StorageConfig(
        backend=storage_data['backend'],
        database_path=database_data['path'],
        database_timeout=database_data['timeout'],
        check_same_thread=database_data['check_same_thread']
    )

    # Parse models (required)
    if 'models' not in data:
        raise ValueError("Missing 'models' section in config")

    models_list = data['models']
    models = {model['name']: model for model in models_list}

    # Parse cascade config (required)
    if 'cascade' not in data:
        raise ValueError("Missing 'cascade' section in config")

    cascade = data['cascade']
    cascade_request = cascade['request_delete_cascade']
    cascade_query = cascade['query_delete_cascade']

    # Parse retention config (required)
    if 'retention' not in data:
        raise ValueError("Missing 'retention' section in config")

    retention = data['retention']
    retention_enabled = retention['enabled']

    # Parse logging config (required)
    if 'logging' not in data:
        raise ValueError("Missing 'logging' section in config")

    logging = data['logging']
    logging_level = logging['level']
    log_ops = logging['log_all_operations']

    return DataManagerConfig(
        storage=storage,
        models=models,
        cascade_request_delete=cascade_request,
        cascade_query_delete=cascade_query,
        retention_enabled=retention_enabled,
        logging_level=logging_level,
        log_all_operations=log_ops
    )
