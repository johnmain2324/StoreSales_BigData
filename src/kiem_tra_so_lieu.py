"""Kiem tra so lieu cuoi cung truoc khi nop: doi chieu so dong o moi giai doan
(raw -> parquet -> processed -> dac trung -> du bao) va tinh hop le cua file du
bao nop bai. Chi doc metadata/parquet bang pandas+pyarrow, khong khoi dong Spark,
de chay nhanh nhu mot buoc kiem tra cuoi.
"""
import csv

import pandas as pd

from cau_hinh import (DATA_RAW, DATA_PARQUET, DATA_PROCESSED, OUT_TABLES, OUT_MODELS,
                       REPORT, FILE_DU_LIEU, HORIZON, tao_thu_muc)

SO_DONG_RAW_KY_VONG = {
    "train.csv": 3_000_888,
    "test.csv": 28_512,
    "stores.csv": 54,
    "oil.csv": 1_218,
    "holidays_events.csv": 350,
    "transactions.csv": 83_488,
    "sample_submission.csv": 28_512,
}

ket_qua = []
loi = []


def ghi(hang_muc, gia_tri, dat=None):
    ket_qua.append((hang_muc, str(gia_tri)))
    danh_dau = "" if dat is None else ("  [DAT]" if dat else "  [LOI]")
    print(f"{hang_muc:<45}: {gia_tri}{danh_dau}")
    if dat is False:
        loi.append(f"{hang_muc}: {gia_tri}")


def dem_dong_csv(duong_dan):
    with open(duong_dan, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.reader(f)) - 1  # tru dong header


def kiem_tra_raw():
    print("\n=== 1. DU LIEU THO (data/raw) ===")
    for ten_file in FILE_DU_LIEU:
        duong_dan = DATA_RAW / ten_file
        if not duong_dan.exists():
            ghi(f"raw/{ten_file}", "KHONG TON TAI", dat=False)
            continue
        so_dong = dem_dong_csv(duong_dan)
        ky_vong = SO_DONG_RAW_KY_VONG[ten_file]
        ghi(f"raw/{ten_file} (so dong)", so_dong, dat=(so_dong == ky_vong))


def kiem_tra_parquet():
    print("\n=== 2. PARQUET GOC (data/parquet) ===")
    for ten_file in FILE_DU_LIEU:
        ten = ten_file.replace(".csv", "")
        duong_dan = DATA_PARQUET / ten
        if not duong_dan.exists():
            ghi(f"parquet/{ten}", "KHONG TON TAI", dat=False)
            continue
        so_dong = len(pd.read_parquet(duong_dan, columns=[]))
        ky_vong = SO_DONG_RAW_KY_VONG[ten_file]
        ghi(f"parquet/{ten} (so dong)", so_dong, dat=(so_dong == ky_vong))


def kiem_tra_processed():
    print("\n=== 3. DU LIEU DA XU LY (data/processed) ===")
    duong_dan_train_sach = DATA_PROCESSED / "train_sach"
    duong_dan_test_sach = DATA_PROCESSED / "test_sach"
    if duong_dan_train_sach.exists():
        so_dong = len(pd.read_parquet(duong_dan_train_sach, columns=[]))
        ghi("processed/train_sach (so dong)", so_dong, dat=(so_dong == SO_DONG_RAW_KY_VONG["train.csv"]))
    else:
        ghi("processed/train_sach", "KHONG TON TAI", dat=False)

    if duong_dan_test_sach.exists():
        so_dong = len(pd.read_parquet(duong_dan_test_sach, columns=[]))
        ghi("processed/test_sach (so dong)", so_dong, dat=(so_dong == SO_DONG_RAW_KY_VONG["test.csv"]))
    else:
        ghi("processed/test_sach", "KHONG TON TAI", dat=False)

    duong_dan_train_dt = DATA_PROCESSED / "train_dac_trung"
    duong_dan_test_dt = DATA_PROCESSED / "test_dac_trung"
    if duong_dan_train_dt.exists():
        so_dong = len(pd.read_parquet(duong_dan_train_dt, columns=[]))
        # sau khi cat leading-zero, so dong phai it hon hoac bang so dong goc
        ghi("processed/train_dac_trung (so dong)", so_dong,
            dat=(0 < so_dong <= SO_DONG_RAW_KY_VONG["train.csv"]))
    else:
        ghi("processed/train_dac_trung", "KHONG TON TAI", dat=False)

    if duong_dan_test_dt.exists():
        so_dong = len(pd.read_parquet(duong_dan_test_dt, columns=[]))
        ghi("processed/test_dac_trung (so dong)", so_dong, dat=(so_dong == SO_DONG_RAW_KY_VONG["test.csv"]))
    else:
        ghi("processed/test_dac_trung", "KHONG TON TAI", dat=False)


