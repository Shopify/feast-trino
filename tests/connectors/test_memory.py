import pandas as pd
import pytest

from feast_trino.connectors.memory import upload_pandas_dataframe_to_trino
from feast_trino.trino_utils import Trino

HOST = "localhost"
PORT = "8080"
TEST_SCHEMA = "memory"
TEST_TABLE_REF = f"{TEST_SCHEMA}.ci.my_df"


@pytest.fixture
def client():
    return Trino(user="user", catalog=TEST_SCHEMA, host=HOST, port=PORT)


def test_base_case(client):
    client.execute_query(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}.ci")
    client.execute_query(f"DROP TABLE IF EXISTS {TEST_TABLE_REF}")

    input_df = pd.DataFrame(
        data={"id": [1, 2, 3], "value": [4, 5, 6], "str": ["a", "b", "c"]}
    )

    upload_pandas_dataframe_to_trino(
        client=client, df=input_df, table_ref=TEST_TABLE_REF
    )

    actual_results = client.execute_query(f"SELECT * FROM {TEST_TABLE_REF}")
    actual_df = pd.DataFrame(
        data=actual_results.data, columns=actual_results.columns_names
    )
    pd.testing.assert_frame_equal(input_df, actual_df)
