"""MapReduce thuan (khong dung Spark) mo phong map - shuffle - reduce bang multiprocessing.

Dung de minh hoa mo hinh MapReduce truoc khi chuyen sang Spark DataFrame o cac buoc sau.
Moi tien trinh con dong vai tro 1 "mapper": doc 1 khoi dong CSV, ap dung ham_map,
gop (combine) cuc bo theo khoa. Tien trinh chinh dong vai tro "reducer": gop
(shuffle + reduce) ket qua cuc bo tu tat ca mapper thanh ket qua cuoi cung.
"""
import csv
from collections import defaultdict
from multiprocessing import Pool


def doc_khoi_dong(duong_dan_csv, kich_thuoc_khoi=200_000):
    """Sinh lan luot cac khoi (list[dict]) tu file CSV co header."""
    with open(duong_dan_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        khoi = []
        for dong in reader:
            khoi.append(dong)
            if len(khoi) >= kich_thuoc_khoi:
                yield khoi
                khoi = []
        if khoi:
            yield khoi


def _map_va_gop_cuc_bo(tham_so):
    """Buoc MAP + combiner cuc bo, chay trong 1 tien trinh con."""
    khoi, ham_map = tham_so
    tong = defaultdict(float)
    dem = defaultdict(int)
    for dong in khoi:
        for khoa, gia_tri in ham_map(dong):
            tong[khoa] += gia_tri
            dem[khoa] += 1
    return tong, dem


def chay_mapreduce_tong(duong_dan_csv, ham_map, kich_thuoc_khoi=200_000, so_tien_trinh=4):
    """
    MapReduce cho bai toan tong hop dang SUM va COUNT theo khoa.

    ham_map: ham top-level (khong phai lambda/closure) nhan 1 dong (dict) va
             sinh ra cac cap (khoa, gia_tri: float). Phai dinh nghia o muc module
             de multiprocessing tren Windows pickle duoc.

    Tra ve: (tong theo khoa: dict, so_dong theo khoa: dict)
    """
    tong_cuoi = defaultdict(float)
    dem_cuoi = defaultdict(int)
    danh_sach_khoi = ((khoi, ham_map) for khoi in doc_khoi_dong(duong_dan_csv, kich_thuoc_khoi))
    with Pool(so_tien_trinh) as pool:
        for tong_cuc_bo, dem_cuc_bo in pool.imap_unordered(_map_va_gop_cuc_bo, danh_sach_khoi):
            for k, v in tong_cuc_bo.items():
                tong_cuoi[k] += v
            for k, v in dem_cuc_bo.items():
                dem_cuoi[k] += v
    return dict(tong_cuoi), dict(dem_cuoi)
