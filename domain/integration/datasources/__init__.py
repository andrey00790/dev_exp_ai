"""
DataSources Module
Модуль источников данных
"""

# DataSources Package
"""DataSources package for various data integrations"""

# Conditional imports to handle missing optional dependencies
try:
    from .clickhouse_datasource import ClickHouseDataSource
except ImportError:
    # Mock ClickHouseDataSource if clickhouse-connect is not installed
    class ClickHouseDataSource:
        def __init__(self, *args, **kwargs):
            raise ImportError("clickhouse-connect package is required for ClickHouse support")

try:
    from .ydb_datasource import YDBDataSource  
except ImportError:
    # Mock YDBDataSource if ydb is not installed
    class YDBDataSource:
        def __init__(self, *args, **kwargs):
            raise ImportError("ydb package is required for YDB support")

__all__ = [
    "ClickHouseDataSource",
    "YDBDataSource"
] 