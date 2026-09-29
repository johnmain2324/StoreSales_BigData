"""Cac ham MAP cho bai toan tong hop doanh so tu data/raw/train.csv.

Moi ham nhan 1 dong CSV (dict, key la ten cot) va sinh ra cac cap (khoa, gia_tri)
de mapreduce_thuan.chay_mapreduce_tong cong don theo khoa.
"""


def map_theo_cua_hang(dong):
    yield dong["store_nbr"], float(dong["sales"])


def map_theo_nhom_hang(dong):
    yield dong["family"], float(dong["sales"])


def map_theo_thang(dong):
    thang = dong["date"][:7]  # yyyy-mm
    yield thang, float(dong["sales"])
