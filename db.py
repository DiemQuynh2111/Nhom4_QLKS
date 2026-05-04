import pyodbc
import pandas as pd


# =========================================================
# CẤU HÌNH KẾT NỐI SQL SERVER
# =========================================================

SERVER = r"LAPTOP-J63HK640"
DATABASE = "QLKS"
DRIVER = "ODBC Driver 17 for SQL Server"


# =========================================================
# KẾT NỐI DATABASE
# =========================================================

def get_connection(username: str, password: str):
    """
    Tạo kết nối SQL Server bằng tài khoản người dùng nhập ở màn hình đăng nhập.
    """
    conn_str = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def query_df(username: str, password: str, sql: str, params=None) -> pd.DataFrame:
    """
    Chạy SELECT hoặc EXEC có trả dữ liệu.
    """
    conn = get_connection(username, password)
    try:
        if params is None:
            params = []
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def execute_sql(username: str, password: str, sql: str, params=None):
    """
    Chạy lệnh SQL không cần trả bảng dữ liệu.
    """
    conn = get_connection(username, password)
    try:
        cursor = conn.cursor()
        if params is None:
            params = []
        cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def execute_proc(username: str, password: str, sql: str, params=None):
    """
    Gọi stored procedure không cần trả bảng.
    """
    execute_sql(username, password, sql, params)


def check_login_and_get_role(username: str, password: str):
    """
    Đăng nhập SQL Server, sau đó kiểm tra tài khoản đang thuộc role nghiệp vụ nào.
    Role cần có trong database:
    - role_ks_letan
    - role_ks_thungan
    - role_ks_ketoan
    - role_ks_quanly
    """
    sql = """
    SELECT
        ISNULL(IS_ROLEMEMBER('role_ks_letan'), 0) AS is_letan,
        ISNULL(IS_ROLEMEMBER('role_ks_thungan'), 0) AS is_thungan,
        ISNULL(IS_ROLEMEMBER('role_ks_ketoan'), 0) AS is_ketoan,
        ISNULL(IS_ROLEMEMBER('role_ks_quanly'), 0) AS is_quanly;
    """

    conn = get_connection(username, password)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()

        if row is None:
            return None

        if row.is_letan == 1:
            return "Lễ tân"

        if row.is_thungan == 1:
            return "Thu ngân"

        if row.is_ketoan == 1:
            return "Kế toán"

        if row.is_quanly == 1:
            return "Quản lý"

        return None

    finally:
        conn.close()
