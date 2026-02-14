# -*- coding: utf-8 -*-
"""
Spark Consumer via Thrift Server: Load Test Data → Iceberg Bronze

Connects to Spark Thrift Server (localhost:10000) and loads test data to Iceberg.

Usage:
    python kafka_to_bronze_thrift.py
"""

import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def load_data_via_sql():
    """Load test data to Iceberg via SQL (no PySpark needed)."""
    import pyodbc
    from sql.pyodbc import connect as pyodbc_connect

    logger.info("================================================================================")
    logger.info("Loading Test Data to Iceberg Bronze via Thrift Server")
    logger.info("================================================================================")

    try:
        # Connect to Spark Thrift Server
        logger.info("Connecting to Spark Thrift Server on localhost:10000...")

        # Use Hive ODBC connection
        conn = pyodbc.connect(
            'Driver={Hive};'
            'Host=localhost;'
            'Port=10000;'
            'AuthMech=0;'
        )

        cursor = conn.cursor()

        # Load events data
        logger.info("Loading events_raw data...")
        cursor.execute("""
            INSERT INTO TABLE default.events_raw
            VALUES
                ('event_001', 'user_001', 'purchase', 1674047400000),
                ('event_002', 'user_002', 'view', 1674047410000),
                ('event_003', 'user_003', 'click', 1674047420000)
        """)
        logger.info("[OK] events_raw loaded (3 rows)")

        # Load fraud data
        logger.info("Loading fraud_raw data...")
        cursor.execute("""
            INSERT INTO TABLE default.fraud_raw
            VALUES
                ('event_001', 0.45),
                ('event_002', 0.12),
                ('event_003', 0.78)
        """)
        logger.info("[OK] fraud_raw loaded (3 rows)")

        # Load inventory data
        logger.info("Loading inventory_raw data...")
        cursor.execute("""
            INSERT INTO TABLE default.inventory_raw
            VALUES
                ('SKU001', 'warehouse_01', -5, 95, 1674047400000),
                ('SKU002', 'warehouse_01', 10, 110, 1674047410000),
                ('SKU003', 'warehouse_02', -2, 48, 1674047420000)
        """)
        logger.info("[OK] inventory_raw loaded (3 rows)")

        # Commit changes
        conn.commit()

        # Verify data
        logger.info("================================================================================")
        logger.info("Verifying Bronze tables...")
        logger.info("================================================================================")

        cursor.execute("SELECT COUNT(*) FROM default.events_raw")
        events_count = cursor.fetchone()[0]
        logger.info(f"✅ events_raw: {events_count} rows")

        cursor.execute("SELECT COUNT(*) FROM default.fraud_raw")
        fraud_count = cursor.fetchone()[0]
        logger.info(f"✅ fraud_raw: {fraud_count} rows")

        cursor.execute("SELECT COUNT(*) FROM default.inventory_raw")
        inventory_count = cursor.fetchone()[0]
        logger.info(f"✅ inventory_raw: {inventory_count} rows")

        cursor.close()
        conn.close()

        logger.info("================================================================================")
        logger.info("[OK] Data loaded successfully!")
        logger.info("================================================================================")

    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        raise


def load_data_via_dbt():
    """Alternative: Load data using dbt seed command."""
    import subprocess

    logger.info("================================================================================")
    logger.info("Loading Test Data using dbt seeds")
    logger.info("================================================================================")

    try:
        # Create a CSV seed file with test data
        seed_dir = Path(__file__).parent.parent / "dbt_project" / "seeds"
        seed_dir.mkdir(exist_ok=True)

        # Create events seed
        events_csv = seed_dir / "events_raw_seed.csv"
        events_csv.write_text(
            "event_id,user_id,event_type,timestamp\n"
            "event_001,user_001,purchase,1674047400000\n"
            "event_002,user_002,view,1674047410000\n"
            "event_003,user_003,click,1674047420000\n"
        )
        logger.info(f"[OK] Created {events_csv}")

        # Create fraud seed
        fraud_csv = seed_dir / "fraud_raw_seed.csv"
        fraud_csv.write_text(
            "event_id,fraud_score\n"
            "event_001,0.45\n"
            "event_002,0.12\n"
            "event_003,0.78\n"
        )
        logger.info(f"[OK] Created {fraud_csv}")

        # Create inventory seed
        inventory_csv = seed_dir / "inventory_raw_seed.csv"
        inventory_csv.write_text(
            "product_id,warehouse_id,quantity_change,current_stock,timestamp\n"
            "SKU001,warehouse_01,-5,95,1674047400000\n"
            "SKU002,warehouse_01,10,110,1674047410000\n"
            "SKU003,warehouse_02,-2,48,1674047420000\n"
        )
        logger.info(f"[OK] Created {inventory_csv}")

        # Run dbt seed
        dbt_project_dir = Path(__file__).parent.parent / "dbt_project"
        logger.info(f"Running dbt seed in {dbt_project_dir}...")

        result = subprocess.run(
            ["dbt", "seed", "--profiles-dir", str(dbt_project_dir)],
            cwd=str(dbt_project_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("[OK] dbt seed completed successfully")
        else:
            logger.error(f"dbt seed failed: {result.stderr}")
            raise Exception(result.stderr)

        logger.info("================================================================================")
        logger.info("[OK] Data loaded via dbt seeds!")
        logger.info("================================================================================")

    except Exception as e:
        logger.error(f"Failed to load data via dbt: {str(e)}")
        raise


def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Use dbt seed method (most reliable)
    load_data_via_dbt()


if __name__ == "__main__":
    main()
