from typing import Any, Dict

import pandas as pd

from feast_trino.connectors.utils import (
    CREATE_SCHEMA_QUERY_TEMPLATE,
    INSERT_ROWS_QUERY_TEMPLATE,
    format_pandas_row,
    get_trino_table_schema_from_dataframe,
    pandas_dataframe_fix_batches,
)
from feast_trino.trino_utils import Trino

SUPPORTED_TYPE = [
    "ORC",
    "PARQUET",
    "AVRO",
    "JSON",
    "CSV",
]


def upload_pandas_dataframe_to_trino(
    client: Trino, df: pd.DataFrame, table_ref: str, config: Dict[str, Any],
) -> None:
    file_type = config["format"]
    if file_type not in SUPPORTED_TYPE:
        raise ValueError(f"The current format is not supported by Hive '{file_type}'")

    client.execute_query(
        _generate_create_schema_query(table_ref=table_ref, df=df, config=config)
    )

    # Upload batchs of 1M rows at a time
    for batch_df in pandas_dataframe_fix_batches(df=df, batch_size=1000000):
        client.execute_query(
            INSERT_ROWS_QUERY_TEMPLATE.format(
                table_ref=table_ref,
                columns=",".join(batch_df.columns),
                values=format_pandas_row(batch_df),
            )
        )


def _generate_create_schema_query(
    table_ref: str, df: pd.DataFrame, config: Dict[str, Any]
) -> str:
    create_schema_query = CREATE_SCHEMA_QUERY_TEMPLATE.format(
        table_ref=table_ref, schema=get_trino_table_schema_from_dataframe(df=df)
    )
    create_schema_query += f"""
    WITH (
        {",".join([f"{k} = '{v}'" for k, v in config.items()])}
    )
    """
    print(create_schema_query)
    return create_schema_query
