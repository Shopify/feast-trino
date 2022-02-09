# Feast Trino Support

Trino is not included in current [Feast](https://github.com/feast-dev/feast) roadmap, this project intends to add Trino support for Offline Store.  

## Version compatibilities
The feast-trino plugin is tested on the following versions of python [3.7, 3.8, 3.9]

Here is also how the current feast-trino plugin has been tested against different versions of Feast and Trino

| Feast-trino | Feast                   | Trino |
|-------------|-------------------------|-------|
| 1.0.*       | From 0.15.\* to 0.16.\* | 364   |

## Quickstart

#### Install feast-trino

- Install stable version

```shell
pip install feast-trino
```

- Install develop version (not stable):

```shell
pip install git+https://github.com/shopify/feast-trino.git@main
```

#### Create a feature repository

```shell
feast init feature_repo
```

#### Edit `feature_store.yaml`

set `offline_store` type to be `feast_trino.TrinoOfflineStore`

```yaml
project: feature_repo
registry: data/registry.db
provider: local
offline_store:
    type: feast_trino.trino.TrinoOfflineStore
    host: localhost
    port: 8080
    catalog: memory
    connector:
        type: memory
online_store:
    path: data/online_store.db
```

#### Create Trino Table
<!-- TODO -->

#### Edit `feature_repo/example.py`

```python
# This is an example feature definition file
import pandas as pd
from google.protobuf.duration_pb2 import Duration
from feast import Entity, Feature, FeatureView, FileSource, ValueType, FeatureStore

from feast_trino.connectors.upload import upload_pandas_dataframe_to_trino
from feast_trino import TrinoSource
from feast_trino.trino_utils import Trino

store = FeatureStore(repo_path="feature_repo")

client = Trino(
    user="user",
    catalog=store.config.offline_store.catalog,
    host=store.config.offline_store.host,
    port=store.config.offline_store.port,
)
client.execute_query("CREATE SCHEMA IF NOT EXISTS feast")
client.execute_query("DROP TABLE IF EXISTS feast.driver_stats")

input_df = pd.read_parquet("./feature_repo/data/driver_stats.parquet")
upload_pandas_dataframe_to_trino(
    client=client,
    df=input_df,
    table_ref="feast.driver_stats",
    connector_args={"type": "memory"},
)


# Read data from parquet files. Parquet is convenient for local development mode. For
# production, you can use your favorite DWH, such as BigQuery. See Feast documentation
# for more info.
driver_hourly_stats = TrinoSource(
    event_timestamp_column="event_timestamp",
    table_ref="feast.driver_stats",
    created_timestamp_column="created",
)

# Define an entity for the driver. You can think of entity as a primary key used to
# fetch features.
driver = Entity(name="driver_id", value_type=ValueType.INT64, description="driver id",)

# Our parquet files contain sample data that includes a driver_id column, timestamps and
# three feature column. Here we define a Feature View that will allow us to serve this
# data to our model online.
driver_hourly_stats_view = FeatureView(
    name="driver_hourly_stats",
    entities=["driver_id"],
    ttl=Duration(seconds=86400 * 1),
    features=[
        Feature(name="conv_rate", dtype=ValueType.FLOAT),
        Feature(name="acc_rate", dtype=ValueType.FLOAT),
        Feature(name="avg_daily_trips", dtype=ValueType.INT64),
    ],
    online=True,
    batch_source=driver_hourly_stats,
    tags={},
)
store.apply([driver, driver_hourly_stats_view])

# Run an historical retrieval query
output_df = store.get_historical_features(
    entity_df="""
    SELECT
        1004 AS driver_id,
        TIMESTAMP '2021-11-21 15:00:00+00:00' AS event_timestamp
    """,
    features=["driver_hourly_stats:conv_rate"]
).to_df()
print(output_df.head())
```

#### Apply the feature definitions

```shell
python feature_repo/example.py
```


## Developing and Testing

#### Developing

```shell
git clone https://github.com/shopify/feast-trino.git
cd feast-trino
# creating virtual env ...
python -v venv venv/
source venv/bin/activate

make build

# before commit
make format
make lint
```

#### Testing unit test

```shell
make start-local-cluster
make test
make kill-local-cluster
```

__Note: You can visit http://localhost:8080/ui/ to access the Web UI of Trino. This makes it easy to look for queries.__

#### Testing against Feast universal suite

```shell
make install-feast-submodule
make start-local-cluster
make test-python-universal
make kill-local-cluster
```

#### Using different versions of Feast or Trino
The [makefile](./Makefile) contains the following default values:
- FEAST_VERSION: 0.17.0
- TRINO_VERSION: 364

Thus, `make install-feast-submodule` will automatically compile Feast `0.17.0`. If you want to try another version like `0.18.0`, you just need to run `make install-feast-submodule FEAST_VERSION=0.18.0`

Same applies for TRINO_VERSION when you start the local cluster `make start-local-cluster TRINO_VERSION=XXX`