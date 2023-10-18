from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket


@task(retries=3)
def fetch(dataset_url: str) -> pd.DataFrame:
    """Read taxi data from web into pandas DataFrame"""

    df = pd.read_csv(dataset_url)

    return df


@task(log_prints=True)
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Fix dtype issues"""

    df.iloc[:, 1] = pd.to_datetime(df.iloc[:, 1])
    df.iloc[:, 2] = pd.to_datetime(df.iloc[:, 2])

    print(df.head(2))
    print(df.dtypes)
    print(f"Rows: {len(df)}")

    return df


@task()
def write_local(df: pd.DataFrame, color: str, dataset_file: str) -> Path:
    """Write DataFrame out locally as parquet file"""

    path = Path(f"data/{color}/{dataset_file}.parquet")
    df.to_parquet(path, compression='gzip')

    return path


@task()
def write_gcs(path: Path) -> None:
    """Uploading local parquet file to GCS"""
    gcp_cloud_storage_bucket_block = GcsBucket.load("zoomcamp-gcs")
    gcp_cloud_storage_bucket_block.upload_from_path(from_path=path, to_path=path)

    return


@flow()
def etl_web_to_gcs(color: str = "yellow", year: int = 2021, month: int = 1) -> None:
    """The main ETL function"""
    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url = (f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/"
                   f"{color}/{dataset_file}.csv.gz")

    df = fetch(dataset_url)
    df_cleaned = clean(df)
    path = write_local(df_cleaned, color, dataset_file)
    write_gcs(path)


if __name__ == '__main__':
    etl_web_to_gcs()