def kiem_tra_mo_hinh():
    print("\n=== 4. MO HINH (outputs/models) ===")
    for ten in ["random_forest_pipeline", "random_forest_pipeline_kiem_dinh"]:
        duong_dan = OUT_MODELS / ten
        co_ton_tai = duong_dan.exists() and (duong_dan / "metadata").exists() and (duong_dan / "stages").exists()
        ghi(f"models/{ten}", "CO" if co_ton_tai else "KHONG TON TAI", dat=co_ton_tai)


def kiem_tra_du_bao_nop():
    print("\n=== 5. FILE DU BAO NOP BAI (outputs/tables/du_bao_test.csv) ===")
    duong_dan = OUT_TABLES / "du_bao_test.csv"
    if not duong_dan.exists():
        ghi("du_bao_test.csv", "KHONG TON TAI", dat=False)
        return

    df = pd.read_csv(duong_dan)
    ghi("du_bao_test.csv - cot", list(df.columns), dat=(list(df.columns) == ["id", "sales"]))
    ghi("du_bao_test.csv - so dong", len(df), dat=(len(df) == SO_DONG_RAW_KY_VONG["test.csv"]))
    ghi("du_bao_test.csv - id duy nhat", df["id"].is_unique, dat=df["id"].is_unique)
    ghi("du_bao_test.csv - khong null", df.isna().sum().sum() == 0, dat=(df.isna().sum().sum() == 0))
    ghi("du_bao_test.csv - sales khong am", (df["sales"] >= 0).all(), dat=bool((df["sales"] >= 0).all()))

    duong_dan_test_raw = DATA_RAW / "test.csv"
    if duong_dan_test_raw.exists():
        id_test_goc = set(pd.read_csv(duong_dan_test_raw, usecols=["id"])["id"])
        khop_id = set(df["id"]) == id_test_goc
        ghi("du_bao_test.csv - id khop voi test.csv goc", khop_id, dat=khop_id)


def kiem_tra_bao_cao():
    print("\n=== 6. BAO CAO (report/) ===")
    cac_file_docx = list(REPORT.glob("*.docx"))
    ghi("report/ - so file .docx", len(cac_file_docx), dat=(len(cac_file_docx) > 0))
    if cac_file_docx:
        ghi("report/ - file bao cao", cac_file_docx[0].name)


def luu_ket_qua():
    ghi("Ket luan", "DAT" if not loi else "CHUA DAT")
    duong_dan_ra = OUT_TABLES / "kiem_tra_so_lieu.csv"
    with open(duong_dan_ra, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["hang_muc", "gia_tri"])
        w.writerows(ket_qua)
    print("\nDa luu:", duong_dan_ra)


if __name__ == "__main__":
    tao_thu_muc()
    print(f"HORIZON du bao: {HORIZON} ngay")
    kiem_tra_raw()
    kiem_tra_parquet()
    kiem_tra_processed()
    kiem_tra_mo_hinh()
    kiem_tra_du_bao_nop()
    kiem_tra_bao_cao()
    print("\n=== KET QUA ===")
    luu_ket_qua()
    if loi:
        print("Cac van de can xu ly:")
        for x in loi:
            print(" -", x)
    else:
        print("Toan bo du lieu, mo hinh va bao cao nhat quan - san sang nop bai.")
