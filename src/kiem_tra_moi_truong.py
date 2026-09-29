import csv
import os
import platform
import shutil
import subprocess
import sys
import time
from importlib.metadata import version, PackageNotFoundError

from cau_hinh import GOC, OUT_TABLES, OUT_LOGS, DATA_PROCESSED, tao_thu_muc

THU_VIEN = ["pyspark", "pandas", "numpy", "pyarrow", "matplotlib", "seaborn",
            "statsmodels", "python-docx", "openpyxl", "ipykernel"]

ket_qua = []
loi = []


def ghi(hang_muc, gia_tri):
    ket_qua.append((hang_muc, str(gia_tri)))
    print(f"{hang_muc:<28}: {gia_tri}")


def ram_gb():
    try:
        if os.name == "nt":
            import ctypes

            class MEM(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]

            m = MEM()
            m.dwLength = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 1024 ** 3, 1)
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3, 1)
    except Exception:
        return "khong xac dinh"


def kiem_tra_he_thong():
    print("\n=== 1. HE THONG VA PYTHON ===")
    ghi("He dieu hanh", f"{platform.system()} {platform.release()} ({platform.version()})")
    ghi("So loi CPU (logic)", os.cpu_count())
    ghi("RAM (GB)", ram_gb())
    ghi("Python", platform.python_version())
    ghi("Python executable", sys.executable)
    trong_venv = sys.prefix != sys.base_prefix
    ghi("Dang chay trong venv", trong_venv)
    if not trong_venv:
        loi.append("Chua kich hoat .venv")
    if sys.version_info[:2] not in [(3, 10), (3, 11)]:
        loi.append("Python nen la 3.10 hoac 3.11")


def kiem_tra_java():
    print("\n=== 2. JAVA ===")
    ghi("JAVA_HOME", os.environ.get("JAVA_HOME", "CHUA DAT"))
    java = shutil.which("java")
    if java is None:
        ghi("Java", "KHONG TIM THAY")
        loi.append("Khong tim thay lenh java trong PATH")
        return
    out = subprocess.run([java, "-version"], capture_output=True, text=True)
    dong = [d for d in (out.stderr + out.stdout).splitlines() if d.strip() and not d.startswith("Picked up")]
    dong_dau = dong[0] if dong else "khong doc duoc"
    ghi("Java", dong_dau)
    if '"17' not in dong_dau and " 17" not in dong_dau:
        loi.append("Java khong phai phien ban 17")
    if "JAVA_HOME" not in os.environ:
        loi.append("Chua dat bien JAVA_HOME")


def kiem_tra_hadoop_windows():
    if os.name != "nt":
        return
    print("\n=== 3. HADOOP_HOME (Windows) ===")
    hh = os.environ.get("HADOOP_HOME")
    ghi("HADOOP_HOME", hh or "CHUA DAT")
    if not hh:
        loi.append("Chua dat bien HADOOP_HOME")
        return
    for f in ["winutils.exe", "hadoop.dll"]:
        co = os.path.isfile(os.path.join(hh, "bin", f))
        ghi(f, "CO" if co else "THIEU")
        if not co:
            loi.append(f"Thieu {f} trong {hh}\\bin")
    bin_trong_path = os.path.join(hh, "bin").lower() in os.environ.get("PATH", "").lower()
    ghi("%HADOOP_HOME%\\bin trong PATH", bin_trong_path)
    if not bin_trong_path:
        loi.append("Chua them %HADOOP_HOME%\\bin vao PATH")


def kiem_tra_thu_vien():
    print("\n=== 4. THU VIEN PYTHON ===")
    for tv in THU_VIEN:
        try:
            ghi(tv, version(tv))
        except PackageNotFoundError:
            ghi(tv, "CHUA CAI")
            loi.append(f"Chua cai {tv}")


def kiem_tra_spark():
    print("\n=== 5. SPARK VA PARQUET ===")
    try:
        from spark_session import tao_spark
    except Exception as e:
        loi.append(f"Khong import duoc pyspark: {e}")
        return

    t0 = time.time()
    spark = tao_spark("KiemTraMoiTruong")
    ghi("Thoi gian khoi dong Spark (s)", round(time.time() - t0, 2))
    sc = spark.sparkContext
    ghi("Spark version", spark.version)
    ghi("Master", sc.master)
    ghi("defaultParallelism", sc.defaultParallelism)
    ghi("spark.driver.memory", spark.conf.get("spark.driver.memory"))
    ghi("spark.sql.shuffle.partitions", spark.conf.get("spark.sql.shuffle.partitions"))
    ghi("Spark UI", sc.uiWebUrl)

    duong_dan = DATA_PROCESSED / "kiem_tra_parquet_tam"
    try:
        df = spark.range(0, 100000).withColumnRenamed("id", "so")
        tong_goc = df.selectExpr("sum(so)").first()[0]
        t0 = time.time()
        df.write.mode("overwrite").parquet(str(duong_dan))
        ghi("Ghi Parquet (s)", round(time.time() - t0, 2))
        df2 = spark.read.parquet(str(duong_dan))
        so_dong = df2.count()
        tong_doc = df2.selectExpr("sum(so)").first()[0]
        ghi("So dong doc lai", so_dong)
        dung = so_dong == 100000 and tong_doc == tong_goc
        ghi("Ghi/doc Parquet", "DAT" if dung else "SAI LECH")
        if not dung:
            loi.append("Du lieu Parquet doc lai khong khop")
        shutil.rmtree(duong_dan, ignore_errors=True)
    except Exception as e:
        ghi("Ghi/doc Parquet", "LOI")
        loi.append(f"Loi ghi/doc Parquet: {str(e).splitlines()[0]}")

    with open(OUT_LOGS / "cau_hinh_spark.txt", "w", encoding="utf-8") as f:
        for k, v in sorted(sc.getConf().getAll()):
            f.write(f"{k} = {v}\n")

    if "--giu" in sys.argv:
        input(f"\nMo {sc.uiWebUrl} (tab Environment, Executors) de chup anh. Nhan Enter de tat Spark...")
    spark.stop()


def luu_ket_qua():
    ghi("Ket luan", "DAT" if not loi else "CHUA DAT")
    with open(OUT_TABLES / "moi_truong.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["hang_muc", "gia_tri"])
        w.writerows(ket_qua)


if __name__ == "__main__":
    tao_thu_muc()
    print(f"Thu muc project: {GOC}")
    kiem_tra_he_thong()
    kiem_tra_java()
    kiem_tra_hadoop_windows()
    kiem_tra_thu_vien()
    kiem_tra_spark()
    print("\n=== KET QUA ===")
    luu_ket_qua()
    if loi:
        print("Cac van de can xu ly:")
        for x in loi:
            print(" -", x)
    else:
        print("Moi truong san sang cho Giai doan 2.")
    print(f"Da luu: {OUT_TABLES / 'moi_truong.csv'}")
    print(f"Da luu: {OUT_LOGS / 'cau_hinh_spark.txt'}")
