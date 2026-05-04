# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import pyodbc
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from html import escape


# =========================================================
# 1. CẤU HÌNH KẾT NỐI SQL SERVER
# =========================================================

SERVER = r"LAPTOP-J63HK640"
DATABASE = "QLKS"
DRIVER = "ODBC Driver 18 for SQL Server"

# File nhỏ để chuyển thông tin đặt phòng vừa tạo từ tài khoản Lễ tân sang Thu ngân
# mà không cần cấp thêm quyền SELECT trực tiếp bảng gốc.
HANDOFF_FILE = Path(__file__).with_name("r5_last_booking.json")
APP_STATE_FILE = Path(__file__).with_name("r5_workflow_state.json")


# =========================================================
# 2. CẤU HÌNH ỨNG DỤNG
# =========================================================

APP_NAME = "Hotel ASR"
APP_SUBTITLE = "Hệ thống quản lý đặt phòng, hóa đơn và thanh toán khách sạn"

ROOM_IMAGES = [
    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1566665797739-1674de7a421a?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1590490360182-c33d57733427?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1571896349842-33c89424de2d?q=80&w=1200&auto=format&fit=crop",
]

# Ảnh phòng theo từng loại phòng.
# Dùng ảnh cố định theo tên loại phòng để card phòng không bị random/lệch hình.
ROOM_TYPE_IMAGES = {
    "standard": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop",
    "superior": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?q=80&w=1200&auto=format&fit=crop",
    "deluxe": "https://images.unsplash.com/photo-1590490360182-c33d57733427?q=80&w=1200&auto=format&fit=crop",
    "premier": "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?q=80&w=1200&auto=format&fit=crop",
    "executive": "https://images.unsplash.com/photo-1591088398332-8a7791972843?q=80&w=1200&auto=format&fit=crop",
    "junior suite": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=1200&auto=format&fit=crop",
    "suite": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?q=80&w=1200&auto=format&fit=crop",
    "family": "https://images.unsplash.com/photo-1560185007-cde436f6a4d0?q=80&w=1200&auto=format&fit=crop",
    "connecting room": "https://images.unsplash.com/photo-1560184897-ae75f418493e?q=80&w=1200&auto=format&fit=crop",
    "vip room": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?q=80&w=1200&auto=format&fit=crop",
}

ROLE_MENUS = {
    "Lễ tân": [
        "Trang chủ",
        "Khách hàng",
        "Tạo đặt phòng",
        "Tìm phòng trống",
        "Phân phòng",
        "Huỷ đặt phòng",
        "Check-in / Check-out",
    ],
    "Thu ngân": [
        "Trang chủ",
        "Lập hóa đơn",
        "Thêm dịch vụ",
        "Thanh toán",
        "Hóa đơn tổng hợp",
    ],
    "Kế toán": [
        "Trang chủ",
        "Công nợ",
        "Lịch sử thanh toán",
        "AuditLog",
    ],
    "Quản lý": [
        "Dashboard",
        "Báo cáo doanh thu",
        "Khách hàng thân thiết",
        "Hóa đơn tổng hợp",
        "Lịch sử thanh toán",
        "AuditLog",
    ],
}

ROLE_ICONS = {
    "Lễ tân": "🛎️",
    "Thu ngân": "💳",
    "Kế toán": "📒",
    "Quản lý": "👔",
}

ROLE_DESCRIPTIONS = {
    "Lễ tân": "Quản lý khách hàng, đặt phòng, kiểm tra phòng trống, phân phòng và check-in/check-out.",
    "Thu ngân": "Lập hóa đơn, thêm dịch vụ phát sinh và ghi nhận thanh toán.",
    "Kế toán": "Theo dõi công nợ, lịch sử thanh toán và AuditLog.",
    "Quản lý": "Theo dõi dashboard, báo cáo doanh thu, khách hàng thân thiết và dữ liệu hệ thống.",
}


# =========================================================
# 3. CẤU HÌNH STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Hotel ASR - Quản lý khách sạn",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# 4. CSS GIAO DIỆN
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: #f1f3f6;
    }

    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    #MainMenu,
    footer,
    header,
    div[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        display: none !important;
        height: 0 !important;
    }

    [data-testid="stSidebar"] {
        display: none;
    }

    .hotel-topbar {
        height: 76px;
        background: rgba(9, 35, 48, 0.96);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 34px;
        border-radius: 0 0 24px 24px;
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.25);
        margin-bottom: 0;
        position: relative;
        z-index: 5;
    }

    .hotel-logo {
        display: flex;
        align-items: baseline;
        gap: 7px;
        color: white;
        font-weight: 900;
        letter-spacing: -1px;
    }

    .hotel-logo .small {
        font-size: 20px;
    }

    .hotel-logo .big {
        font-size: 40px;
        font-style: italic;
        color: #ffffff;
    }

    .topbar-right {
        display: flex;
        align-items: center;
        gap: 14px;
        color: #e5e7eb;
        font-size: 13px;
    }

    .user-chip {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 999px;
        padding: 10px 14px;
        color: #fff;
        font-weight: 700;
    }

    .logout-note {
        color: #d1d5db;
        font-size: 12px;
    }

    .hero-resort {
        margin-top: -4px;
        min-height: 330px;
        border-radius: 0 0 32px 32px;
        background:
            linear-gradient(90deg, rgba(3, 24, 38, 0.75), rgba(3, 24, 38, 0.38)),
            url('https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1800&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        color: white;
        padding: 46px 42px 92px 42px;
        box-shadow: 0 20px 46px rgba(15, 23, 42, 0.18);
    }

    .hero-label {
        display: inline-flex;
        padding: 8px 13px;
        border-radius: 999px;
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.22);
        color: #f8fafc;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.4px;
        text-transform: uppercase;
        margin-bottom: 16px;
    }

    .hero-title {
        max-width: 800px;
        font-size: 48px;
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: -2px;
        margin: 0 0 16px 0;
    }

    .hero-subtitle {
        max-width: 760px;
        font-size: 16px;
        color: rgba(255,255,255,0.9);
        line-height: 1.7;
    }

    .search-panel {
        background: white;
        border-radius: 10px;
        padding: 24px 26px;
        margin: -54px auto 24px auto;
        position: relative;
        z-index: 10;
        box-shadow: 0 18px 42px rgba(15, 23, 42, 0.14);
        border: 1px solid rgba(226, 232, 240, 0.92);
    }

    .page-title-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin: 8px 0 18px 0;
    }

    .page-title {
        color: #24445c;
        font-weight: 900;
        font-size: 25px;
        letter-spacing: -0.6px;
        margin: 0;
    }

    .page-subtitle {
        color: #6b7280;
        font-size: 14px;
        margin-top: 6px;
    }

    .content-card {
        background: white;
        border-radius: 12px;
        padding: 26px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
        margin-bottom: 24px;
    }

    .section-title {
        color: #24445c;
        font-size: 18px;
        font-weight: 900;
        letter-spacing: -0.3px;
        margin: 0 0 18px 0;
        padding-bottom: 14px;
        border-bottom: 3px solid #20a7d8;
    }

    .metric-box {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.07);
        min-height: 116px;
    }

    .metric-icon {
        font-size: 24px;
        margin-bottom: 8px;
    }

    .metric-label {
        color: #64748b;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .3px;
    }

    .metric-value {
        color: #0f172a;
        font-size: 27px;
        font-weight: 900;
        letter-spacing: -1px;
        margin-top: 4px;
    }

    .room-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 28px;
        margin-top: 18px;
    }

    .room-card {
        background: white;
        overflow: hidden;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 12px 25px rgba(15, 23, 42, 0.08);
        transition: transform .2s ease, box-shadow .2s ease;
    }

    .room-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 18px 38px rgba(15, 23, 42, 0.13);
    }

    .room-img {
        height: 185px;
        min-height: 185px;
        display: block !important;
        background-color: #dbeafe;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: relative;
    }

    .room-img::after {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.05), rgba(15, 23, 42, 0.24));
    }

    .room-body {
        padding: 18px 18px 20px 18px;
    }

    .room-name {
        color: #425f75;
        font-weight: 900;
        font-size: 15px;
        margin-bottom: 10px;
    }

    .room-meta {
        color: #6b7280;
        font-size: 13px;
        line-height: 1.8;
        margin-bottom: 11px;
    }

    .status-row {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }

    .pill-green {
        background: #0f9f9a;
        color: white;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        padding: 6px 10px;
    }

    .pill-yellow {
        background: #ffd166;
        color: #ff3d2e;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        padding: 6px 10px;
    }

    .room-price {
        color: #ff3b30;
        font-size: 17px;
        font-weight: 900;
    }

    .login-page {
        min-height: 0;
        display: block;
        padding: 0;
    }

    .login-card {
        background: rgba(255,255,255,0.96);
        border-radius: 22px;
        border: 1px solid rgba(226, 232, 240, 0.9);
        padding: 34px;
        box-shadow: 0 28px 70px rgba(15, 23, 42, 0.22);
    }

    .login-brand {
        font-size: 38px;
        font-weight: 900;
        letter-spacing: -1.5px;
        color: #0f172a;
        margin-bottom: 8px;
    }

    .login-brand span {
        color: #b9896f;
        font-style: italic;
    }

    .login-desc {
        color: #64748b;
        line-height: 1.7;
        margin-bottom: 24px;
    }

    .login-visual {
        min-height: 520px;
        border-radius: 24px;
        background:
            linear-gradient(180deg, rgba(3, 24, 38, 0.2), rgba(3, 24, 38, 0.76)),
            url('https://images.unsplash.com/photo-1540541338287-41700207dee6?q=80&w=1600&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        padding: 34px;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        box-shadow: 0 24px 70px rgba(15, 23, 42, 0.2);
    }

    .login-visual h1 {
        font-size: 44px;
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: -2px;
        margin-bottom: 12px;
    }

    .login-visual p {
        color: rgba(255,255,255,0.9);
        line-height: 1.7;
    }

    .role-mini-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 22px;
    }

    .role-mini-card {
        background: rgba(255,255,255,0.13);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 14px;
        padding: 14px;
    }

    .role-mini-card b {
        color: white;
        font-size: 14px;
    }

    .role-mini-card div {
        color: rgba(255,255,255,0.78);
        font-size: 12px;
        margin-top: 4px;
    }

    .step-box {
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
    }

    .step-title {
        font-size: 15px;
        font-weight: 900;
        color: #24445c;
        margin-bottom: 6px;
    }

    .step-text {
        font-size: 13px;
        color: #64748b;
    }

    .stButton > button {
        border: 0 !important;
        border-radius: 3px !important;
        background: #bd8b70 !important;
        color: white !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        height: 44px;
        padding: 0 20px !important;
        box-shadow: 0 9px 18px rgba(189, 139, 112, 0.22);
    }

    .stButton > button:hover {
        background: #a9755b !important;
        color: white !important;
        transform: translateY(-1px);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        padding: 8px 18px;
        background: #f3f4f6;
        color: #334155;
        font-weight: 800;
    }
    /* Không dùng div:empty ở đây vì .room-img là div rỗng có background-image.
       Nếu ẩn div rỗng, ảnh phòng sẽ biến mất. */

    .content-card:empty,
    .search-panel:empty,
    .hotel-card:empty,
    .login-card:empty,
    .step-box:empty {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        box-shadow: none !important;
}
    .stTabs [aria-selected="true"] {
        background: #24445c !important;
        color: white !important;
    }

    @media (max-width: 980px) {
        .room-grid {
            grid-template-columns: 1fr;
        }
        .hero-title {
            font-size: 34px;
        }
        .hotel-topbar {
            padding: 0 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 5. DATABASE FUNCTIONS
# =========================================================

# =========================================================
# 5. DATABASE FUNCTIONS
# =========================================================

def get_connection(username: str, password: str):
    conn_str = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=8)


def query_df(username: str, password: str, sql: str, params=None) -> pd.DataFrame:
    """
    Chạy SELECT hoặc EXEC có trả dữ liệu.
    Có COMMIT để các procedure INSERT/UPDATE kèm SELECT OUTPUT không bị rollback.
    """
    if params is None:
        params = []

    conn = get_connection(username, password)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)

        last_df = pd.DataFrame()

        while True:
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                last_df = pd.DataFrame.from_records(
                    [tuple(row) for row in rows],
                    columns=columns
                )

            if not cursor.nextset():
                break

        conn.commit()
        return last_df

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def execute_sql(username: str, password: str, sql: str, params=None):
    if params is None:
        params = []

    conn = get_connection(username, password)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def execute_sql_return_df(username: str, password: str, sql: str, params=None) -> pd.DataFrame:
    """
    Chạy batch SQL gồm DECLARE/EXEC/SELECT.
    Dùng cho procedure có OUTPUT ID.
    """
    return query_df(username, password, sql, params)


def check_login_and_get_role(username: str, password: str):
    """
    Tự nhận diện role theo tài khoản SQL Server.
    Hỗ trợ cả role hiện tại của bạn và role_ks_*.
    """
    sql = """
    SELECT
        CASE WHEN
            ISNULL(IS_ROLEMEMBER('role_LeTan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_letan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_letan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_LeTan'), 0) = 1
        THEN 1 ELSE 0 END AS is_letan,

        CASE WHEN
            ISNULL(IS_ROLEMEMBER('role_thungan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ThuNgan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_thungan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_ThuNgan'), 0) = 1
        THEN 1 ELSE 0 END AS is_thungan,

        CASE WHEN
            ISNULL(IS_ROLEMEMBER('role_ketoan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_KeToan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_ketoan'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_KeToan'), 0) = 1
        THEN 1 ELSE 0 END AS is_ketoan,

        CASE WHEN
            ISNULL(IS_ROLEMEMBER('role_quanly'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_QuanLy'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_quanly'), 0) = 1 OR
            ISNULL(IS_ROLEMEMBER('role_ks_QuanLy'), 0) = 1
        THEN 1 ELSE 0 END AS is_quanly;
    """

    conn = get_connection(username, password)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()

        if row is None:
            return None

        is_letan = int(row[0])
        is_thungan = int(row[1])
        is_ketoan = int(row[2])
        is_quanly = int(row[3])

        if is_quanly == 1:
            return "Quản lý"

        if is_ketoan == 1:
            return "Kế toán"

        if is_thungan == 1:
            return "Thu ngân"

        if is_letan == 1:
            return "Lễ tân"

        return None

    finally:
        conn.close()

