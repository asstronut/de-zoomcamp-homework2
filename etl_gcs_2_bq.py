from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect_gcp.bigquery import GcpCredentials


@task(retries=3)
def extract_from_gcs(color, year, month) -> Path:
    """Download trip data from GCS"""
    gcs_path = f"data/{color}/{color}_tripdata_{year}-{month:02}.parquet"
    gcs_block = GcsBucket.load("zoomcamp-gcs")
    gcs_block.get_directory(from_path=gcs_path, local_path=f"../{gcs_path}")

    return Path(f"../{gcs_path}")


@task()
def write_to_bq(df: pd.DataFrame) -> None:
    """Write transformed data into Big Query"""

    gcp_credentials_block = GcpCredentials.load("zoomcamp-gcs")

    df.to_gbq(
        destination_table='trips_data_all.yellow_trips',
        project_id='ny-rides-akbarattamimi',
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append"
    )


@flow(log_prints=True)
def etl_gcs_to_bq(color: str = "yellow", year: int = 2019, months: list[int] = [2, 3]):
    """Main ETL flows to load data from GCS into Big Query"""
    total = 0
    for month in months:
        path = extract_from_gcs(color, year, month)
        df = pd.read_parquet(path)
        total += len(df)
        write_to_bq(df)
    print(f"Total rows processed = {total:,}")


if __name__ == '__main__':
    etl_gcs_to_bq()
