from pathlib import Path

TEN_DE_TAI = "Phân tích Chuỗi thời gian (Time Series Analysis) trong Dự báo Nhu cầu Năng lượng / Tài chính"
PHU_DE = "Ứng dụng thuật toán Random Forest trên nền tảng Apache Spark với bộ dữ liệu Store Sales"

SEED = 42
HORIZON = 16

SPARK_DRIVER_MEMORY = "8g"
SO_PARTITION_SHUFFLE = 16

GOC = Path(__file__).resolve().parents[1]

DATA_RAW = GOC / "data" / "raw"
DATA_PARQUET = GOC / "data" / "parquet"
DATA_SAMPLE = GOC / "data" / "sample"
DATA_PROCESSED = GOC / "data" / "processed"

OUT_FIGURES = GOC / "outputs" / "figures"
OUT_TABLES = GOC / "outputs" / "tables"
OUT_MODELS = GOC / "outputs" / "models"
OUT_LOGS = GOC / "outputs" / "logs"

REPORT = GOC / "report"
THU_MUC_TAM_SPARK = GOC / "tmp_spark"

FILE_DU_LIEU = [
    "train.csv",
    "test.csv",
    "stores.csv",
    "oil.csv",
    "holidays_events.csv",
    "transactions.csv",
    "sample_submission.csv",
]


def tao_thu_muc():
    for p in [DATA_RAW, DATA_PARQUET, DATA_SAMPLE, DATA_PROCESSED,
              OUT_FIGURES, OUT_TABLES, OUT_MODELS, OUT_LOGS,
              REPORT, THU_MUC_TAM_SPARK, GOC / "notebooks", GOC / "src" / "mapreduce"]:
        p.mkdir(parents=True, exist_ok=True)