# =========================================================
# 6. SESSION STATE
# =========================================================

def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "password": "",
        "role": "",
        "active_menu": "",
        "last_room_search": None,
        "last_available_rooms": pd.DataFrame(),
        "last_created_booking": None,
        "last_assigned_room": None,
        "last_created_invoice": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session()


# =========================================================
# 7. HELPER FUNCTIONS
# =========================================================

def rerun_app():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


def get_auth():
    return st.session_state["username"], st.session_state["password"], st.session_state["role"]


def db_query(sql: str, params=None) -> pd.DataFrame:
    username, password, _ = get_auth()
    return query_df(username, password, sql, params)


def db_exec(sql: str, params=None):
    username, password, _ = get_auth()
    return execute_sql(username, password, sql, params)


def db_exec_return_df(sql: str, params=None) -> pd.DataFrame:
    username, password, _ = get_auth()
    return execute_sql_return_df(username, password, sql, params)


def safe_money(value):
    try:
        if value is None or pd.isna(value):
            value = 0
        return f"{float(value):,.0f}đ"
    except Exception:
        return "0đ"


def safe_text(value, default=""):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    return str(value)


def escape_text(value):
    return escape(safe_text(value))


def safe_dataframe(df: pd.DataFrame, height=420):
    if df is None or df.empty:
        st.info("Không có dữ liệu để hiển thị.")
    else:
        st.dataframe(df, use_container_width=True, height=height)


def first_existing(row_dict, candidates, default=""):
    for col in candidates:
        if col in row_dict and pd.notna(row_dict[col]):
            return row_dict[col]
    return default


