@echo off
REM ========================================
REM Spark Thrift Server Launcher for dbt
REM ========================================

REM Configure Spark location
set SPARK_HOME=D:\dowload\spark-4.1.1-bin-hadoop3
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot
set PYTHONPATH=%SPARK_HOME%\python;%PYTHONPATH%

REM Configure Iceberg + MinIO
set SPARK_SQL_CATALOG_ICEBERG=org.apache.iceberg.spark.SparkCatalog
set SPARK_SQL_CATALOG_ICEBERG_TYPE=hadoop
set SPARK_SQL_CATALOG_ICEBERG_WAREHOUSE=s3a://iceberg-warehouse
set SPARK_HADOOP_FS_S3A_ENDPOINT=http://localhost:9000
set SPARK_HADOOP_FS_S3A_ACCESS_KEY=minioadmin
set SPARK_HADOOP_FS_S3A_SECRET_KEY=minioadmin
set SPARK_HADOOP_FS_S3A_PATH_STYLE_ACCESS=true

REM Start Spark Thrift Server
echo ========================================
echo Starting Spark Thrift Server...
echo SPARK_HOME: %SPARK_HOME%
echo JAVA_HOME: %JAVA_HOME%
echo ========================================
echo.
echo Server will run on: localhost:10000
echo Press Ctrl+C to stop
echo.

cd /d "%SPARK_HOME%"

REM Launch Thrift Server via spark-submit
"%SPARK_HOME%\bin\spark-submit.cmd" ^
  --master local[*] ^
  --class org.apache.spark.sql.hive.thriftserver.HiveThriftServer2 ^
  --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog ^
  --conf spark.sql.catalog.iceberg.type=hadoop ^
  --conf spark.sql.catalog.iceberg.warehouse=s3a://iceberg-warehouse ^
  --conf spark.hadoop.fs.s3a.endpoint=http://localhost:9000 ^
  --conf spark.hadoop.fs.s3a.access.key=minioadmin ^
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin ^
  --conf spark.hadoop.fs.s3a.path.style.access=true ^
  "%SPARK_HOME%\jars\spark-hive-thriftserver_2.12-4.1.1.jar"

pause
