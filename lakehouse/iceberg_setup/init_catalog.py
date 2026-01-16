# -*- coding: utf-8 -*-
"""Initialize Apache Iceberg catalog with MinIO backend."""

import logging
import boto3
from typing import Dict

logger = logging.getLogger(__name__)


def initialize_iceberg_catalog() -> Dict:
    """Initialize Iceberg catalog with MinIO as object storage."""

    logger.info("Initializing Iceberg catalog...")

    # Configuration MinIO
    catalog_config = {
        'type': 'rest',
        'uri': 'http://minio:9000',
        'warehouse': 's3a://iceberg-warehouse',
        'client.region': 'us-east-1',
        'client.access-key-id': 'minioadmin',
        'client.secret-access-key': 'minioadmin',
    }

    # Create bucket if it doesn't exist
    s3_client = boto3.client(
        's3',
        endpoint_url='http://localhost:9010',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        region_name='us-east-1'
    )

    try:
        s3_client.head_bucket(Bucket='iceberg-warehouse')
        logger.info("[OK] Bucket 'iceberg-warehouse' already exists")
    except:
        s3_client.create_bucket(Bucket='iceberg-warehouse')
        logger.info("[OK] Created bucket 'iceberg-warehouse'")

    logger.info("[OK] Iceberg catalog initialized successfully")
    return catalog_config


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_iceberg_catalog()