def metric_card(icon, label, value):
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{escape_text(label)}</div>
            <div class="metric-value">{escape_text(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def content_card_start(title=None):
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"<div class='section-title'>{escape_text(title)}</div>", unsafe_allow_html=True)


def content_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def page_title(title, subtitle=""):
    st.markdown(
        f"""
        <div class="page-title-row">
            <div>
                <div class="page-title">{escape_text(title)}</div>
                <div class="page-subtitle">{escape_text(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def json_safe(value):
    """Chuyển date/datetime và kiểu số của pandas về dạng ghi được vào JSON."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        if hasattr(value, "item"):
            return value.item()
    except Exception:
        pass
    return value


def save_workflow_state(**updates):
    """Lưu trạng thái luồng nghiệp vụ ra file để đổi role vẫn dùng tiếp được."""
    try:
        state = {}
        if APP_STATE_FILE.exists():
            old = json.loads(APP_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(old, dict):
                state.update(old)

        for key, value in updates.items():
            if isinstance(value, pd.DataFrame):
                state[key] = value.head(200).applymap(json_safe).to_dict("records")
            elif isinstance(value, dict):
                state[key] = {k: json_safe(v) for k, v in value.items()}
            else:
                state[key] = json_safe(value)

        state["updated_at"] = datetime.now().isoformat(timespec="seconds")
        APP_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        # Giữ file cũ để tương thích với bản trước.
        if "last_created_booking" in updates:
            HANDOFF_FILE.write_text(
                json.dumps(state.get("last_created_booking", {}), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
    except Exception:
        pass


def load_workflow_state():
    """Đọc trạng thái luồng nghiệp vụ đã lưu."""
    try:
        if APP_STATE_FILE.exists():
            data = json.loads(APP_STATE_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def load_saved_value(key, default=None):
    """Lấy giá trị từ session trước, nếu chưa có thì lấy từ file workflow."""
    current = st.session_state.get(key)
    if key == "last_available_rooms":
        if isinstance(current, pd.DataFrame) and not current.empty:
            return current
    elif current:
        return current

    state = load_workflow_state()
    saved = state.get(key, default)

    if key == "last_available_rooms" and isinstance(saved, list):
        saved = pd.DataFrame(saved)

    if saved is not None:
        st.session_state[key] = saved

    return saved


def save_booking_handoff(data: dict):
    """Tương thích tên hàm cũ: lưu đặt phòng gần nhất."""
    save_workflow_state(last_created_booking=data)


def load_booking_handoff():
    """Tương thích tên hàm cũ: đọc đặt phòng gần nhất."""
    data = load_saved_value("last_created_booking", None)
    return data if isinstance(data, dict) else None


def parse_iso_date(value, fallback):
    try:
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value.strip():
            return date.fromisoformat(value[:10])
    except Exception:
        pass
    return fallback


def logout():
    for key in ["logged_in", "username", "password", "role", "active_menu"]:
        if key in st.session_state:
            del st.session_state[key]
    init_session()
    rerun_app()


def generate_code(prefix):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}"


def nullable_int_from_text(value):
    value = str(value).strip()
    if value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def text_to_nullable_int(value):
    return nullable_int_from_text(value)


def is_signature_error(error):
    msg = str(error).lower()
    signature_keywords = [
        "too many arguments",
        "too many parameters",
        "expects parameter",
        "not a parameter",
        "has no parameter",
        "parameter",
    ]
    return any(k in msg for k in signature_keywords)


def try_exec_with_fallback(sql_main, params_main, sql_fallback=None, params_fallback=None):
    try:
        db_exec(sql_main, params_main)
        return
    except Exception as main_error:
        if sql_fallback is None:
            raise main_error

        if is_signature_error(main_error):
            db_exec(sql_fallback, params_fallback if params_fallback is not None else params_main)
            return

        raise main_error




# =========================================================
# 7B. DANH MỤC HIỂN THỊ AN TOÀN
# =========================================================
# Các role nghiệp vụ trong R3 không được SELECT trực tiếp bảng danh mục.
# Vì vậy app ưu tiên lấy tên từ view/bảng nếu tài khoản có quyền; nếu không có
# quyền thì dùng danh sách gợi ý bên dưới để người dùng không phải nhập ID mù.

ROOM_TYPE_FALLBACK = {
    1: "Standard",
    2: "Superior",
    3: "Deluxe",
    4: "Premier",
    5: "Executive",
    6: "Junior Suite",
    7: "Suite",
    8: "Family",
    9: "Connecting Room",
    10: "VIP Room",
}

SOURCE_FALLBACK = {
    1: "Lễ tân / Trực tiếp",
    2: "Website",
    3: "Booking.com",
    4: "Agoda",
    5: "Traveloka",
    6: "Expedia",
    7: "Công ty / Corporate",
    8: "Đại lý du lịch",
    9: "Facebook / Social",
    10: "Điện thoại",
}

PAYMENT_METHOD_FALLBACK = {
    1: "Tiền mặt",
    2: "Chuyển khoản",
    3: "QR Banking",
    4: "Thẻ tín dụng",
    5: "Thẻ ghi nợ",
    6: "Ví điện tử",
    7: "VNPay",
    8: "Momo",
    9: "ZaloPay",
    10: "Khác",
}

SERVICE_FALLBACK = {
    1: 'Nước suối Lavie 500ml',
    2: 'Nước suối Aquafina 500ml',
    3: 'Coca-Cola lon',
    4: 'Pepsi lon',
    5: 'Bia Heineken lon',
    6: 'Bia Tiger lon',
    7: 'Mì ly',
    8: 'Snack khoai tây',
    9: 'Chocolate thanh',
    10: 'Cà phê phin',
    11: 'Cà phê sữa đá',
    12: 'Nước cam ép',
    13: 'Ăn sáng buffet',
    14: 'Bữa trưa set menu',
    15: 'Bữa tối set menu',
    16: 'Giặt áo sơ mi',
    17: 'Giặt quần dài',
    18: 'Giặt váy',
    19: 'Giặt áo khoác',
    20: 'Ủi áo sơ mi',
    21: 'Ủi quần dài',
    22: 'Spa thư giãn 60 phút',
    23: 'Massage chân 30 phút',
    24: 'Massage body 60 phút',
    25: 'Xông hơi khô',
    26: 'Đưa đón sân bay một chiều',
    27: 'Đưa đón sân bay hai chiều',
    28: 'Thuê xe máy một ngày',
    29: 'Thuê ô tô 4 chỗ một ngày',
    30: 'Tour city nửa ngày',
    31: 'Tour Hội An một ngày',
    32: 'Tour Bà Nà Hills một ngày',
    33: 'Tour Cù Lao Chàm một ngày',
    34: 'Thuê phòng họp nửa ngày',
    35: 'Thuê phòng họp một ngày',
    36: 'Trà nước phòng họp',
    37: 'Giường phụ một đêm',
    38: 'Phụ thu trẻ em',
    39: 'Phụ thu nhận phòng sớm',
    40: 'Phụ thu trả phòng trễ',
    41: 'In tài liệu A4',
    42: 'Photocopy A4',
    43: 'Dịch vụ gửi hành lý',
    44: 'Trang trí phòng sinh nhật',
    45: 'Hoa tươi trong phòng',
    46: 'Nước dừa tươi',
    47: 'Sinh tố xoài',
    48: 'Sinh tố bơ',
    49: 'Mì xào hải sản',
    50: 'Cơm chiên hải sản',
    51: 'Bánh mì ốp la',
    52: 'Bánh ngọt',
    53: 'Trà đào cam sả',
    54: 'Trà gừng mật ong',
    55: 'Rượu vang mini',
    56: 'Bộ dao cạo râu',
    57: 'Bàn chải đánh răng',
    58: 'Sạc điện thoại cho thuê',
    59: 'Nôi em bé',
    60: 'Xe lăn hỗ trợ',
}

SERVICE_PRICE_FALLBACK = {
    1: 15000.0,
    2: 15000.0,
    3: 25000.0,
    4: 25000.0,
    5: 45000.0,
    6: 40000.0,
    7: 30000.0,
    8: 35000.0,
    9: 30000.0,
    10: 35000.0,
    11: 40000.0,
    12: 60000.0,
    13: 180000.0,
    14: 250000.0,
    15: 300000.0,
    16: 35000.0,
    17: 45000.0,
    18: 50000.0,
    19: 70000.0,
    20: 25000.0,
    21: 30000.0,
    22: 550000.0,
    23: 250000.0,
    24: 650000.0,
    25: 180000.0,
    26: 250000.0,
    27: 450000.0,
    28: 180000.0,
    29: 900000.0,
    30: 450000.0,
    31: 850000.0,
    32: 1200000.0,
    33: 950000.0,
    34: 1500000.0,
    35: 2500000.0,
    36: 300000.0,
    37: 350000.0,
    38: 200000.0,
    39: 300000.0,
    40: 400000.0,
    41: 5000.0,
    42: 3000.0,
    43: 50000.0,
    44: 650000.0,
    45: 400000.0,
    46: 45000.0,
    47: 65000.0,
    48: 70000.0,
    49: 120000.0,
    50: 130000.0,
    51: 60000.0,
    52: 45000.0,
    53: 55000.0,
    54: 50000.0,
    55: 250000.0,
    56: 35000.0,
    57: 25000.0,
    58: 30000.0,
    59: 120000.0,
    60: 100000.0,
}

ROOM_TYPE_PRICE_FALLBACK = {
    1: 600000.0,    # Standard
    2: 750000.0,    # Superior
    3: 950000.0,    # Deluxe
    4: 1150000.0,   # Premier
    5: 1400000.0,   # Executive
    6: 1600000.0,   # Junior Suite
    7: 1900000.0,   # Suite
    8: 2100000.0,   # Family
    9: 2300000.0,   # Connecting Room
    10: 2800000.0,  # VIP Room
}


ROOM_TYPE_CAPACITY_FALLBACK = {
    # Khớp cột suc_chua_toi_da trong dữ liệu LoaiPhong R2.
    1: 2,
    2: 2,
    3: 3,
    4: 3,
    5: 3,
    6: 4,
    7: 4,
    8: 5,
    9: 5,
    10: 4,
}


def make_fallback_options(items: dict[int, str]):
    return {f"{k} - {v}": int(k) for k, v in items.items()}


def make_reference_options(sql: str, value_col: str, label_cols: list[str], fallback_items: dict[int, str]):
    """
    Thử lấy danh mục thật nếu có quyền SELECT. Nếu bị chặn bởi R3 thì dùng fallback.
    Return: (options, source_note)
    """
    try:
        df = db_query(sql)
        if df is not None and not df.empty and value_col in df.columns:
            options = {}
            for _, row in df.iterrows():
                value = int(row[value_col])
                labels = []
                for col in label_cols:
                    if col in df.columns:
                        labels.append(str(row[col]))
                label = " - ".join(labels) if labels else f"{value}"
                options[label] = value
            if options:
                return options, "actual"
    except Exception:
        pass

    return make_fallback_options(fallback_items), "fallback"


def select_reference(label: str, sql: str, value_col: str, label_cols: list[str], fallback_items: dict[int, str], help_text: str = "", default_id=None):
    options, source = make_reference_options(sql, value_col, label_cols, fallback_items)
    labels = list(options.keys())

    selected_index = 0
    if default_id is not None:
        try:
            default_id = int(default_id)
            for i, option_label in enumerate(labels):
                if int(options[option_label]) == default_id:
                    selected_index = i
                    break
        except Exception:
            selected_index = 0

    selected_label = st.selectbox(label, labels, index=selected_index, help=help_text)
    selected_id = options[selected_label]



    return selected_id, selected_label


def parse_nullable_decimal(text_value: str):
    value = str(text_value).strip().replace(",", "")
    if value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def default_price_for_room_type(room_type_id: int):
    return float(ROOM_TYPE_PRICE_FALLBACK.get(int(room_type_id), 600000.0))


def default_price_for_room_name(room_type_name):
    """Tìm giá fallback theo tên loại phòng khi kết quả procedure chỉ trả ten_loai_phong.
    Hàm này tránh lỗi NameError ở màn hình Trang chủ/Tìm phòng trống.
    """
    name = safe_text(room_type_name).strip().lower()
    name = name.replace("_", " ").replace("-", " ")
    name = " ".join(name.split())

    for rid, rname in ROOM_TYPE_FALLBACK.items():
        rname_norm = rname.strip().lower()
        if name == rname_norm or rname_norm in name or name in rname_norm:
            return default_price_for_room_type(rid)

    # Một số tên tiếng Việt/cách viết có thể xuất hiện trong dữ liệu hoặc view.
    alias_map = {
        "standard": 1,
        "superior": 2,
        "deluxe": 3,
        "premier": 4,
        "executive": 5,
        "junior suite": 6,
        "suite": 7,
        "family": 8,
        "connecting": 9,
        "vip": 10,
    }
    for key, rid in alias_map.items():
        if key in name:
            return default_price_for_room_type(rid)

    return 600000.0



def normalize_room_type_name(room_type_name):
    name = safe_text(room_type_name).strip().lower()
    name = name.replace("_", " ").replace("-", " ")
    return " ".join(name.split())


def get_room_image_for_type(room_type_name, idx=0):
    """Chọn hình phù hợp với tên loại phòng trả về từ SQL Server.

    Ưu tiên match chính xác Junior Suite trước Suite để không bị nhầm.
    """
    name = normalize_room_type_name(room_type_name)

    match_order = [
        "connecting room",
        "junior suite",
        "vip room",
        "standard",
        "superior",
        "deluxe",
        "premier",
        "executive",
        "family",
        "suite",
    ]

    for key in match_order:
        if name == key or key in name or name in key:
            return ROOM_TYPE_IMAGES.get(key, ROOM_IMAGES[idx % len(ROOM_IMAGES)])

    return ROOM_IMAGES[idx % len(ROOM_IMAGES)]


def default_capacity_for_room_type(room_type_id: int):
    return int(ROOM_TYPE_CAPACITY_FALLBACK.get(int(room_type_id), 2))


def get_room_type_meta(room_type_id: int):
    """Lấy sức chứa và giá loại phòng từ view an toàn nếu có; nếu không thì dùng fallback."""
    room_type_id = int(room_type_id)
    meta = {
        "suc_chua_toi_da": default_capacity_for_room_type(room_type_id),
        "gia_niem_yet": default_price_for_room_type(room_type_id),
    }
    try:
        df = db_query(
            """
            SELECT TOP 1 suc_chua_toi_da, gia_niem_yet
            FROM dbo.v_R5_LoaiPhong
            WHERE loai_phong_id = ?
            """,
            [room_type_id],
        )
        if df is not None and not df.empty:
            if "suc_chua_toi_da" in df.columns and pd.notna(df.iloc[0].get("suc_chua_toi_da")):
                meta["suc_chua_toi_da"] = int(df.iloc[0]["suc_chua_toi_da"])
            if "gia_niem_yet" in df.columns and pd.notna(df.iloc[0].get("gia_niem_yet")):
                meta["gia_niem_yet"] = float(df.iloc[0]["gia_niem_yet"])
    except Exception:
        pass
    return meta


def get_service_catalog():
    """Trả về danh mục dịch vụ có giá để thu ngân nhìn thấy trước khi thêm."""
    rows = []
    try:
        df = db_query(
            """
            SELECT dich_vu_id, ten_dich_vu, gia_niem_yet
            FROM dbo.v_R5_DichVu
            ORDER BY dich_vu_id
            """
        )
        if df is not None and not df.empty and {"dich_vu_id", "ten_dich_vu"}.issubset(set(df.columns)):
            for _, row in df.iterrows():
                service_id = int(row["dich_vu_id"])
                price = row.get("gia_niem_yet", SERVICE_PRICE_FALLBACK.get(service_id, 0.0))
                rows.append({
                    "dich_vu_id": service_id,
                    "ten_dich_vu": safe_text(row.get("ten_dich_vu")),
                    "gia_niem_yet": float(price if pd.notna(price) else 0.0),
                    "source": "actual",
                })
    except Exception:
        rows = []

    if not rows:
        for service_id, name in SERVICE_FALLBACK.items():
            rows.append({
                "dich_vu_id": int(service_id),
                "ten_dich_vu": name,
                "gia_niem_yet": float(SERVICE_PRICE_FALLBACK.get(service_id, 0.0)),
                "source": "fallback",
            })
    return rows


def count_available_rooms_for_range(start_date: date, end_date: date):
    """Đếm phòng trống bằng procedure, không SELECT trực tiếp bảng Phong."""
    total = 0
    has_any = False
    for room_type_id in ROOM_TYPE_FALLBACK.keys():
        try:
            df = db_query(
                """
                EXEC dbo.sp_R2_KiemTraPhongTrong
                    @loai_phong_id = ?,
                    @ngay_den = ?,
                    @ngay_di = ?
                """,
                [int(room_type_id), start_date, end_date],
            )
            if df is not None:
                total += len(df)
                has_any = True
        except Exception:
            continue
    return total if has_any else None


# =========================================================
# 8. DATA LOADERS QUA VIEW
# =========================================================

def load_customers_masked():
    return db_query(
        """
        SELECT khach_hang_id, ho_ten
        FROM dbo.v_R3_KhachHang_Masked
        ORDER BY khach_hang_id DESC
        """
    )


def load_recent_invoices():
    return db_query(
        """
        SELECT TOP 300 *
        FROM dbo.v_R2_HoaDonTongHop
        ORDER BY ngay_lap DESC
        """
    )


# =========================================================
# 9. VISUAL COMPONENTS
# =========================================================

def render_login_page():
    st.markdown("<div class='login-page'>", unsafe_allow_html=True)

    left, right = st.columns([0.95, 1.05], gap="large")

    with left:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-brand'>Hotel <span>ASR</span></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="login-desc">
                Đăng nhập bằng tài khoản SQL Server. Hệ thống sẽ tự nhận diện vai trò
                và chỉ hiển thị những chức năng đã được phân quyền.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", placeholder="login_letan")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            submit = st.form_submit_button("Đăng nhập")

            if submit:
                if not username.strip() or not password.strip():
                    st.warning("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
                else:
                    try:
                        role = check_login_and_get_role(username.strip(), password)

                        if role is None:
                            st.error("Đăng nhập được nhưng tài khoản chưa được gán role nghiệp vụ trong database.")
                        else:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username.strip()
                            st.session_state["password"] = password
                            st.session_state["role"] = role
                            st.session_state["active_menu"] = ROLE_MENUS[role][0]
                            st.success(f"Đăng nhập thành công với vai trò: {role}")
                            rerun_app()

                    except Exception as e:
                        st.error(f"Đăng nhập thất bại: {e}")

        with st.expander("Tài khoản demo"):
            st.write("Lễ tân: `login_letan` / `letan123`")
            st.write("Thu ngân: `login_thungan` / `thungan123`")
            st.write("Kế toán: `login_ketoan` / `ketoan123`")
            st.write("Quản lý: `login_quanly` / `quanly123`")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            """
            <div class="login-visual">
                <div class="hero-label">DATABASE APPLICATION</div>
                <h1>Quản lý khách sạn hiện đại trên SQL Server</h1>
                <div class="role-mini-grid">
                    <div class="role-mini-card"><b>🛎️ Lễ tân</b><div>Khách hàng, đặt phòng, check-in</div></div>
                    <div class="role-mini-card"><b>💳 Thu ngân</b><div>Hóa đơn, dịch vụ, thanh toán</div></div>
                    <div class="role-mini-card"><b>📒 Kế toán</b><div>Công nợ, thanh toán, AuditLog</div></div>
                    <div class="role-mini-card"><b>👔 Quản lý</b><div>Dashboard, doanh thu, báo cáo</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_topbar():
    role = st.session_state["role"]
    username = st.session_state["username"]

    st.markdown(
        f"""
        <div class="hotel-topbar">
            <div class="hotel-logo">
                <span class="small">Hotel</span>
                <span class="big">ASR</span>
            </div>
            <div class="topbar-right">
                <span class="user-chip">{ROLE_ICONS.get(role, "👤")} {escape_text(role)} · {escape_text(username)}</span>
                <span class="logout-note">SQL Server: {escape_text(DATABASE)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    role = st.session_state["role"]
    st.markdown(
        f"""
        <div class="hero-resort">
            <div class="hero-label">{escape_text(role)}</div>
            <div class="hero-title">{escape_text(APP_SUBTITLE)}</div>
            <div class="hero-subtitle">
                {escape_text(ROLE_DESCRIPTIONS.get(role, ""))}
                Ứng dụng không truy vấn trực tiếp bảng gốc nếu role chưa được cấp quyền;
                các thao tác chính đi qua stored procedure và view.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_nav():
    role = st.session_state["role"]
    menus = ROLE_MENUS[role]

    if st.session_state.get("active_menu") not in menus:
        st.session_state["active_menu"] = menus[0]

    current_index = menus.index(st.session_state["active_menu"])

    selected = st.radio(
        "Chức năng",
        menus,
        index=current_index,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.session_state["active_menu"] = selected

    col1, col2 = st.columns([1, 0.14])
    with col2:
        if st.button("Đăng xuất", use_container_width=True):
            logout()

    return selected


def render_room_cards(df: pd.DataFrame, title="Căn hộ / phòng đề xuất", limit=6):
    """Hiển thị phòng dạng card.

    Lưu ý: Không dùng chuỗi HTML nhiều dòng có thụt lề 4 spaces vì Markdown sẽ hiểu là code block
    và in nguyên thẻ <div> ra màn hình.
    """
    st.markdown("<div class='content-card room-card-wrapper'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-title'>{escape_text(title)}</div>", unsafe_allow_html=True)

    if df is None or df.empty:
        st.info("Không có phòng để hiển thị.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    rows = df.head(limit).to_dict("records")
    html_parts = ["<div class='room-grid'>"]

    for idx, row in enumerate(rows):
        room_name = first_existing(row, ["ma_phong", "ten_phong", "phong_id"], f"Phòng {idx + 1}")
        room_type = first_existing(row, ["ten_loai_phong", "loai_phong", "LoaiPhong"], "Loại phòng")
        floor = first_existing(row, ["tang", "floor"], "Đang cập nhật")
        status = first_existing(row, ["trang_thai_theo_ngay", "trang_thai", "status"], "Còn phòng")
        price = first_existing(row, ["gia_niem_yet", "don_gia_ap_dung", "gia"], default_price_for_room_name(room_type))
        phong_id = first_existing(row, ["phong_id"], "")
        img = get_room_image_for_type(room_type, idx)

        room_title = f"Phòng {room_name}"
        if phong_id:
            room_title = f"Phòng {room_name} · ID {phong_id}"

        html_parts.append(
            "<div class='room-card'>"
            f"<div class='room-img' style=\"background-image:url('{img}')\"></div>"
            "<div class='room-body'>"
            f"<div class='room-name'>{escape_text(room_title)}</div>"
            "<div class='room-meta'>"
            f"Loại: <b>{escape_text(room_type)}</b><br>"
            f"Tầng: <b>{escape_text(floor)}</b>"
            "</div>"
            "<div class='status-row'>"
            f"<span class='pill-green'>{escape_text(status if status else 'Còn phòng')}</span>"
            "<span class='pill-yellow'>Chưa VAT</span>"
            "</div>"
            "<div class='room-meta'>ĐỀ XUẤT</div>"
            f"<div class='room-price'>{safe_money(price)}</div>"
            "</div>"
            "</div>"
        )

    html_parts.append("</div>")
    html = "".join(html_parts)
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_search_panel():
    st.markdown("<div class='search-panel'>", unsafe_allow_html=True)

    with st.form("quick_room_search"):
        col1, col2, col3, col4, col5 = st.columns([1.35, 1, 1, 1.6, 0.9])

        with col1:
            loai_phong_id, loai_phong_label = select_reference(
                label="Loại phòng",
                sql="""
                    SELECT loai_phong_id, ten_loai_phong
                    FROM dbo.v_R5_LoaiPhong
                    ORDER BY loai_phong_id
                """,
                value_col="loai_phong_id",
                label_cols=["loai_phong_id", "ten_loai_phong"],
                fallback_items=ROOM_TYPE_FALLBACK,
                help_text="Chọn tên loại phòng. Nếu role không có quyền SELECT LoaiPhong, app dùng danh mục gợi ý."
            )

        with col2:
            ngay_den = st.date_input("Ngày đến", value=date.today(), label_visibility="collapsed")

        with col3:
            ngay_di = st.date_input("Ngày đi", value=date.today() + timedelta(days=1), label_visibility="collapsed")

        with col4:
            keyword = st.text_input("Từ khóa tìm kiếm", placeholder="Từ khóa tìm kiếm", label_visibility="collapsed")

        with col5:
            submit = st.form_submit_button("Tìm kiếm", use_container_width=True)

        if submit:
            if ngay_di <= ngay_den:
                st.warning("Ngày đi phải lớn hơn ngày đến.")
            else:
                try:
                    df = db_query(
                        """
                        EXEC dbo.sp_R2_KiemTraPhongTrong
                            @loai_phong_id = ?,
                            @ngay_den = ?,
                            @ngay_di = ?
                        """,
                        [loai_phong_id, ngay_den, ngay_di],
                    )

                    if keyword.strip() and not df.empty:
                        keyword_lower = keyword.strip().lower()
                        mask = pd.Series([False] * len(df))
                        for col in df.columns:
                            mask = mask | df[col].astype(str).str.lower().str.contains(keyword_lower, na=False)
                        df = df[mask]

                    search_payload = {
                        "loai_phong_id": int(loai_phong_id),
                        "loai_phong_label": loai_phong_label,
                        "ngay_den": ngay_den,
                        "ngay_di": ngay_di,
                        "keyword": keyword,
                        "so_dem": max((ngay_di - ngay_den).days, 0),
                    }
                    st.session_state["last_available_rooms"] = df
                    st.session_state["last_room_search"] = search_payload
                    save_workflow_state(last_room_search=search_payload, last_available_rooms=df)
                    st.success(f"Tìm thấy {len(df)} phòng phù hợp cho loại phòng: {loai_phong_label}.")

                except Exception as e:
                    st.error(f"Lỗi tìm phòng: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

def page_home():
    role = st.session_state["role"]

    if role == "Lễ tân":
        render_search_panel()
        page_title(
            "Tổng quan lễ tân",
            "Theo dõi nhanh tình trạng phòng, khách hàng và luồng đặt phòng đang xử lý."
        )

        today = date.today()
        tomorrow = today + timedelta(days=1)
        available_today = count_available_rooms_for_range(today, tomorrow)
        last_booking = load_saved_value("last_created_booking", {}) or {}
        last_assignment = load_saved_value("last_assigned_room", {}) or {}
        last_rooms = load_saved_value("last_available_rooms", pd.DataFrame())

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            try:
                df = db_query("SELECT COUNT(*) AS n FROM dbo.v_R3_KhachHang_Masked")
                metric_card("👤", "Khách hàng", int(df.iloc[0]["n"]))
            except Exception:
                metric_card("👤", "Khách hàng", "N/A")

        with c2:
            metric_card("🛏️", "Phòng trống đêm nay", available_today if available_today is not None else "N/A")

        with c3:
            if isinstance(last_rooms, pd.DataFrame) and not last_rooms.empty:
                metric_card("🔎", "Kết quả tìm gần nhất", len(last_rooms))
            else:
                metric_card("🔎", "Kết quả tìm gần nhất", 0)

        with c4:
            current_flow = "Chưa có"
            if last_assignment.get("phan_phong_id"):
                current_flow = f"PP {last_assignment.get('phan_phong_id')}"
            elif last_booking.get("dat_phong_id"):
                current_flow = f"DP {last_booking.get('dat_phong_id')}"
            metric_card("📌", "Luồng đang xử lý", current_flow)

        st.write("")

        if last_booking:
            content_card_start("Đặt phòng gần nhất")
            st.markdown(
                f"""
                <div class="step-box">
                    <div class="step-title">Thông tin đang được lưu để chuyển bước</div>
                    <div class="step-text">
                        Mã đặt phòng: <b>{escape_text(last_booking.get('ma_dat_phong'))}</b><br>
                        Đặt phòng ID: <b>{escape_text(last_booking.get('dat_phong_id'))}</b> · CTDP ID: <b>{escape_text(last_booking.get('ct_dat_phong_id'))}</b><br>
                        Loại phòng: <b>{escape_text(last_booking.get('loai_phong_label'))}</b> · Số đêm: <b>{escape_text(last_booking.get('so_dem'))}</b><br>
                        Tạm tính tiền phòng: <b>{safe_money(last_booking.get('tam_tinh_tien_phong'))}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            content_card_end()

        result_df = st.session_state.get("last_available_rooms")
        if isinstance(result_df, pd.DataFrame) and not result_df.empty:
            render_room_cards(result_df, "Phòng trống đã tìm gần nhất")
        else:
            content_card_start("Gợi ý thao tác cho lễ tân")
            st.markdown(
                """
                <div class="step-box">
                    <div class="step-title">1. Khách hàng</div>
                    <div class="step-text">Xem khách hàng qua view masked và thêm khách bằng stored procedure.</div>
                </div>
                <div class="step-box">
                    <div class="step-title">2. Tạo đặt phòng</div>
                    <div class="step-text">Chọn loại phòng, ngày ở và số khách. App sẽ tự kiểm tra sức chứa tối đa.</div>
                </div>
                <div class="step-box">
                    <div class="step-title">3. Tìm phòng và phân phòng</div>
                    <div class="step-text">Tìm phòng trống theo ngày, sau đó chọn đúng phòng trong kết quả để phân phòng.</div>
                </div>
                <div class="step-box">
                    <div class="step-title">4. Check-in / Check-out</div>
                    <div class="step-text">Khách cần được thanh toán trước khi check-out để đúng luồng nghiệp vụ.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            content_card_end()

    elif role == "Thu ngân":
        page_title("Tổng quan thu ngân", "Theo dõi hóa đơn, dịch vụ và thanh toán qua view tài chính.")

        try:
            df = db_query(
                """
                SELECT *
                FROM dbo.v_R2_HoaDonTongHop
                ORDER BY ngay_lap DESC
                """
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                metric_card("🧾", "Số hóa đơn", len(df))
            with c2:
                value = df["tong_can_thanh_toan"].fillna(0).sum() if "tong_can_thanh_toan" in df.columns else 0
                metric_card("💰", "Tổng phát sinh", safe_money(value))
            with c3:
                value = df["tong_da_thanh_toan"].fillna(0).sum() if "tong_da_thanh_toan" in df.columns else 0
                metric_card("💳", "Đã thanh toán", safe_money(value))
            with c4:
                value = df["so_tien_con_lai"].fillna(0).sum() if "so_tien_con_lai" in df.columns else 0
                metric_card("⚠️", "Còn lại", safe_money(value))

            st.write("")
            content_card_start("Hóa đơn gần đây")
            safe_dataframe(df.head(200), height=420)
            content_card_end()

        except Exception as e:
            st.error(f"Lỗi tổng quan thu ngân: {e}")

    elif role == "Kế toán":
        page_title("Tổng quan kế toán", "Cập nhật hóa đơn, công nợ và lịch sử thanh toán phục vụ đối soát.")

        try:
            df = db_query(
                """
                SELECT *
                FROM dbo.v_R2_HoaDonTongHop
                ORDER BY ngay_lap DESC
                """
            )

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                metric_card("🧾", "Số hóa đơn", len(df))
            with c2:
                value = df["tong_can_thanh_toan"].fillna(0).sum() if "tong_can_thanh_toan" in df.columns else 0
                metric_card("💰", "Tổng phát sinh", safe_money(value))
            with c3:
                value = df["tong_da_thanh_toan"].fillna(0).sum() if "tong_da_thanh_toan" in df.columns else 0
                metric_card("✅", "Đã thu", safe_money(value))
            with c4:
                value = df["so_tien_con_lai"].fillna(0).sum() if "so_tien_con_lai" in df.columns else 0
                metric_card("⚠️", "Công nợ", safe_money(value))

            left, right = st.columns([1.1, 0.9], gap="large")
            with left:
                content_card_start("Hóa đơn mới cập nhật")
                safe_dataframe(df.head(150), height=380)
                content_card_end()
            with right:
                content_card_start("Thanh toán mới nhất")
                try:
                    pay_df = db_query(
                        """
                        SELECT TOP 150 *
                        FROM dbo.v_R2_ThanhToanChiTiet
                        ORDER BY ngay_thanh_toan DESC
                        """
                    )
                    safe_dataframe(pay_df, height=380)
                except Exception as e:
                    st.info(f"Không tải được lịch sử thanh toán: {e}")
                content_card_end()

        except Exception as e:
            st.error(f"Lỗi tổng quan kế toán: {e}")

    else:
        page_dashboard()


# =========================================================
# 11. PAGE: DASHBOARD
# =========================================================


def page_dashboard():
    page_title("Dashboard quản lý", "Tổng quan doanh thu, thanh toán, công nợ và hoạt động khách sạn.")

    try:
        df = db_query(
            """
            SELECT *
            FROM dbo.v_R2_HoaDonTongHop
            ORDER BY ngay_lap DESC
            """
        )

        if df.empty:
            st.info("Chưa có dữ liệu hóa đơn.")
            return

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            metric_card("🧾", "Số hóa đơn", len(df))
        with c2:
            value = df["tong_can_thanh_toan"].fillna(0).sum() if "tong_can_thanh_toan" in df.columns else 0
            metric_card("💰", "Tổng phát sinh", safe_money(value))
        with c3:
            value = df["tong_da_thanh_toan"].fillna(0).sum() if "tong_da_thanh_toan" in df.columns else 0
            metric_card("💳", "Đã thanh toán", safe_money(value))
        with c4:
            value = df["so_tien_con_lai"].fillna(0).sum() if "so_tien_con_lai" in df.columns else 0
            metric_card("⚠️", "Công nợ", safe_money(value))

        st.write("")

        left, right = st.columns([1.15, 0.85], gap="large")

        with left:
            content_card_start("Hóa đơn mới nhất")
            safe_dataframe(df.head(250), height=430)
            content_card_end()

        with right:
            content_card_start("Biểu đồ doanh thu theo tháng")
            if "ngay_lap" in df.columns and "tong_can_thanh_toan" in df.columns:
                chart_df = df.copy()
                chart_df["ngay_lap"] = pd.to_datetime(chart_df["ngay_lap"], errors="coerce")
                chart_df = chart_df.dropna(subset=["ngay_lap"])
                chart_df["thang"] = chart_df["ngay_lap"].dt.to_period("M").astype(str)
                revenue_df = chart_df.groupby("thang", as_index=False)["tong_can_thanh_toan"].sum().sort_values("thang")
                if not revenue_df.empty:
                    st.bar_chart(revenue_df.set_index("thang"))
                else:
                    st.info("Không có dữ liệu biểu đồ.")
            else:
                st.info("View chưa có cột ngay_lap hoặc tong_can_thanh_toan.")
            content_card_end()

        left2, right2 = st.columns([1, 1], gap="large")
        with left2:
            content_card_start("Thanh toán mới ghi nhận")
            try:
                pay_df = db_query(
                    """
                    SELECT TOP 200 *
                    FROM dbo.v_R2_ThanhToanChiTiet
                    ORDER BY ngay_thanh_toan DESC
                    """
                )
                safe_dataframe(pay_df, height=360)
            except Exception as e:
                st.info(f"Không tải được lịch sử thanh toán: {e}")
            content_card_end()

        with right2:
            content_card_start("Hóa đơn còn công nợ")
            try:
                debt_df = df.copy()
                if "so_tien_con_lai" in debt_df.columns:
                    debt_df = debt_df[debt_df["so_tien_con_lai"].fillna(0) > 0]
                safe_dataframe(debt_df.head(200), height=360)
            except Exception as e:
                st.info(f"Không tải được công nợ: {e}")
            content_card_end()

    except Exception as e:
        st.error(f"Lỗi dashboard: {e}")


def page_customers():
    page_title("Quản lý khách hàng", "Xem view masked, thêm khách mới và tìm kiếm an toàn.")

    tab1, tab2, tab3 = st.tabs(["Danh sách khách hàng", "Thêm khách hàng", "Tìm kiếm an toàn"])

    with tab1:
        content_card_start("Danh sách khách hàng")

        try:
            df = db_query(
                """
                SELECT TOP 300 *
                FROM dbo.v_R3_KhachHang_Masked
                ORDER BY khach_hang_id DESC
                """
            )
            safe_dataframe(df, height=520)
        except Exception as e:
            st.error(f"Lỗi tải danh sách khách hàng: {e}")

        content_card_end()

    with tab2:
        content_card_start("Thêm khách hàng mới")

        c1, c2 = st.columns(2)

        with c1:
            ho_ten = st.text_input("Họ tên khách hàng")
            so_dien_thoai = st.text_input("Số điện thoại")
            quoc_tich = st.text_input("Quốc tịch", value="Việt Nam")

        with c2:
            email = st.text_input("Email")
            cccd_ho_chieu = st.text_input("CCCD/Hộ chiếu")

        st.markdown(
            """
            <div class="step-box">
                <div class="step-title">Gợi ý thao tác</div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Thêm khách hàng"):
            if not ho_ten.strip():
                st.warning("Vui lòng nhập họ tên khách hàng.")
            else:
                try:
                    db_exec(
                        """
                        SET NOCOUNT ON;
                        DECLARE @khach_hang_id INT;

                        EXEC dbo.sp_R2_TaoKhachHang
                            @khach_hang_id = @khach_hang_id OUTPUT,
                            @ho_ten = ?,
                            @so_dien_thoai = ?,
                            @email = ?,
                            @cccd_ho_chieu = ?,
                            @quoc_tich = ?;
                        """,
                        [ho_ten, so_dien_thoai, email, cccd_ho_chieu, quoc_tich],
                    )
                    st.success("Thêm khách hàng thành công.")
                except Exception as e:
                    st.error(f"Lỗi thêm khách hàng: {e}")

        content_card_end()

    with tab3:
        content_card_start("Tìm kiếm khách hàng bằng stored procedure có tham số")

        keyword = st.text_input("Từ khóa tìm kiếm", placeholder="Nhập tên, số điện thoại, email...")

        if st.button("Tìm kiếm khách hàng"):
            try:
                df = db_query(
                    "EXEC dbo.sp_R3_TimKhachHang_AnToan @tu_khoa = ?",
                    [keyword],
                )
                safe_dataframe(df, height=440)
            except Exception as e:
                st.error(f"Lỗi tìm kiếm khách hàng bằng sp_R3_TimKhachHang_AnToan: {e}")

        content_card_end()


def page_create_booking():
    page_title(
        "Tạo đặt phòng",
        "Chọn khách, nguồn đặt phòng và loại phòng; app lưu lại ID để các bước sau không phải nhập lại."
    )

    content_card_start("Bước 1 — Chọn khách hàng từ view masked")

    try:
        customer_df = load_customers_masked()

        if customer_df.empty:
            st.warning("Không có dữ liệu khách hàng. Hãy thêm khách hàng trước.")
            content_card_end()
            return

        customer_options = {}
        for _, row in customer_df.iterrows():
            label = f"{row['khach_hang_id']} - {row['ho_ten']}"
            customer_options[label] = int(row["khach_hang_id"])

        selected_customer = st.selectbox("Khách hàng", list(customer_options.keys()))
        khach_hang_id = customer_options[selected_customer]

    except Exception as e:
        st.error(f"Không tải được view khách hàng masked: {e}")
        content_card_end()
        return

    content_card_end()

    content_card_start("Bước 2 — Thông tin đặt phòng")

    col1, col2 = st.columns(2)

    with col1:
        booking_code = st.text_input("Mã đặt phòng", value=generate_code("DP_APP"))
        nguon_id, nguon_label = select_reference(
            label="Nguồn đặt phòng",
            sql="""
                SELECT nguon_id, ten_nguon
                FROM dbo.v_R5_NguonDatPhong
                ORDER BY nguon_id
            """,
            value_col="nguon_id",
            label_cols=["nguon_id", "ten_nguon"],
            fallback_items=SOURCE_FALLBACK,
            help_text="Chọn tên nguồn đặt phòng. Nếu role không có quyền SELECT, app dùng danh mục gợi ý."
        )
        staff_id = nullable_int_from_text(
            st.text_input(
                "Nhân viên tiếp nhận ID",
                value="",
                placeholder="Để trống nếu procedure cho phép NULL"
            )
        )

    with col2:
        arrival_date = st.date_input("Ngày đến", value=date.today())
        departure_date = st.date_input("Ngày đi", value=date.today() + timedelta(days=1))
        note = st.text_area("Ghi chú", value="Tạo từ ứng dụng R5")

    content_card_end()

    content_card_start("Bước 3 — Khách muốn đặt loại phòng gì")

    col3, col4 = st.columns(2)

    with col3:
        loai_phong_id, loai_phong_label = select_reference(
            label="Loại phòng khách muốn đặt",
            sql="""
                SELECT loai_phong_id, ten_loai_phong
                FROM dbo.v_R5_LoaiPhong
                ORDER BY loai_phong_id
            """,
            value_col="loai_phong_id",
            label_cols=["loai_phong_id", "ten_loai_phong"],
            fallback_items=ROOM_TYPE_FALLBACK,
            help_text="Chọn tên loại phòng thay vì nhập ID. App sẽ truyền loai_phong_id tương ứng vào procedure."
        )
        room_meta = get_room_type_meta(loai_phong_id)
        max_guests = int(room_meta.get("suc_chua_toi_da", default_capacity_for_room_type(loai_phong_id)))
        st.caption(f"Sức chứa tối đa của loại phòng này: {max_guests} khách.")
        adults = st.number_input("Số người lớn", min_value=1, max_value=max_guests, value=1)
        max_children = max(max_guests - int(adults), 0)
        children = st.number_input("Số trẻ em", min_value=0, max_value=max_children, value=0)

    with col4:
        so_dem = max((departure_date - arrival_date).days, 0)
        default_price = float(room_meta.get("gia_niem_yet", default_price_for_room_type(loai_phong_id)))
        price = st.number_input(
            "Đơn giá 1 đêm",
            min_value=0.0,
            value=default_price,
            step=50000.0,
            help="Đây là giá cho 1 đêm. Tổng tiền phòng sẽ được tính theo số đêm lưu trú."
        )
        discount = st.number_input("Giảm giá toàn bộ lượt đặt", min_value=0.0, value=0.0, step=50000.0)
        estimated_room_total = max(float(so_dem) * float(price) - float(discount), 0.0)

        st.metric("Số đêm lưu trú", so_dem)
        st.metric("Tạm tính tiền phòng", safe_money(estimated_room_total))

    st.markdown(
        f"""
        <div class="step-box">
            <div class="step-title">Tóm tắt yêu cầu đặt phòng</div>
            <div class="step-text">
                Khách hàng: <b>{escape_text(selected_customer)}</b><br>
                Nguồn đặt: <b>{escape_text(nguon_label)}</b><br>
                Loại phòng muốn đặt: <b>{escape_text(loai_phong_label)}</b><br>
                Thời gian: <b>{arrival_date}</b> đến <b>{departure_date}</b> = <b>{so_dem} đêm</b><br>
                Đơn giá 1 đêm: <b>{safe_money(price)}</b> · Giảm giá: <b>{safe_money(discount)}</b><br>
                Tạm tính tiền phòng: <b>{safe_money(estimated_room_total)}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Tạo đặt phòng"):
        if departure_date <= arrival_date:
            st.warning("Ngày đi phải lớn hơn ngày đến.")
        elif int(adults) + int(children) > int(max_guests):
            st.warning(f"Số khách vượt quá sức chứa tối đa của {loai_phong_label}: {max_guests} khách.")
        else:
            try:
                result_df = db_exec_return_df(
                    """
                    SET NOCOUNT ON;
                    DECLARE @dat_phong_id INT;
                    DECLARE @ct_dat_phong_id INT;

                    EXEC dbo.sp_R2_TaoDatPhong
                        @dat_phong_id = @dat_phong_id OUTPUT,
                        @ma_dat_phong = ?,
                        @khach_hang_id = ?,
                        @nguon_id = ?,
                        @nhan_vien_dat_phong_id = ?,
                        @ngay_den = ?,
                        @ngay_di = ?,
                        @ghi_chu = ?;

                    EXEC dbo.sp_R2_ThemChiTietDatPhong
                        @ct_dat_phong_id = @ct_dat_phong_id OUTPUT,
                        @dat_phong_id = @dat_phong_id,
                        @loai_phong_id = ?,
                        @nguoi_lon = ?,
                        @tre_em = ?,
                        @don_gia_ap_dung = ?,
                        @giam_gia = ?;

                    SELECT
                        @dat_phong_id AS dat_phong_id,
                        @ct_dat_phong_id AS ct_dat_phong_id;
                    """,
                    [
                        booking_code,
                        khach_hang_id,
                        nguon_id,
                        staff_id,
                        arrival_date,
                        departure_date,
                        note,
                        loai_phong_id,
                        adults,
                        children,
                        price,
                        discount,
                    ],
                )

                dat_phong_id = None
                ct_dat_phong_id = None
                if result_df is not None and not result_df.empty:
                    dat_phong_id = int(result_df.iloc[0]["dat_phong_id"])
                    ct_dat_phong_id = int(result_df.iloc[0]["ct_dat_phong_id"])

                booking_payload = {
                    "dat_phong_id": dat_phong_id,
                    "ct_dat_phong_id": ct_dat_phong_id,
                    "loai_phong_id": int(loai_phong_id),
                    "loai_phong_label": loai_phong_label,
                    "ngay_den": arrival_date,
                    "ngay_di": departure_date,
                    "so_dem": int(so_dem),
                    "don_gia_mot_dem": float(price),
                    "giam_gia": float(discount),
                    "tam_tinh_tien_phong": float(estimated_room_total),
                    "ma_dat_phong": booking_code,
                    "khach_hang": selected_customer,
                    "nguon_id": int(nguon_id),
                    "nguon_label": nguon_label,
                }

                st.session_state["last_created_booking"] = booking_payload
                save_workflow_state(last_created_booking=booking_payload)

                if dat_phong_id is not None and ct_dat_phong_id is not None:
                    st.success(
                        f"Tạo đặt phòng thành công. Đặt phòng ID: {dat_phong_id} | "
                        f"Chi tiết đặt phòng ID cần dùng để phân phòng: {ct_dat_phong_id}."
                    )
                    st.info(
                        "Bước tiếp theo: vào 'Tìm phòng trống', giữ đúng loại phòng và ngày ở này, "
                        "chọn một phòng trong kết quả rồi sang 'Phân phòng'."
                    )
                else:
                    st.success(f"Tạo đặt phòng thành công cho loại phòng: {loai_phong_label}.")
                    st.warning("Procedure chạy xong nhưng app chưa đọc được ID trả về. Hãy kiểm tra lại chữ ký OUTPUT của procedure.")

            except Exception as e:
                st.error(f"Lỗi tạo đặt phòng: {e}")

    last = load_saved_value("last_created_booking", None)
    if last:
        st.markdown(
            f"""
            <div class="step-box">
                <div class="step-title">Đặt phòng vừa tạo gần nhất</div>
                <div class="step-text">
                    Mã đặt phòng: <b>{escape_text(last.get('ma_dat_phong'))}</b><br>
                    Đặt phòng ID: <b>{escape_text(last.get('dat_phong_id'))}</b><br>
                    Chi tiết đặt phòng ID: <b>{escape_text(last.get('ct_dat_phong_id'))}</b><br>
                    Loại phòng: <b>{escape_text(last.get('loai_phong_label'))}</b><br>
                    Ngày ở: <b>{escape_text(last.get('ngay_den'))}</b> đến <b>{escape_text(last.get('ngay_di'))}</b> = <b>{escape_text(last.get('so_dem'))} đêm</b><br>
                    Đơn giá 1 đêm: <b>{safe_money(last.get('don_gia_mot_dem'))}</b><br>
                    Tạm tính tiền phòng: <b>{safe_money(last.get('tam_tinh_tien_phong'))}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    content_card_end()


def page_room_search():
    page_title(
        "Tìm phòng trống",
        "Chọn đúng loại phòng và khoảng ngày của đặt phòng; app lưu danh sách phòng để bước Phân phòng dùng tiếp."
    )

    last = load_saved_value("last_created_booking", {}) or {}
    default_loai_phong_id = last.get("loai_phong_id")
    default_ngay_den = parse_iso_date(last.get("ngay_den"), date.today())
    default_ngay_di = parse_iso_date(last.get("ngay_di"), date.today() + timedelta(days=1))

    if last:
        st.info(
            f"Gợi ý theo đặt phòng vừa tạo: CTDP ID {last.get('ct_dat_phong_id')} - "
            f"{last.get('loai_phong_label')} - {last.get('ngay_den')} đến {last.get('ngay_di')} "
            f"({last.get('so_dem', '')} đêm)."
        )

    content_card_start("Thông tin tìm kiếm")

    col1, col2, col3 = st.columns(3)

    with col1:
        loai_phong_id, loai_phong_label = select_reference(
            label="Loại phòng",
            sql="""
                SELECT loai_phong_id, ten_loai_phong
                FROM dbo.v_R5_LoaiPhong
                ORDER BY loai_phong_id
            """,
            value_col="loai_phong_id",
            label_cols=["loai_phong_id", "ten_loai_phong"],
            fallback_items=ROOM_TYPE_FALLBACK,
            help_text="Chọn đúng loại phòng đã đặt. Phòng phân phải cùng loại với chi tiết đặt phòng.",
            default_id=default_loai_phong_id,
        )

    with col2:
        ngay_den = st.date_input("Ngày đến", value=default_ngay_den)

    with col3:
        ngay_di = st.date_input("Ngày đi", value=default_ngay_di)

    if st.button("Tìm phòng trống"):
        if ngay_di <= ngay_den:
            st.warning("Ngày đi phải lớn hơn ngày đến.")
        else:
            try:
                df = db_query(
                    """
                    EXEC dbo.sp_R2_KiemTraPhongTrong
                        @loai_phong_id = ?,
                        @ngay_den = ?,
                        @ngay_di = ?
                    """,
                    [loai_phong_id, ngay_den, ngay_di],
                )

                search_payload = {
                    "loai_phong_id": int(loai_phong_id),
                    "loai_phong_label": loai_phong_label,
                    "ngay_den": ngay_den,
                    "ngay_di": ngay_di,
                    "so_dem": max((ngay_di - ngay_den).days, 0),
                }
                st.session_state["last_available_rooms"] = df
                st.session_state["last_room_search"] = search_payload
                save_workflow_state(last_room_search=search_payload, last_available_rooms=df)

                st.success(f"Tìm thấy {len(df)} phòng phù hợp cho loại phòng: {loai_phong_label}.")
                safe_dataframe(df, height=360)

                if not df.empty:
                    render_room_cards(df, "Kết quả phòng trống", limit=9)

            except Exception as e:
                st.error(f"Lỗi tìm phòng trống: {e}")

    saved_rooms = load_saved_value("last_available_rooms", pd.DataFrame())
    if isinstance(saved_rooms, pd.DataFrame) and not saved_rooms.empty:
        st.markdown("#### Phòng trống đã tìm gần nhất")
        safe_dataframe(saved_rooms, height=260)

    content_card_end()


def page_assign_room():
    page_title("Phân phòng")

    last_booking = load_saved_value("last_created_booking", {}) or {}
    last_rooms = load_saved_value("last_available_rooms", pd.DataFrame())
    last_search = load_saved_value("last_room_search", {}) or {}

    content_card_start("Nhập thông tin phân phòng")

    if last_booking:
        st.info(
            f"Gợi ý từ đặt phòng vừa tạo: CTDP ID {last_booking.get('ct_dat_phong_id')} - "
            f"{last_booking.get('loai_phong_label')} - {last_booking.get('so_dem', '')} đêm. "
            "Hãy chọn phòng từ kết quả tìm phòng trống cùng loại."
        )

    col1, col2 = st.columns(2)

    with col1:
        default_ctdp = last_booking.get("ct_dat_phong_id") or 1
        ct_dat_phong_id = st.number_input("Chi tiết đặt phòng ID", min_value=1, value=int(default_ctdp))

    with col2:
        phong_id = None
        selected_room_label = ""
        if isinstance(last_rooms, pd.DataFrame) and not last_rooms.empty and "phong_id" in last_rooms.columns:
            room_options = {}
            for _, row in last_rooms.iterrows():
                pid = int(row["phong_id"])
                ma_phong = safe_text(row.get("ma_phong", f"Phòng {pid}"))
                ten_loai = safe_text(row.get("ten_loai_phong", last_search.get("loai_phong_label", "")))
                tang = safe_text(row.get("tang", ""))
                label = f"{pid} - {ma_phong}"
                if ten_loai:
                    label += f" - {ten_loai}"
                if tang:
                    label += f" - Tầng {tang}"
                room_options[label] = pid

            selected_room_label = st.selectbox("Phòng trống phù hợp", list(room_options.keys()))
            phong_id = room_options[selected_room_label]
        else:
            phong_id = st.number_input("Phòng ID", min_value=1, value=1)
            selected_room_label = f"Phòng ID {phong_id}"
            st.caption("Chưa có kết quả tìm phòng trống. Nên vào 'Tìm phòng trống' trước để lấy phòng đúng loại.")

    

    if st.button("Phân phòng cho khách"):
        try:
            phan_phong_id = None
            try:
                result_df = db_exec_return_df(
                    """
                    SET NOCOUNT ON;
                    DECLARE @phan_phong_id INT;

                    EXEC dbo.sp_R2_PhanPhongChoKhach
                        @ct_dat_phong_id = ?,
                        @phong_id = ?,
                        @phan_phong_id = @phan_phong_id OUTPUT;

                    SELECT @phan_phong_id AS phan_phong_id;
                    """,
                    [ct_dat_phong_id, phong_id],
                )
                if result_df is not None and not result_df.empty and "phan_phong_id" in result_df.columns:
                    phan_phong_id = int(result_df.iloc[0]["phan_phong_id"])
            except Exception as main_error:
                if is_signature_error(main_error):
                    db_exec(
                        """
                        EXEC dbo.sp_R2_PhanPhongChoKhach
                            @ct_dat_phong_id = ?,
                            @phong_id = ?;
                        """,
                        [ct_dat_phong_id, phong_id],
                    )
                else:
                    raise main_error

            assignment_payload = {
                "phan_phong_id": phan_phong_id,
                "ct_dat_phong_id": int(ct_dat_phong_id),
                "phong_id": int(phong_id),
                "phong_label": selected_room_label,
                "loai_phong_label": last_booking.get("loai_phong_label") or last_search.get("loai_phong_label"),
                "ngay_den": last_booking.get("ngay_den") or last_search.get("ngay_den"),
                "ngay_di": last_booking.get("ngay_di") or last_search.get("ngay_di"),
                "so_dem": last_booking.get("so_dem") or last_search.get("so_dem"),
            }
            st.session_state["last_assigned_room"] = assignment_payload
            save_workflow_state(last_assigned_room=assignment_payload)

            if phan_phong_id:
                st.success(f"Phân phòng thành công. Phân phòng ID: {phan_phong_id}. Hãy dùng ID này khi thêm tiền phòng vào hóa đơn.")
            else:
                st.success("Phân phòng thành công. Nếu procedure không trả ID, hãy dùng ID phân phòng vừa phát sinh trong SQL Server.")

        except Exception as e:
            err = str(e)
            if "không đúng loại phòng" in err.lower() or "khong dung loai phong" in err.lower():
                st.error(
                    "Phân phòng thất bại: phòng bạn chọn không cùng loại với loại phòng khách đã đặt. "
                    "Hãy vào 'Tìm phòng trống', chọn đúng loại phòng của CTDP rồi chọn phòng trong kết quả."
                )
            else:
                st.error(f"Phân phòng thất bại: {e}")

    last_assignment = load_saved_value("last_assigned_room", {}) or {}
    if last_assignment:
        st.markdown(
            f"""
            <div class="step-box">
                <div class="step-title">Phân phòng gần nhất đã lưu</div>
                <div class="step-text">
                    Phân phòng ID: <b>{escape_text(last_assignment.get('phan_phong_id'))}</b><br>
                    CTDP ID: <b>{escape_text(last_assignment.get('ct_dat_phong_id'))}</b><br>
                    Phòng: <b>{escape_text(last_assignment.get('phong_label') or last_assignment.get('phong_id'))}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    content_card_end()



# =========================================================
# 15B. PAGE: HỦY ĐẶT PHÒNG
# =========================================================

def page_cancel_booking():
    page_title("Huỷ đặt phòng", "Hủy đặt phòng bằng stored procedure, không cập nhật trực tiếp bảng DatPhong.")

    last_booking = load_saved_value("last_created_booking", {}) or {}

    content_card_start("Thông tin hủy đặt phòng")

    if last_booking:
        st.info(
            f"Đặt phòng gần nhất: mã {last_booking.get('ma_dat_phong')} · "
            f"Đặt phòng ID {last_booking.get('dat_phong_id')} · CTDP ID {last_booking.get('ct_dat_phong_id')}."
        )

    ma_dat_phong = st.text_input(
        "Mã đặt phòng",
        value=safe_text(last_booking.get("ma_dat_phong", "")),
        placeholder="Ví dụ: DP_APP_20260504120000"
    )
    dat_phong_id = st.number_input(
        "Đặt phòng ID dự phòng",
        min_value=1,
        value=int(last_booking.get("dat_phong_id") or 1),
        help="Chỉ dùng nếu procedure của bạn nhận @dat_phong_id thay vì @ma_dat_phong."
    )
    ly_do_huy = st.text_area("Lý do hủy", value="Khách yêu cầu hủy đặt phòng")


    if st.button("Huỷ đặt phòng"):
        try:
            if ma_dat_phong.strip():
                try:
                    db_exec(
                        """
                        EXEC dbo.sp_R2_HuyDatPhong
                            @ma_dat_phong = ?,
                            @ly_do_huy = ?
                        """,
                        [ma_dat_phong.strip(), ly_do_huy],
                    )
                except Exception as main_error:
                    if is_signature_error(main_error):
                        db_exec(
                            """
                            EXEC dbo.sp_R2_HuyDatPhong
                                @dat_phong_id = ?,
                                @ly_do_huy = ?
                            """,
                            [int(dat_phong_id), ly_do_huy],
                        )
                    else:
                        raise main_error
            else:
                db_exec(
                    """
                    EXEC dbo.sp_R2_HuyDatPhong
                        @dat_phong_id = ?,
                        @ly_do_huy = ?
                    """,
                    [int(dat_phong_id), ly_do_huy],
                )

            save_workflow_state(last_cancelled_booking={"ma_dat_phong": ma_dat_phong, "dat_phong_id": int(dat_phong_id), "ly_do_huy": ly_do_huy, "cancelled_at": datetime.now()})
            st.success("Huỷ đặt phòng thành công. Phòng đã phân nếu có sẽ được giải phóng theo logic stored procedure.")

        except Exception as e:
            st.error(f"Lỗi huỷ đặt phòng: {e}")

    content_card_end()

def can_checkout_current_assignment(phan_phong_id: int):
    """
    Chỉ cho check-out khi:
    1. Có hóa đơn đã tạo.
    2. Hóa đơn đó đã được gắn với phân phòng đang check-out.
    3. Thu ngân đã bấm 'Ghi nhận thanh toán' cho đúng hóa đơn đó.
    """

    last_assignment = load_saved_value("last_assigned_room", {}) or {}
    last_invoice = load_saved_value("last_created_invoice", {}) or {}
    last_charge = load_saved_value("last_added_room_charge", {}) or {}
    last_payment = load_saved_value("last_payment", {}) or {}

    phan_phong_id = int(phan_phong_id)

    # 1. Kiểm tra phân phòng đang chọn có đúng phân phòng trong luồng app không
    assignment_id = last_assignment.get("phan_phong_id")
    if assignment_id and int(assignment_id) != phan_phong_id:
        return False, (
            "Phân phòng ID đang chọn không khớp với phân phòng gần nhất trong luồng app. "
            "Hãy chọn đúng Phân phòng ID đã được lập hóa đơn/thanh toán."
        )

    # 2. Xác định hóa đơn cần thanh toán
    invoice_id = None

    if last_charge and last_charge.get("hoa_don_id"):
        if int(last_charge.get("phan_phong_id", 0)) == phan_phong_id:
            invoice_id = int(last_charge["hoa_don_id"])

    if invoice_id is None and last_invoice and last_invoice.get("hoa_don_id"):
        invoice_id = int(last_invoice["hoa_don_id"])

    if invoice_id is None:
        return False, (
            "Chưa có hóa đơn cho lượt lưu trú này. "
            "Hãy đăng nhập Thu ngân → Lập hóa đơn → Thêm tiền phòng trước."
        )

    # 3. Kiểm tra đã bấm Ghi nhận thanh toán chưa
    if not last_payment:
        return False, (
            f"Hóa đơn {invoice_id} chưa được ghi nhận thanh toán. "
            "Hãy đăng nhập Thu ngân → Thanh toán → bấm 'Ghi nhận thanh toán', rồi quay lại check-out."
        )

    paid_invoice_id = last_payment.get("hoa_don_id")

    if not paid_invoice_id or int(paid_invoice_id) != int(invoice_id):
        return False, (
            f"Thanh toán gần nhất không thuộc hóa đơn {invoice_id}. "
            "Hãy thanh toán đúng hóa đơn của lượt lưu trú này trước khi check-out."
        )

    return True, f"Hóa đơn {invoice_id} đã được ghi nhận thanh toán. Có thể check-out."
def get_phan_phong_detail(phan_phong_id: int):
    """
    Lấy thông tin chi tiết phân phòng: khách hàng, phòng, ngày đến/ngày đi.
    """
    try:
        df = db_query(
            """
            SELECT TOP 1 *
            FROM dbo.v_R5_PhanPhongChiTiet
            WHERE phan_phong_id = ?
            """,
            [int(phan_phong_id)]
        )

        if df is not None and not df.empty:
            return df.iloc[0].to_dict(), df

    except Exception:
        pass

    return None, pd.DataFrame()


def clear_after_checkout():
    """
    Sau khi check-out thành công thì xóa thông tin luồng hiện tại
    để màn hình không còn hiện khách vừa check-out nữa.
    """
    empty_payload = {
        "last_assigned_room": {},
        "last_checkin": {},
        "last_created_invoice": {},
        "last_added_room_charge": {},
        "last_payment": {},
        "last_checkout_ready": {},
    }

    for key, value in empty_payload.items():
        st.session_state[key] = value

    save_workflow_state(**empty_payload)
# =========================================================
# 16. PAGE: CHECK-IN / CHECK-OUT
# =========================================================

def page_checkin_checkout():
    page_title(
        "Check-in / Check-out",
        "Hiển thị thông tin khách hàng, chỉ cho check-out sau khi đã ghi nhận thanh toán."
    )

    last_assignment = load_saved_value("last_assigned_room", {}) or {}
    last_payment = load_saved_value("last_payment", {}) or {}
    last_invoice = load_saved_value("last_created_invoice", {}) or {}
    last_charge = load_saved_value("last_added_room_charge", {}) or {}

    default_phan_phong_id = int(last_assignment.get("phan_phong_id") or 1)

    content_card_start("Thông tin lượt phân phòng")

    if last_assignment:
        st.info(
            f"Gợi ý phân phòng gần nhất: Phân phòng ID {last_assignment.get('phan_phong_id')} - "
            f"Phòng {last_assignment.get('phong_label') or last_assignment.get('phong_id')}."
        )
    else:
        st.warning("Chưa có phân phòng gần nhất trong luồng app. Có thể nhập Phân phòng ID thủ công.")

    if last_invoice:
        st.info(
            f"Hóa đơn gần nhất: Hóa đơn ID {last_invoice.get('hoa_don_id')} - "
            f"Đặt phòng ID {last_invoice.get('dat_phong_id')}."
        )

    if last_charge:
        st.info(
            f"Tiền phòng đã thêm vào hóa đơn: Hóa đơn ID {last_charge.get('hoa_don_id')} - "
            f"Phân phòng ID {last_charge.get('phan_phong_id')}."
        )

    if last_payment:
        st.success(
            f"Thanh toán gần nhất: Hóa đơn ID {last_payment.get('hoa_don_id')} - "
            f"Số tiền {safe_money(last_payment.get('so_tien_thanh_toan'))}."
        )
    else:
        st.error(
            "Chưa thấy thao tác 'Ghi nhận thanh toán'. "
            "Khách chưa được phép check-out."
        )

    phan_phong_id = st.number_input(
        "Phân phòng ID",
        min_value=1,
        value=default_phan_phong_id
    )

    detail, detail_df = get_phan_phong_detail(int(phan_phong_id))

    if detail:
        st.markdown("### Thông tin khách hàng đang lưu trú")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div class="step-box">
                    <div class="step-title">Khách hàng</div>
                    <div class="step-text">
                        Họ tên: <b>{escape_text(detail.get('ho_ten'))}</b><br>
                        Khách hàng ID: <b>{escape_text(detail.get('khach_hang_id'))}</b><br>
                        Đặt phòng ID: <b>{escape_text(detail.get('dat_phong_id'))}</b><br>
                        Mã đặt phòng: <b>{escape_text(detail.get('ma_dat_phong'))}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div class="step-box">
                    <div class="step-title">Phòng</div>
                    <div class="step-text">
                        Phân phòng ID: <b>{escape_text(detail.get('phan_phong_id'))}</b><br>
                        Phòng: <b>{escape_text(detail.get('ma_phong'))}</b><br>
                        Loại phòng: <b>{escape_text(detail.get('ten_loai_phong'))}</b><br>
                        Trạng thái: <b>{escape_text(detail.get('trang_thai'))}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"""
                <div class="step-box">
                    <div class="step-title">Thời gian</div>
                    <div class="step-text">
                        Ngày đến: <b>{escape_text(detail.get('ngay_den'))}</b><br>
                        Ngày đi: <b>{escape_text(detail.get('ngay_di'))}</b><br>
                        Check-in thực tế: <b>{escape_text(detail.get('check_in_thuc_te'))}</b><br>
                        Check-out thực tế: <b>{escape_text(detail.get('check_out_thuc_te'))}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with st.expander("Xem dòng dữ liệu chi tiết"):
            safe_dataframe(detail_df, height=180)

    else:
        st.warning("Không tải được thông tin khách hàng cho phân phòng này.")

    # Kiểm tra có được check-out hay chưa
    can_checkout = False
    checkout_message = ""

    invoice_id = None

    if last_charge and last_charge.get("hoa_don_id"):
        if int(last_charge.get("phan_phong_id", 0)) == int(phan_phong_id):
            invoice_id = int(last_charge.get("hoa_don_id"))

    if invoice_id is None and last_invoice and last_invoice.get("hoa_don_id"):
        invoice_id = int(last_invoice.get("hoa_don_id"))

    if invoice_id is None:
        checkout_message = (
            "Chưa có hóa đơn cho lượt lưu trú này. "
            "Hãy đăng nhập Thu ngân → Lập hóa đơn → Thêm tiền phòng trước."
        )
    elif not last_payment:
        checkout_message = (
            f"Hóa đơn {invoice_id} chưa được ghi nhận thanh toán. "
            "Hãy đăng nhập Thu ngân → Thanh toán → bấm 'Ghi nhận thanh toán'."
        )
    elif int(last_payment.get("hoa_don_id", 0)) != int(invoice_id):
        checkout_message = (
            f"Thanh toán gần nhất không thuộc hóa đơn {invoice_id}. "
            "Hãy thanh toán đúng hóa đơn của lượt lưu trú này trước khi check-out."
        )
    else:
        can_checkout = True
        checkout_message = f"Hóa đơn {invoice_id} đã được ghi nhận thanh toán. Có thể check-out."

    if can_checkout:
        st.success(checkout_message)
    else:
        st.error(checkout_message)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Check-in"):
            try:
                db_exec(
                    "EXEC dbo.sp_R2_CheckIn @phan_phong_id = ?",
                    [int(phan_phong_id)]
                )

                save_workflow_state(
                    last_checkin={
                        "phan_phong_id": int(phan_phong_id),
                        "checked_in_at": datetime.now()
                    }
                )

                st.success("Check-in thành công.")
                st.cache_data.clear()
                st.rerun()

            except Exception as e:
                st.error(f"Lỗi check-in: {e}")

    with col2:
        if st.button("Check-out", disabled=not can_checkout):
            try:
                db_exec(
                    "EXEC dbo.sp_R2_CheckOut @phan_phong_id = ?",
                    [int(phan_phong_id)]
                )

                save_workflow_state(
                    last_checkout={
                        "phan_phong_id": int(phan_phong_id),
                        "hoa_don_id": invoice_id,
                        "ho_ten": detail.get("ho_ten") if detail else "",
                        "checked_out_at": datetime.now()
                    }
                )

                st.success("Check-out thành công. Thông tin khách vừa check-out đã được xóa khỏi màn hình.")

                clear_after_checkout()

                st.cache_data.clear()
                st.rerun()

            except Exception as e:
                st.error(f"Lỗi check-out: {e}")

    content_card_end()

# =========================================================
# 17. PAGE: LẬP HÓA ĐƠN
# =========================================================

def page_invoice():
    page_title("Lập hóa đơn", "Tạo hóa đơn cho đúng Đặt phòng ID, sau đó thêm tiền phòng theo Phân phòng ID.")

    last_booking = load_saved_value("last_created_booking", {}) or {}
    last_assignment = load_saved_value("last_assigned_room", {}) or {}
    last_invoice = load_saved_value("last_created_invoice", {}) or {}

    default_dat_phong_id = int(last_booking.get("dat_phong_id") or 1)
    default_phan_phong_id = int(last_assignment.get("phan_phong_id") or 1)
    default_hoa_don_id = int(last_invoice.get("hoa_don_id") or 1)

    if last_booking:
        st.info(
            "Đặt phòng gần nhất từ lễ tân: "
            f"Mã {last_booking.get('ma_dat_phong')} | "
            f"Đặt phòng ID {last_booking.get('dat_phong_id')} | "
            f"CTDP ID {last_booking.get('ct_dat_phong_id')} | "
            f"Loại phòng {last_booking.get('loai_phong_label')} | "
            f"{last_booking.get('so_dem', '')} đêm | "
            f"Tạm tính {safe_money(last_booking.get('tam_tinh_tien_phong'))}."
        )

    if last_assignment:
        st.success(
            "Phân phòng gần nhất đã lưu: "
            f"Phân phòng ID {last_assignment.get('phan_phong_id')} | "
            f"Phòng {last_assignment.get('phong_label') or last_assignment.get('phong_id')}."
        )

    content_card_start("Tạo hóa đơn")

    dat_phong_id = st.number_input(
        "Đặt phòng ID",
        min_value=1,
        value=default_dat_phong_id,
        help="Phải là dat_phong_id thật trong bảng DatPhong. Không dùng ct_dat_phong_id hoặc phong_id ở ô này."
    )

    staff_id = nullable_int_from_text(
        st.text_input(
            "Nhân viên lập hóa đơn ID",
            value="",
            placeholder="Để trống nếu procedure cho phép NULL"
        )
    )

    st.markdown(
        """
        <div class="step-box">
            <div class="step-title">Lưu ý quan trọng</div>
            <div class="step-text">
                Hóa đơn liên kết với <b>dat_phong_id</b>. Nếu nhập nhầm Chi tiết đặt phòng ID, Phân phòng ID,
                hoặc một ID không tồn tại trong DatPhong thì SQL Server sẽ báo lỗi khóa ngoại FK_HoaDon_DatPhong.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Tạo hóa đơn"):
        try:
            hoa_don_id = None
            try:
                result_df = db_exec_return_df(
                    """
                    SET NOCOUNT ON;
                    DECLARE @hoa_don_id INT;

                    EXEC dbo.sp_R2_TaoHoaDon
                        @dat_phong_id = ?,
                        @nhan_vien_lap_hoa_don_id = ?,
                        @hoa_don_id = @hoa_don_id OUTPUT;

                    SELECT @hoa_don_id AS hoa_don_id;
                    """,
                    [dat_phong_id, staff_id],
                )
                if result_df is not None and not result_df.empty and "hoa_don_id" in result_df.columns:
                    hoa_don_id = int(result_df.iloc[0]["hoa_don_id"])
            except Exception as main_error:
                if is_signature_error(main_error):
                    db_exec(
                        """
                        EXEC dbo.sp_R2_TaoHoaDon
                            @dat_phong_id = ?,
                            @nhan_vien_lap_hoa_don_id = ?;
                        """,
                        [dat_phong_id, staff_id],
                    )
                else:
                    raise main_error

            invoice_payload = {
                "hoa_don_id": hoa_don_id,
                "dat_phong_id": int(dat_phong_id),
                "created_at": datetime.now(),
            }
            st.session_state["last_created_invoice"] = invoice_payload
            save_workflow_state(last_created_invoice=invoice_payload)

            if hoa_don_id:
                st.success(f"Tạo hóa đơn thành công. Hóa đơn ID: {hoa_don_id}.")
                st.info("Bước tiếp theo: dùng Phân phòng ID đã lưu rồi bấm 'Thêm tiền phòng'.")
            else:
                st.success("Tạo hóa đơn thành công. Nếu procedure không trả ID, hãy tra hóa đơn vừa tạo trong view hóa đơn tổng hợp.")

        except Exception as e:
            err = str(e)
            if "FK_HoaDon_DatPhong" in err or "DatPhong" in err or "FOREIGN KEY" in err:
                st.error(
                    "Lỗi tạo hóa đơn: Đặt phòng ID bạn nhập không tồn tại trong DatPhong. "
                    "Hãy dùng đúng Đặt phòng ID được hiện ở màn hình Lễ tân sau khi tạo đặt phòng, "
                    "không dùng Chi tiết đặt phòng ID hoặc Phân phòng ID."
                )
                st.code(f"Đặt phòng ID đang nhập: {dat_phong_id}", language="text")
            else:
                st.error(f"Lỗi tạo hóa đơn: {e}")

    content_card_end()

    content_card_start("Thêm tiền phòng vào hóa đơn")

    last_invoice = load_saved_value("last_created_invoice", {}) or {}
    default_hoa_don_id = int(last_invoice.get("hoa_don_id") or default_hoa_don_id)

    col1, col2 = st.columns(2)

    with col1:
        hoa_don_id = st.number_input(
            "Hóa đơn ID",
            min_value=1,
            value=default_hoa_don_id,
            help="Là hoa_don_id vừa được procedure sp_R2_TaoHoaDon tạo."
        )

    with col2:
        phan_phong_id = st.number_input(
            "Phân phòng ID",
            min_value=1,
            value=default_phan_phong_id,
            help="Là phan_phong_id sau khi lễ tân phân phòng thành công."
        )

    so_dem = int(last_booking.get("so_dem") or last_assignment.get("so_dem") or 0)
    don_gia = float(last_booking.get("don_gia_mot_dem") or 0)
    giam_gia = float(last_booking.get("giam_gia") or 0)
    expected_total = max(so_dem * don_gia - giam_gia, 0.0) if so_dem and don_gia else None

    if expected_total is not None:
        st.markdown(
            f"""
            <div class="step-box">
                <div class="step-title">Tiền phòng dự kiến</div>
                <div class="step-text">
                    Đơn giá 1 đêm: <b>{safe_money(don_gia)}</b> × <b>{so_dem} đêm</b> - giảm giá <b>{safe_money(giam_gia)}</b><br>
                    Tạm tính tiền phòng: <b>{safe_money(expected_total)}</b>.<br>
                    Nếu chi tiết hóa đơn trong SQL vẫn chỉ bằng 1 ngày, cần kiểm tra lại logic trong procedure <b>sp_R2_ThemTienPhongVaoHoaDon</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Thêm tiền phòng"):
        try:
            db_exec(
                """
                EXEC dbo.sp_R2_ThemTienPhongVaoHoaDon
                    @hoa_don_id = ?,
                    @phan_phong_id = ?
                """,
                [hoa_don_id, phan_phong_id],
            )

            charge_payload = {
                "hoa_don_id": int(hoa_don_id),
                "phan_phong_id": int(phan_phong_id),
                "so_dem": so_dem,
                "don_gia_mot_dem": don_gia,
                "giam_gia": giam_gia,
                "tien_phong_du_kien": expected_total,
                "added_at": datetime.now(),
            }
            save_workflow_state(last_added_room_charge=charge_payload)
            st.success("Thêm tiền phòng vào hóa đơn thành công.")

        except Exception as e:
            st.error(f"Lỗi thêm tiền phòng: {e}")

    st.divider()
    st.info(
        "Thu ngân không xem trực tiếp view chi tiết hóa đơn nếu role chưa được cấp quyền. "
        "Sau khi thêm tiền phòng hoặc dịch vụ, kiểm tra tổng tiền ở màn hình 'Hóa đơn tổng hợp'. "
        "Kế toán/Quản lý sẽ đối soát chi tiết qua các view được phân quyền."
    )

    content_card_end()


# =========================================================
# 18. PAGE: THÊM DỊCH VỤ
# =========================================================


def page_service():
    page_title("Thêm dịch vụ phát sinh", "Chọn dịch vụ có hiển thị giá trước khi thêm vào hóa đơn.")

    last_assignment = load_saved_value("last_assigned_room", {}) or {}
    last_invoice = load_saved_value("last_created_invoice", {}) or {}
    last_charge = load_saved_value("last_added_room_charge", {}) or {}

    default_phan_phong_id = int(last_assignment.get("phan_phong_id") or last_charge.get("phan_phong_id") or 1)

    content_card_start("Kiểm tra trước khi thêm dịch vụ")
    st.markdown(
        """
        <div class="step-box">
            <div class="step-title">Điều kiện để thêm dịch vụ</div>
            <div class="step-text">
                Dịch vụ được thêm bằng <b>sp_R2_AddServiceUsage</b>. Procedure dùng <b>phan_phong_id</b>
                để tìm hóa đơn tương ứng, nên cần phân phòng đúng và đã lập hóa đơn trước đó.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    info_cols = st.columns(3)
    with info_cols[0]:
        metric_card("🛏️", "Phân phòng đang nhớ", last_assignment.get("phan_phong_id", "Chưa có"))
    with info_cols[1]:
        metric_card("🧾", "Hóa đơn đang nhớ", last_invoice.get("hoa_don_id", "Chưa có"))
    with info_cols[2]:
        metric_card("💵", "Tiền phòng đã thêm", last_charge.get("hoa_don_id", "Chưa có"))

    content_card_end()

    content_card_start("Thêm dịch vụ")

    catalog = get_service_catalog()
    option_map = {}
    for item in catalog:
        label = f"{item['dich_vu_id']} - {item['ten_dich_vu']} - {safe_money(item['gia_niem_yet'])}"
        option_map[label] = item

    col1, col2, col3 = st.columns([1, 1.45, 0.8])

    with col1:
        phan_phong_id = st.number_input(
            "Phân phòng ID",
            min_value=1,
            value=default_phan_phong_id,
            step=1,
            help="Đây là phan_phong_id, không phải dat_phong_id hoặc phong_id."
        )

    with col2:
        manual_service = st.checkbox(
            "Nhập dịch vụ ID thủ công",
            value=False,
            help="Bật nếu danh mục gợi ý trong app không khớp với ID dịch vụ thật trong SQL Server."
        )
        if manual_service:
            dich_vu_id = st.number_input("Dịch vụ ID", min_value=1, value=1, step=1)
            service_price = st.number_input("Đơn giá dịch vụ", min_value=0.0, value=float(SERVICE_PRICE_FALLBACK.get(int(dich_vu_id), 0.0)), step=10000.0)
            dich_vu_label = f"Dịch vụ ID {int(dich_vu_id)}"
        else:
            selected_label = st.selectbox("Dịch vụ", list(option_map.keys()))
            selected_service = option_map[selected_label]
            dich_vu_id = int(selected_service["dich_vu_id"])
            service_price = float(selected_service["gia_niem_yet"])
            dich_vu_label = f"{dich_vu_id} - {selected_service['ten_dich_vu']}"

    with col3:
        quantity = st.number_input("Số lượng", min_value=1, value=1, step=1)

    subtotal = float(service_price) * int(quantity)
    st.markdown(
        f"""
        <div class="step-box">
            <div class="step-title">Tạm tính dịch vụ</div>
            <div class="step-text">
                Dịch vụ: <b>{escape_text(dich_vu_label)}</b><br>
                Đơn giá: <b>{safe_money(service_price)}</b> × Số lượng: <b>{int(quantity)}</b><br>
                Tạm tính trước thuế: <b>{safe_money(subtotal)}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if catalog and catalog[0].get("source") == "fallback":
        st.caption("Đang dùng danh mục gợi ý trong app vì role hiện tại không đọc trực tiếp được view/bảng dịch vụ.")

    if st.button("Thêm dịch vụ"):
        try:
            db_exec(
                """
                EXEC dbo.sp_R2_AddServiceUsage
                    @phan_phong_id = ?,
                    @dich_vu_id = ?,
                    @so_luong = ?
                """,
                [int(phan_phong_id), int(dich_vu_id), int(quantity)],
            )

            service_payload = {
                "phan_phong_id": int(phan_phong_id),
                "dich_vu_id": int(dich_vu_id),
                "dich_vu_label": dich_vu_label,
                "so_luong": int(quantity),
                "don_gia": float(service_price),
                "tam_tinh": float(subtotal),
                "added_at": datetime.now(),
            }
            save_workflow_state(last_added_service=service_payload)
            st.success(f"Thêm dịch vụ thành công: {dich_vu_label} · Số lượng {int(quantity)} · Tạm tính {safe_money(subtotal)}.")
            st.info("Sau bước này, vào 'Hóa đơn tổng hợp' hoặc 'Thanh toán' để kiểm tra số tiền còn lại.")

        except Exception as e:
            err = str(e)
            low = err.lower()
            if "hoa don" in low or "hóa đơn" in low:
                st.error("Không thêm được dịch vụ vì chưa tìm thấy hóa đơn tương ứng với phân phòng này. Hãy lập hóa đơn trước.")
                st.caption(err)
            elif "dịch vụ" in low or "dich vu" in low:
                st.error("Không thêm được dịch vụ vì Dịch vụ ID có thể không tồn tại. Hãy bật nhập ID thủ công và nhập đúng ID trong SQL Server.")
                st.caption(err)
            elif "permission" in low or "denied" in low:
                st.error("Tài khoản thu ngân chưa có quyền EXECUTE procedure thêm dịch vụ hoặc chưa được cấp quyền liên quan.")
                st.caption(err)
            else:
                st.error(f"Lỗi thêm dịch vụ: {e}")

    content_card_end()


def page_payment():
    page_title("Thanh toán", "Ghi nhận thanh toán cho hóa đơn bằng stored procedure. Thanh toán phải thực hiện trước check-out.")

    last_invoice = load_saved_value("last_created_invoice", {}) or {}
    last_checkout = load_saved_value("last_checkout", {}) or {}
    default_invoice_id = int(last_invoice.get("hoa_don_id") or 1)

    content_card_start("Ghi nhận thanh toán")

    if last_checkout:
        st.warning(
            "App có lưu một lượt check-out gần nhất. Nếu hóa đơn đang chọn thuộc lượt đã check-out đó, app sẽ chặn thanh toán mới. "
            "Với luồng mới, bạn vẫn có thể thanh toán bình thường."
        )

    try:
        invoice_df = load_recent_invoices()
    except Exception:
        invoice_df = pd.DataFrame()

    invoice_row = pd.DataFrame()
    suggested_amount = 100000.0

    if not invoice_df.empty and "hoa_don_id" in invoice_df.columns:
        invoice_options = {}
        selected_index = 0
        for idx, (_, r) in enumerate(invoice_df.iterrows()):
            invoice_id = int(r["hoa_don_id"])
            invoice_no = safe_text(r.get("so_hoa_don", ""))
            remain = r.get("so_tien_con_lai", 0)
            label = f"{invoice_id} - {invoice_no} - Còn lại {safe_money(remain)}"
            invoice_options[label] = invoice_id
            if invoice_id == default_invoice_id:
                selected_index = idx
        labels = list(invoice_options.keys())
        selected_invoice = st.selectbox("Hóa đơn", labels, index=min(selected_index, len(labels) - 1))
        hoa_don_id = invoice_options[selected_invoice]
        invoice_row = invoice_df[invoice_df["hoa_don_id"] == hoa_don_id]
        if not invoice_row.empty and "so_tien_con_lai" in invoice_row.columns:
            try:
                suggested_amount = max(float(invoice_row.iloc[0]["so_tien_con_lai"]), 0.0)
            except Exception:
                suggested_amount = 100000.0
    else:
        st.warning("Không tải được view hóa đơn tổng hợp. Nhập hóa đơn ID thủ công.")
        hoa_don_id = st.number_input("Hóa đơn ID", min_value=1, value=default_invoice_id)

    col1, col2 = st.columns(2)

    with col1:
        phuong_thuc_id, phuong_thuc_label = select_reference(
            label="Phương thức thanh toán",
            sql="""
                SELECT phuong_thuc_id, ten_phuong_thuc
                FROM dbo.v_R5_PhuongThucThanhToan
                ORDER BY phuong_thuc_id
            """,
            value_col="phuong_thuc_id",
            label_cols=["phuong_thuc_id", "ten_phuong_thuc"],
            fallback_items=PAYMENT_METHOD_FALLBACK,
            help_text="Chọn tên phương thức. Nếu role không có quyền SELECT, app dùng danh mục gợi ý."
        )
        staff_id = nullable_int_from_text(
            st.text_input("Nhân viên thu tiền ID", value="", placeholder="Để trống nếu procedure cho phép NULL")
        )

    with col2:
        amount = st.number_input("Số tiền thanh toán", min_value=0.0, value=float(suggested_amount), step=50000.0)
        customer_paid_text = st.text_input("Số tiền khách đưa", value="", placeholder="Chỉ nhập nếu thanh toán tiền mặt; để trống với QR/chuyển khoản/thẻ")
        customer_paid = parse_nullable_decimal(customer_paid_text)
        transaction_code = st.text_input("Mã giao dịch", value="", placeholder="Nhập nếu phương thức yêu cầu mã giao dịch")
        transaction_code = transaction_code.strip() or None

    if not invoice_row.empty:
        st.markdown("#### Tóm tắt hóa đơn")
        safe_dataframe(invoice_row, height=160)

    st.caption(f"Phương thức đã chọn: {phuong_thuc_label}. Nếu không phải tiền mặt, nên để trống 'Số tiền khách đưa' để tránh trigger chặn.")

    if st.button("Ghi nhận thanh toán"):
            try:
                db_exec(
                    """
                    EXEC dbo.sp_R2_GhiNhanThanhToan
                        @hoa_don_id = ?,
                        @nhan_vien_thu_tien_id = ?,
                        @phuong_thuc_id = ?,
                        @so_tien_thanh_toan = ?,
                        @so_tien_khach_dua = ?,
                        @ma_giao_dich = ?
                    """,
                    [hoa_don_id, staff_id, phuong_thuc_id, amount, customer_paid, transaction_code],
                )
                payment_payload = {
                    "hoa_don_id": int(hoa_don_id),
                    "phuong_thuc_id": int(phuong_thuc_id),
                    "phuong_thuc_label": phuong_thuc_label,
                    "so_tien_thanh_toan": float(amount),
                    "so_tien_khach_dua": customer_paid,
                    "ma_giao_dich": transaction_code,
                    "paid_at": datetime.now(),
                }
                save_workflow_state(last_payment=payment_payload)
                
                st.success("Ghi nhận thanh toán thành công. Bây giờ có thể quay lại Lễ tân để check-out.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi thanh toán: {e}")

    st.divider()
    st.subheader("Lịch sử thanh toán của hóa đơn")
    try:
        history_df = db_query(
            """
            SELECT *
            FROM dbo.v_R2_ThanhToanChiTiet
            WHERE hoa_don_id = ?
            ORDER BY ngay_thanh_toan DESC
            """,
            [hoa_don_id],
        )
        safe_dataframe(history_df, height=300)
    except Exception as e:
        st.info(f"Không tải được lịch sử thanh toán: {e}")

    content_card_end()


def page_invoice_summary():
    page_title("Hóa đơn tổng hợp", "Xem tổng tiền phòng, tiền dịch vụ, đã thanh toán và số tiền còn lại.")

    content_card_start("Bộ lọc hóa đơn")

    keyword = st.text_input("Tìm kiếm nhanh", placeholder="Nhập mã hóa đơn, trạng thái, mã đặt phòng...")

    try:
        df = load_recent_invoices()

        if keyword.strip():
            keyword_lower = keyword.strip().lower()
            mask = pd.Series([False] * len(df))
            for col in df.columns:
                mask = mask | df[col].astype(str).str.lower().str.contains(keyword_lower, na=False)
            df = df[mask]

        safe_dataframe(df, height=560)

    except Exception as e:
        st.error(f"Lỗi tải hóa đơn tổng hợp: {e}")

    content_card_end()


# =========================================================
# 21. PAGE: CÔNG NỢ
# =========================================================

def page_debt():
    page_title("Công nợ", "Danh sách hóa đơn còn số tiền chưa thanh toán.")

    content_card_start("Hóa đơn còn nợ")

    try:
        try:
            df = db_query("EXEC dbo.sp_R2_TraCuuHoaDonCongNo")
        except Exception:
            df = db_query(
                """
                SELECT *
                FROM dbo.v_R2_HoaDonTongHop
                WHERE ISNULL(so_tien_con_lai, 0) > 0
                ORDER BY ngay_lap DESC
                """
            )

        safe_dataframe(df, height=560)

    except Exception as e:
        st.error(f"Lỗi tra cứu công nợ: {e}")

    content_card_end()


# =========================================================
# 22. PAGE: LỊCH SỬ THANH TOÁN
# =========================================================

def page_payment_history():
    page_title("Lịch sử thanh toán", "Theo dõi các giao dịch thanh toán đã phát sinh.")

    content_card_start("Lịch sử thanh toán")

    invoice_id_text = st.text_input("Lọc theo hóa đơn ID", value="", placeholder="Để trống để xem tất cả")

    try:
        invoice_id = nullable_int_from_text(invoice_id_text)

        if invoice_id is None:
            df = db_query(
                """
                SELECT TOP 500 *
                FROM dbo.v_R2_ThanhToanChiTiet
                ORDER BY ngay_thanh_toan DESC
                """
            )
        else:
            df = db_query(
                """
                SELECT TOP 500 *
                FROM dbo.v_R2_ThanhToanChiTiet
                WHERE hoa_don_id = ?
                ORDER BY ngay_thanh_toan DESC
                """,
                [invoice_id],
            )

        safe_dataframe(df, height=560)

    except Exception as e:
        st.error(f"Lỗi tải lịch sử thanh toán: {e}")

    content_card_end()


# =========================================================
# 23. PAGE: BÁO CÁO DOANH THU
# =========================================================

def page_revenue_report():
    page_title("Báo cáo doanh thu", "Tổng hợp doanh thu phát sinh, thực thu và công nợ theo tháng.")

    content_card_start("Chọn kỳ báo cáo")

    report_year = st.number_input("Năm báo cáo", min_value=2020, max_value=2035, value=datetime.now().year)

    if st.button("Xem báo cáo doanh thu"):
        try:
            try:
                df = db_query(
                    "EXEC dbo.sp_R2_BaoCaoDoanhThuTheoThang @nam = ?",
                    [report_year],
                )
            except Exception:
                df = db_query(
                    """
                    SELECT
                        YEAR(ngay_lap) AS nam,
                        MONTH(ngay_lap) AS thang,
                        SUM(ISNULL(tong_can_thanh_toan, 0)) AS doanh_thu_phat_sinh,
                        SUM(ISNULL(tong_da_thanh_toan, 0)) AS doanh_thu_thuc_thu,
                        SUM(ISNULL(so_tien_con_lai, 0)) AS cong_no
                    FROM dbo.v_R2_HoaDonTongHop
                    WHERE YEAR(ngay_lap) = ?
                    GROUP BY YEAR(ngay_lap), MONTH(ngay_lap)
                    ORDER BY thang
                    """,
                    [report_year],
                )

            if df.empty:
                st.info("Không có dữ liệu báo cáo.")
            else:
                safe_dataframe(df, height=330)

                chart_cols = [
                    col for col in df.select_dtypes(include="number").columns
                    if col not in ["nam", "thang"]
                ]

                if "thang" in df.columns and chart_cols:
                    st.markdown("#### Biểu đồ doanh thu")
                    st.bar_chart(df.set_index("thang")[chart_cols])

        except Exception as e:
            st.error(f"Lỗi báo cáo doanh thu: {e}")

    content_card_end()


# =========================================================
# 24. PAGE: KHÁCH HÀNG THÂN THIẾT
# =========================================================

def page_loyal_customers():
    page_title("Khách hàng thân thiết", "Xếp hạng khách hàng bằng stored procedure báo cáo.")

    content_card_start("Lọc khách hàng thân thiết")

    top_n = st.number_input("Top N khách hàng", min_value=1, max_value=100, value=10)

    if st.button("Lọc khách hàng"):
        try:
            df = db_query(
                "EXEC dbo.sp_R2_LocKhachHangThanThiet @top_n = ?",
                [top_n],
            )

            safe_dataframe(df, height=520)

        except Exception as e:
            st.error(f"Lỗi lọc khách hàng thân thiết: {e}")

    content_card_end()


# =========================================================
# 25. PAGE: AUDIT LOG
# =========================================================

def page_audit_log():
    page_title("AuditLog", "Theo dõi thao tác quan trọng trong hệ thống.")

    content_card_start("Nhật ký thao tác")

    keyword = st.text_input("Tìm kiếm trong AuditLog", placeholder="Nhập tên bảng, thao tác, người dùng...")

    try:
        try:
            df = db_query(
                """
                SELECT TOP 500 *
                FROM dbo.AuditLog
                ORDER BY audit_id DESC
                """
            )
        except Exception:
            df = db_query(
                """
                SELECT TOP 500 *
                FROM dbo.AuditLog
                """
            )

        if keyword.strip():
            keyword_lower = keyword.strip().lower()
            mask = pd.Series([False] * len(df))
            for col in df.columns:
                mask = mask | df[col].astype(str).str.lower().str.contains(keyword_lower, na=False)
            df = df[mask]

        safe_dataframe(df, height=560)

    except Exception as e:
        st.error(f"Không thể xem AuditLog hoặc không có quyền: {e}")

    content_card_end()


# =========================================================
# 26. MAIN ROUTER
# =========================================================

def main():
    if not st.session_state["logged_in"]:
        render_login_page()
        return

    render_topbar()
    render_hero()
    selected_menu = render_nav()

    if selected_menu == "Trang chủ":
        page_home()

    elif selected_menu == "Dashboard":
        page_dashboard()

    elif selected_menu == "Khách hàng":
        page_customers()

    elif selected_menu == "Tạo đặt phòng":
        page_create_booking()

    elif selected_menu == "Tìm phòng trống":
        page_room_search()

    elif selected_menu == "Phân phòng":
        page_assign_room()

    elif selected_menu == "Huỷ đặt phòng":
        page_cancel_booking()

    elif selected_menu == "Check-in / Check-out":
        page_checkin_checkout()

    elif selected_menu == "Lập hóa đơn":
        page_invoice()

    elif selected_menu == "Thêm dịch vụ":
        page_service()

    elif selected_menu == "Thanh toán":
        page_payment()

    elif selected_menu == "Hóa đơn tổng hợp":
        page_invoice_summary()

    elif selected_menu == "Công nợ":
        page_debt()

    elif selected_menu == "Lịch sử thanh toán":
        page_payment_history()

    elif selected_menu == "Báo cáo doanh thu":
        page_revenue_report()

    elif selected_menu == "Khách hàng thân thiết":
        page_loyal_customers()

    elif selected_menu == "AuditLog":
        page_audit_log()

    else:
        st.info("Chức năng đang được phát triển.")


main()
