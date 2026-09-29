import os
import sys

from pyspark.sql import SparkSession

from cau_hinh import SPARK_DRIVER_MEMORY, SO_PARTITION_SHUFFLE, THU_MUC_TAM_SPARK


def tao_spark(ten_app="StoreSales_BigData", so_loi="*", driver_memory=SPARK_DRIVER_MEMORY):
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    THU_MUC_TAM_SPARK.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName(ten_app)
        .master(f"local[{so_loi}]")
        .config("spark.driver.memory", driver_memory)
        .config("spark.sql.shuffle.partitions", SO_PARTITION_SHUFFLE)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.local.dir", str(THU_MUC_TAM_SPARK))
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def dung_spark():
    spark = SparkSession.getActiveSession()
    if spark is not None:
        spark.stop()
