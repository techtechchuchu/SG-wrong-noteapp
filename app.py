import io
import base64
import re
import hashlib
from collections import Counter
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

import pandas as pd
import streamlit as st
from supabase import Client, create_client


# ---------------------- 기본 설정 ----------------------
st.set_page_config(
    page_title="SG 고등관 오답노트",
    page_icon="📝",
    layout="centered"
)

BANNER_PATH = Path("sg_banner.png")

BOOKS = [
    "공통수학2 고쟁이",
    "공통수학2 RPM",
    "미적분1 고쟁이",
    "확통 고쟁이",
    "미적분2 쎈",
    "기하 쎈",
    "마플교과서 공통수학1",
    "공통수학1 RPM"
]


TEACHERS = ["이주백.T", "박병민.T", "노대근.T"]
ALL_TEACHER_ADMIN = "전체 관리자"

ROSTER_REQUIRED_COLUMNS = {
    "반명",
    "담당선생님",
    "학생명",
    "학교명",
    "학년",
}

GRADES = ["중3", "고1", "고2", "고3"]

try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    ADMIN_PASSWORD = None

try:
    STUDENT_SIGNUP_CODE = st.secrets["STUDENT_SIGNUP_CODE"]
except Exception:
    STUDENT_SIGNUP_CODE = None


try:
    SUPERADMIN_PASSWORD = st.secrets["SUPERADMIN_PASSWORD"]
except Exception:
    SUPERADMIN_PASSWORD = None



try:
    SUPABASE_URL = str(st.secrets["SUPABASE_URL"]).strip().rstrip("/")
    SUPABASE_KEY = str(st.secrets["SUPABASE_KEY"]).strip()
except Exception:
    st.error(
        "Supabase 연결 정보가 없습니다. "
        "Streamlit의 Settings → Secrets에 "
        "SUPABASE_URL과 SUPABASE_KEY를 입력해주세요."
    )
    st.stop()


@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase_client()
KST = ZoneInfo("Asia/Seoul")


def now_kst_iso() -> str:
    """Supabase timestamp 컬럼에 저장할 한국 시간 문자열입니다."""
    return datetime.now(KST).replace(tzinfo=None).isoformat(timespec="seconds")


def get_qr_signup_code():
    try:
        return st.query_params.get("code", "")
    except Exception:
        return ""



def apply_global_style():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(40, 180, 170, 0.05), transparent 28%),
                linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
        }

        .block-container {
            max-width: 980px;
            padding-top: 2rem;
            padding-bottom: 8.5rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.03em;
        }

        div[data-testid="stButton"] > button {
            min-height: 3.15rem;
            border-radius: 12px;
            font-weight: 700;
            border: 1px solid #d8dde6;
            transition: all 0.18s ease;
            white-space: pre-line;
        }

        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(31, 41, 55, 0.08);
            border-color: #aab4c3;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            border-radius: 10px;
        }

        div[data-testid="stExpander"] {
            border-radius: 12px;
            border: 1px solid #e3e7ed;
            overflow: hidden;
        }

        .sg-role-title {
            margin-top: 1.2rem;
            margin-bottom: 0.25rem;
            font-size: 2.1rem;
            font-weight: 900;
            color: #202938;
            letter-spacing: -0.04em;
        }

        .sg-role-subtitle {
            color: #586174;
            margin-bottom: 1rem;
            font-size: 1rem;
        }

        .sg-info-box {
            margin-top: 1rem;
            padding: 14px 16px;
            border-radius: 12px;
            background: #eef6ff;
            border: 1px solid #cfe3fb;
            color: #35506f;
            font-size: 14px;
            line-height: 1.65;
        }

        .sg-account-notice {
            width: 100%;
            box-sizing: border-box;
            margin: 2px 0 22px;
            padding: 16px 18px;
            border: 1px solid #cfe3fb;
            border-left: 5px solid #2878c8;
            border-radius: 13px;
            background: linear-gradient(135deg, #f5faff 0%, #edf6ff 100%);
            color: #2e4f6d;
            line-height: 1.7;
            box-shadow: 0 5px 16px rgba(40, 120, 200, 0.07);
        }

        .sg-account-notice-title {
            margin-bottom: 6px;
            color: #15599d;
            font-size: 17px;
            font-weight: 850;
        }

        .sg-account-notice-text {
            font-size: 14px;
            word-break: keep-all;
            overflow-wrap: anywhere;
        }

        .sg-logo-wrap {
            width: 100%;
            min-height: 92px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            box-sizing: border-box;
            padding: 10px 8px 14px 8px;
            overflow: visible;
        }

        .sg-logo-wrap img {
            display: block;
            width: 320px;
            max-width: 82vw;
            height: auto;
            object-fit: contain;
        }

        .sg-footer {
            position: fixed;
            left: 50%;
            bottom: 0;
            transform: translateX(-50%);
            z-index: 9999;
            width: min(980px, calc(100% - 2rem));
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 6px 12px;
            padding: 9px 14px 10px;
            border: 1px solid #e7ebf0;
            border-bottom: 0;
            border-radius: 14px 14px 0 0;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(8px);
            text-align: center;
            color: #7d8798;
            font-size: 12px;
            line-height: 1.4;
            box-shadow: 0 -5px 18px rgba(31, 41, 55, 0.07);
        }

        .sg-footer-text {
            display: flex;
            flex-direction: column;
            gap: 1px;
        }

        .sg-footer-credit {
            white-space: nowrap;
        }

        .sg-contact-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 34px;
            padding: 6px 13px;
            border: 1px solid #e3cd00;
            border-radius: 9px;
            background: #fee500;
            color: #191919 !important;
            text-decoration: none !important;
            font-size: 13px;
            font-weight: 800;
            line-height: 1;
            white-space: nowrap;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .sg-contact-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 5px 12px rgba(25, 25, 25, 0.12);
        }

        .sg-notice-card {
            box-sizing: border-box;
            width: 100%;
            margin: 16px 0 24px 0;
            padding: 24px 26px;
            border: 1px solid #ead5cf;
            border-left: 6px solid #a62c20;
            border-radius: 16px;
            background: linear-gradient(135deg, #fffdfa 0%, #fff7f3 100%);
            color: #252b35;
            line-height: 1.72;
            box-shadow: 0 10px 28px rgba(87, 49, 38, 0.08);
            overflow: visible;
        }

        .sg-notice-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 14px;
            color: #8f241b;
            font-size: 23px;
            font-weight: 900;
            letter-spacing: -0.5px;
        }

        .sg-notice-intro,
        .sg-notice-foot {
            font-size: 16px;
            word-break: keep-all;
            overflow-wrap: anywhere;
        }

        .sg-temp-password {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 18px 0;
            padding: 14px 17px;
            border: 1px solid #ead8d2;
            border-radius: 12px;
            background: #ffffff;
        }

        .sg-lock {
            flex: 0 0 auto;
            font-size: 21px;
        }

        .sg-temp-label {
            flex: 0 1 auto;
            color: #364152;
            font-size: 16px;
            font-weight: 800;
            white-space: nowrap;
        }

        .sg-temp-value {
            flex: 0 0 auto;
            padding: 5px 12px;
            border-radius: 9px;
            background: #fff0e8;
            color: #b3261e;
            font-size: 21px;
            font-weight: 900;
        }

        .sg-action-box {
            margin-top: 16px;
            padding: 16px 18px;
            border: 1px solid #cfe3f6;
            border-radius: 12px;
            background: #eef7ff;
        }

        .sg-action-title {
            margin-bottom: 10px;
            color: #174b87;
            font-size: 17px;
            font-weight: 850;
        }

        .sg-action-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin: 8px 0;
            font-size: 16px;
            word-break: keep-all;
            overflow-wrap: anywhere;
        }

        .sg-action-item strong {
            color: #174b87;
        }

        .sg-action-number {
            display: inline-flex;
            flex: 0 0 24px;
            width: 24px;
            height: 24px;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: #174b87;
            color: #ffffff;
            font-size: 13px;
            font-weight: 800;
            line-height: 1;
        }

        .sg-notice-foot {
            margin-top: 16px;
            color: #5d6470;
            font-size: 15px;
        }

        .sg-signature {
            margin-top: 18px;
            text-align: center;
            color: #303846;
            font-size: 16px;
            font-weight: 800;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
                padding-bottom: 9rem;
            }

            .sg-logo-wrap {
                min-height: 76px;
                padding: 8px 2px 10px;
            }

            .sg-logo-wrap img {
                width: 285px;
                max-width: 90vw;
            }

            .sg-footer {
                width: calc(100% - 0.75rem);
                gap: 5px 8px;
                padding: 8px 9px 9px;
                font-size: 10.5px;
            }

            .sg-contact-button {
                min-height: 32px;
                padding: 6px 11px;
                font-size: 12px;
            }

            .sg-footer-credit {
                width: 100%;
            }

            .sg-notice-card {
                margin-top: 10px;
                padding: 18px 16px;
                border-left-width: 5px;
                border-radius: 14px;
            }

            .sg-notice-title {
                font-size: 20px;
            }

            .sg-notice-intro,
            .sg-action-item {
                font-size: 15px;
                line-height: 1.65;
            }

            .sg-temp-password {
                display: grid;
                grid-template-columns: auto 1fr;
                gap: 8px 10px;
                padding: 13px 14px;
            }

            .sg-temp-label {
                white-space: normal;
            }

            .sg-temp-value {
                grid-column: 1 / -1;
                justify-self: stretch;
                text-align: center;
                font-size: 20px;
            }

            .sg-action-box {
                padding: 14px;
            }

            .sg-action-title {
                font-size: 16px;
            }

            .sg-notice-foot {
                font-size: 14px;
            }

            .sg-role-title {
                font-size: 1.7rem;
            }

            div[data-testid="stButton"] > button {
                min-height: 4.25rem;
                font-size: 0.95rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# ---------------------- 배너 ----------------------
def show_banner():
    """SG고등관 로고가 잘리지 않도록 여백을 포함해 표시합니다."""
    if not BANNER_PATH.exists():
        return

    image_base64 = base64.b64encode(BANNER_PATH.read_bytes()).decode("utf-8")
    image_suffix = BANNER_PATH.suffix.lower().lstrip(".") or "png"
    image_mime = "jpeg" if image_suffix in {"jpg", "jpeg"} else image_suffix

    logo_html = (
        '<div class="sg-logo-wrap">'
        f'<img src="data:image/{image_mime};base64,{image_base64}" '
        'alt="SG고등관 로고">'
        '</div>'
    )
    st.markdown(logo_html, unsafe_allow_html=True)



def show_account_notice():
    """역할 선택 및 로그인 화면에 계정 정리 공지를 표시합니다."""
    notice_html = (
        '<div class="sg-account-notice">'
        '<div class="sg-account-notice-title">📢 계정 이용 안내</div>'
        '<div class="sg-account-notice-text">'
        '기존 학생들의 <strong>중복 계정을 정리</strong>했습니다.<br>'
        '모든 학생 계정은 <strong>본인 이름으로 수정 완료</strong>했습니다.<br>'
        '<strong>비밀번호 오류 및 계정 관리 등 문의사항은 화면 하단의 '
        '오픈채팅 문의를 이용해주시기 바랍니다.</strong>'
        '</div>'
        '</div>'
    )
    st.markdown(notice_html, unsafe_allow_html=True)


def show_global_footer():
    """모든 화면 하단에 안내 및 카카오 오픈채팅 버튼을 고정 표시합니다."""
    footer_html = (
        '<div class="sg-footer">'
        '<div class="sg-footer-text">'
        '<span>SG고등관 재원생 및 직원 전용 학습관리 시스템입니다.</span>'
        '<span>계정 공유 및 타인의 계정 사용을 금지합니다.</span>'
        '</div>'
        '<a class="sg-contact-button" '
        'href="https://open.kakao.com/o/sLgsIMFi" '
        'target="_blank" rel="noopener noreferrer">'
        '💬 오픈채팅 문의'
        '</a>'
        '<div class="sg-footer-credit">'
        '© 2026 techtechchu · Developed for SG고등관'
        '</div>'
        '</div>'
    )
    st.markdown(footer_html, unsafe_allow_html=True)


# ---------------------- Supabase 연결 ----------------------
def verify_supabase_connection():
    """앱 시작 시 Supabase 연결과 각 테이블을 순서대로 확인합니다."""
    if not SUPABASE_URL.startswith("https://"):
        st.error("SUPABASE_URL 형식이 올바르지 않습니다.")
        st.code("https://프로젝트ID.supabase.co")
        st.stop()

    if not SUPABASE_KEY:
        st.error("SUPABASE_KEY가 비어 있습니다.")
        st.stop()

    checks = [
        ("users", "username"),
        ("wrong_answers", "id"),
        ("student_roster", "id"),
        ("print_status", "id"),
        ("book_master", "id"),
        ("school_exam_master", "id"),
        ("school_exam_wrong_answers", "id"),
    ]

    for table_name, column_name in checks:
        try:
            (
                supabase.table(table_name)
                .select(column_name)
                .limit(1)
                .execute()
            )
        except Exception as error:
            st.error(f"Supabase의 '{table_name}' 테이블 연결에 실패했습니다.")
            st.code(
                f"{type(error).__name__}: {error}",
                language="text"
            )
            st.info(
                "위 오류 문구를 확인하면 URL·API Key·테이블·권한 중 "
                "어느 부분이 문제인지 정확히 알 수 있습니다."
            )
            st.stop()


def fetch_all_rows(
    table_name: str,
    columns: str = "*",
    *,
    filters: list[tuple[str, str, object]] | None = None,
    order_column: str | None = None,
    desc: bool = False,
    page_size: int = 1000
) -> list[dict]:
    """PostgREST 행 제한을 고려하여 전체 데이터를 페이지 단위로 가져옵니다."""
    all_rows: list[dict] = []
    start = 0

    while True:
        query = supabase.table(table_name).select(columns)

        for column, operation, value in filters or []:
            if operation == "eq":
                query = query.eq(column, value)
            elif operation == "neq":
                query = query.neq(column, value)
            elif operation == "in":
                query = query.in_(column, value)
            else:
                raise ValueError(f"지원하지 않는 필터 연산입니다: {operation}")

        if order_column:
            query = query.order(order_column, desc=desc)

        response = query.range(start, start + page_size - 1).execute()
        rows = response.data or []
        all_rows.extend(rows)

        if len(rows) < page_size:
            break

        start += page_size

    return all_rows



# ---------------------- 학생 명단·반·교재 관리 ----------------------
def normalize_teacher_name(value) -> str:
    """
    담당 선생님 표기의 공백·점·영문 대소문자 차이를 자동 통일합니다.

    예:
    - 노대근T / 노대근.T / 노대근t / 노대근.t → 노대근.T
    - 이주백T / 이주백.T / 이주백t / 이주백.t → 이주백.T
    - 새 선생님도 이름 뒤에 T 또는 t가 있으면 자동으로 '이름.T'로 변환됩니다.
    """
    raw = str(value or "").strip()

    if not raw:
        return ""

    compact = re.sub(r"\s+", "", raw)

    # 이름 뒤의 T, t, .T, .t를 모두 제거한 뒤 표준 '.T'를 붙입니다.
    teacher_match = re.fullmatch(r"(.+?)(?:\.?[Tt])", compact)

    if teacher_match:
        teacher_base = teacher_match.group(1).rstrip(".")
        return f"{teacher_base}.T"

    return raw


def normalize_roster_grade(value) -> str:
    """엑셀의 1, 2, 3 또는 고1, 고2 형식을 앱 학년 형식으로 통일합니다."""
    raw = str(value or "").strip()

    if raw.lower() == "nan" or not raw:
        return "미지정"

    if raw in {"1", "1.0"}:
        return "고1"
    if raw in {"2", "2.0"}:
        return "고2"
    if raw in {"3", "3.0"}:
        return "중3"

    return raw


def get_roster_df() -> pd.DataFrame:
    rows = fetch_all_rows(
        "student_roster",
        "id,class_name,teacher_name,student_name,school_name,grade,book_name,created_at",
        order_column="teacher_name",
        desc=False,
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "기록ID", "반명", "담당선생님", "학생명",
                "학교명", "학년", "매칭교재", "등록일시"
            ]
        )

    return pd.DataFrame(
        [
            {
                "기록ID": row.get("id"),
                "반명": row.get("class_name", ""),
                "담당선생님": normalize_teacher_name(
                    row.get("teacher_name", "")
                ),
                "학생명": row.get("student_name", ""),
                "학교명": row.get("school_name", ""),
                "학년": row.get("grade", ""),
                "매칭교재": row.get("book_name", ""),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ]
    )


def import_roster_from_excel(uploaded_file) -> dict:
    """최종 학생명단 엑셀의 '학생명단' 시트를 Supabase에 일괄 저장합니다."""
    df = pd.read_excel(uploaded_file, sheet_name="학생명단")
    missing = ROSTER_REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            "명단 엑셀에 필요한 열이 없습니다: " + ", ".join(sorted(missing))
        )

    if "매칭교재" not in df.columns:
        df["매칭교재"] = ""

    clean_df = df[
        ["반명", "담당선생님", "학생명", "학교명", "학년", "매칭교재"]
    ].copy()

    for column in ["반명", "담당선생님", "학생명", "학교명", "매칭교재"]:
        clean_df[column] = clean_df[column].fillna("").astype(str).str.strip()

    clean_df["담당선생님"] = clean_df["담당선생님"].apply(
        normalize_teacher_name
    )
    clean_df["학년"] = clean_df["학년"].apply(normalize_roster_grade)
    clean_df = clean_df[
        (clean_df["학생명"] != "")
        & (clean_df["반명"] != "")
        & (clean_df["담당선생님"] != "")
    ].drop_duplicates(
        subset=["반명", "담당선생님", "학생명"]
    )

    rows = [
        {
            "class_name": row["반명"],
            "teacher_name": row["담당선생님"],
            "student_name": row["학생명"],
            "school_name": row["학교명"],
            "grade": row["학년"],
            "book_name": row["매칭교재"],
            "created_at": now_kst_iso(),
        }
        for _, row in clean_df.iterrows()
    ]

    # 명단은 최신 업로드본을 기준으로 전체 교체
    supabase.table("student_roster").delete().neq("id", 0).execute()

    if rows:
        supabase.table("student_roster").insert(rows).execute()

    return {
        "count": len(rows),
        "teachers": sorted(clean_df["담당선생님"].unique().tolist()),
        "classes": sorted(clean_df["반명"].unique().tolist()),
    }


def get_student_roster_rows(username: str) -> pd.DataFrame:
    roster = get_roster_df()

    if roster.empty:
        return roster

    return roster[roster["학생명"] == username].copy()


def get_book_master_df(active_only: bool = True) -> pd.DataFrame:
    filters = [("is_active", "eq", True)] if active_only else []

    rows = fetch_all_rows(
        "book_master",
        (
            "id,book_name,grade,subject,publisher,"
            "question_count,category,is_active,created_at"
        ),
        filters=filters,
        order_column="book_name",
        desc=False,
    )

    columns = [
        "교재ID", "교재명", "학년", "과목", "출판사",
        "문항수", "분류", "사용중", "등록일시",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "교재ID": row.get("id"),
                "교재명": row.get("book_name", ""),
                "학년": row.get("grade", ""),
                "과목": row.get("subject", ""),
                "출판사": row.get("publisher", ""),
                "문항수": row.get("question_count"),
                "분류": row.get("category", "교재"),
                "사용중": bool(row.get("is_active", True)),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ],
        columns=columns,
    )


def get_active_book_names() -> list[str]:
    try:
        book_df = get_book_master_df(active_only=True)

        if not book_df.empty:
            names = (
                book_df["교재명"]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )
            return list(dict.fromkeys(name for name in names if name))
    except Exception:
        pass

    return BOOKS.copy()


def get_student_allowed_books(username: str) -> list[str]:
    """현재 관리자 화면에서 사용 중으로 설정된 교재를 반환합니다."""
    return get_active_book_names()


def get_teacher_student_status_df() -> pd.DataFrame:
    """명단 기준으로 학생별 오답 작성 여부와 문제 개수를 계산합니다."""
    roster = get_roster_df()

    if roster.empty:
        return pd.DataFrame(
            columns=[
                "담당선생님", "반명", "학생명", "학교명",
                "학년", "매칭교재", "작성여부", "작성문제수", "최근작성일시"
            ]
        )

    answer_rows = fetch_all_rows(
        "wrong_answers",
        "username,unit,problem,created_at",
        order_column="id",
        desc=False,
    )

    answer_map: dict[tuple[str, str], dict] = {}

    for row in answer_rows:
        key = (
            str(row.get("username", "")).strip(),
            str(row.get("unit", "")).strip(),
        )
        info = answer_map.setdefault(
            key,
            {"numbers": [], "latest": ""}
        )

        for number in parse_problem_numbers(row.get("problem", "")):
            if number not in info["numbers"]:
                info["numbers"].append(number)

        created_at = str(row.get("created_at", ""))
        if created_at > info["latest"]:
            info["latest"] = created_at

    records = []

    for _, row in roster.iterrows():
        key = (str(row["학생명"]), str(row["매칭교재"]))
        answer = answer_map.get(key, {"numbers": [], "latest": ""})
        count = len(answer["numbers"])

        records.append(
            {
                "담당선생님": row["담당선생님"],
                "반명": row["반명"],
                "학생명": row["학생명"],
                "학교명": row["학교명"],
                "학년": row["학년"],
                "매칭교재": row["매칭교재"],
                "작성여부": "O" if count > 0 else "X",
                "작성문제수": count,
                "최근작성일시": answer["latest"],
            }
        )

    return pd.DataFrame(records)


def simplify_class_for_paper(class_name: str, grade: str, book_name: str) -> str:
    """
    PDF 상단 제목에 들어갈 짧은 수업명 생성.
    예: 화목토일(앞) 고2 미적분1 → 고2 미적분1
    """
    class_name = str(class_name or "").strip()
    grade = str(grade or "").strip()

    subject_map = {
        "미적분1 고쟁이": "미적분1",
        "확통 고쟁이": "확통",
        "미적분2 쎈": "미적분2",
        "기하 쎈": "기하",
        "공통수학2 고쟁이": "공통수학2",
        "공통수학2 RPM": "공통수학2",
        "마플교과서 공통수학1": "공통수학1",
        "공통수학1 RPM": "공통수학1",
    }

    subject = subject_map.get(book_name, "")
    if grade and subject:
        return f"{grade} {subject}"

    # 요일 및 앞/뒤 표기를 제거한 보조 처리
    cleaned = re.sub(r"^(월|화|수|목|금|토|일|,|\(|\)|앞|뒤)+\s*", "", class_name)
    return cleaned or class_name


def build_paper_title(
    teacher_name: str,
    class_name: str,
    grade: str,
    book_name: str,
    month: int,
    week: int
) -> str:
    teacher = str(teacher_name).replace(".", "").strip()
    course = simplify_class_for_paper(class_name, grade, book_name)
    return f"{teacher} {course} 오답 Paper - {month}월 {week}주차"


def build_claude_export_df(
    teacher_name: str,
    class_name: str,
    selected_students: list[str],
    selected_book: str,
    month: int,
    week: int,
) -> pd.DataFrame:
    roster = get_roster_df()
    answers = get_all_wrong_answers()

    selected_roster = roster[
        (roster["담당선생님"] == teacher_name)
        & (roster["반명"] == class_name)
        & (roster["학생명"].isin(selected_students))
    ].copy()

    records = []

    for _, student in selected_roster.iterrows():
        student_answers = answers[
            (answers["학생"] == student["학생명"])
            & (answers["교재"] == selected_book)
        ].copy()

        all_numbers = []
        all_memos = []

        for _, answer in student_answers.iterrows():
            for number in parse_problem_numbers(answer["문제번호"]):
                if number not in all_numbers:
                    all_numbers.append(number)

            memo = str(answer.get("비고", "") or "").strip()
            if memo and memo not in all_memos:
                all_memos.append(memo)

        title = build_paper_title(
            teacher_name,
            class_name,
            student["학년"],
            selected_book,
            month,
            week,
        )

        records.append(
            {
                "학생명": student["학생명"],
                "학교명": student["학교명"],
                "학년": student["학년"],
                "담당선생님": teacher_name,
                "반명": class_name,
                "교재": selected_book,
                "문제번호": format_problem_numbers(all_numbers),
                "비고": " / ".join(all_memos),
                "PDF상단제목": title,
                "파일명": (
                    f"[오답paper][{student['학년']} {student['학생명']}]"
                    f"[{month}월 {week}주차].pdf"
                ),
            }
        )

    return pd.DataFrame(records)


# ---------------------- 비밀번호 처리 ----------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()



def find_signup_name_conflict(username: str) -> dict | None:
    """
    회원가입 이름이 기존 계정 또는 명단 학생 이름과 충돌하는지 확인합니다.

    예:
    - 명단 이름이 '양서율'인데 '양서율성신고'로 가입 시도
    - 기존 계정이 '양서율'인데 '양서율1'로 가입 시도
    위 경우 별도 계정 생성을 막고 관리자 문의를 안내합니다.
    """
    clean_name = re.sub(r"\s+", "", str(username or "").strip())

    if not clean_name:
        return None

    user_rows = fetch_all_rows("users", "username")
    roster_rows = fetch_all_rows("student_roster", "student_name,school_name")

    existing_user_names = sorted(
        {
            re.sub(r"\s+", "", str(row.get("username", "")).strip())
            for row in user_rows
            if str(row.get("username", "")).strip()
        },
        key=len,
        reverse=True,
    )

    roster_map: dict[str, str] = {}
    for row in roster_rows:
        roster_name = re.sub(
            r"\s+",
            "",
            str(row.get("student_name", "")).strip(),
        )
        if roster_name:
            roster_map.setdefault(
                roster_name,
                str(row.get("school_name", "")).strip(),
            )

    # 이미 정확히 같은 계정이 존재하는 경우
    if clean_name in existing_user_names:
        return {
            "type": "existing_account",
            "matched_name": clean_name,
            "school_name": roster_map.get(clean_name, ""),
        }

    # 명단에 정확히 존재하는 이름이고 아직 계정이 없다면 정상 가입 허용
    if clean_name in roster_map:
        return None

    candidate_names = sorted(
        set(existing_user_names) | set(roster_map.keys()),
        key=len,
        reverse=True,
    )

    # 본인 이름 뒤에 학교명·숫자 등을 붙인 별도 계정 생성을 차단
    for candidate in candidate_names:
        if len(candidate) < 2:
            continue

        if clean_name.startswith(candidate) or candidate.startswith(clean_name):
            return {
                "type": "similar_name",
                "matched_name": candidate,
                "school_name": roster_map.get(candidate, ""),
            }

    return None


def create_user(username: str, password: str, grade: str) -> bool:
    username = username.strip()

    if not username:
        return False

    existing = (
        supabase.table("users")
        .select("username")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if existing.data:
        return False

    supabase.table("users").insert(
        {
            "username": username,
            "password_hash": hash_pw(password),
            "grade": grade,
            "temp_password": "",
            "created_at": now_kst_iso()
        }
    ).execute()

    return True


def check_user(username: str, password: str) -> bool:
    response = (
        supabase.table("users")
        .select("password_hash")
        .eq("username", username.strip())
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    return response.data[0]["password_hash"] == hash_pw(password)


def change_my_password(
    username: str,
    current_password: str,
    new_password: str
) -> bool:
    """학생 본인이 현재 비밀번호를 확인한 뒤 새 비밀번호로 변경합니다."""
    if not check_user(username, current_password):
        return False

    supabase.table("users").update(
        {
            "password_hash": hash_pw(new_password),
            "temp_password": ""
        }
    ).eq("username", username).execute()

    return True


def get_admin_password_status() -> pd.DataFrame:
    """
    관리자는 복구·초기화 때 설정한 임시 비밀번호만 확인합니다.
    학생이 직접 변경한 비밀번호는 해시만 저장되므로 확인할 수 없습니다.
    """
    rows = fetch_all_rows(
        "users",
        "username,grade,temp_password,created_at",
        order_column="created_at",
        desc=True
    )

    if not rows:
        return pd.DataFrame(
            columns=["학생", "학년", "비밀번호상태", "가입일시"]
        )

    records = []

    for row in rows:
        temp_password = row.get("temp_password") or ""
        records.append(
            {
                "학생": row.get("username", ""),
                "학년": row.get("grade") or "미지정",
                "비밀번호상태": (
                    temp_password
                    if temp_password
                    else "학생이 직접 변경함"
                ),
                "가입일시": row.get("created_at", "")
            }
        )

    return pd.DataFrame(records)


# ---------------------- 오답 저장/조회 ----------------------
def parse_problem_numbers(value: str) -> list[str]:
    """
    쉼표, 띄어쓰기, 줄바꿈이 섞여 있어도 숫자만 순서대로 추출합니다.
    예: '371, 499, 486, 587 961' → ['371', '499', '486', '587', '961']
    """
    numbers = re.findall(r"\d+", str(value or ""))
    return list(dict.fromkeys(numbers))


def format_problem_numbers(numbers: list[str]) -> str:
    return ", ".join(numbers)


def get_existing_problem_numbers(username: str, book: str) -> set[str]:
    rows = fetch_all_rows(
        "wrong_answers",
        "problem",
        filters=[
            ("username", "eq", username),
            ("unit", "eq", book),
        ],
    )

    existing: set[str] = set()

    for row in rows:
        existing.update(parse_problem_numbers(row.get("problem", "")))

    return existing


def add_wrong_answer(
    username: str,
    book: str,
    problem_number: str,
    note: str
) -> dict:
    submitted_numbers = parse_problem_numbers(problem_number)

    if not submitted_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": [],
            "message": "저장할 문제번호가 없습니다.",
        }

    existing_numbers = get_existing_problem_numbers(username, book)

    new_numbers = [
        number
        for number in submitted_numbers
        if number not in existing_numbers
    ]
    duplicate_numbers = [
        number
        for number in submitted_numbers
        if number in existing_numbers
    ]

    if not new_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": duplicate_numbers,
            "message": "입력한 문제번호가 모두 이미 저장되어 있습니다.",
        }

    supabase.table("wrong_answers").insert(
        {
            "username": username,
            "unit": book,
            "problem": format_problem_numbers(new_numbers),
            "memo": note,
            "created_at": now_kst_iso(),
        }
    ).execute()

    return {
        "saved": True,
        "new_numbers": new_numbers,
        "duplicate_numbers": duplicate_numbers,
        "message": "새 문제번호만 저장했습니다.",
    }


def cleanup_duplicate_wrong_answers() -> dict:
    """
    학생·교재별 작성 순서대로 확인하여 이미 저장된 번호는 뒤 기록에서 제거합니다.
    완전히 같은 중복 행은 삭제합니다.
    """
    rows = fetch_all_rows(
        "wrong_answers",
        "id,username,unit,problem,created_at",
        order_column="id",
        desc=False,
    )

    seen_by_group: dict[tuple[str, str], set[str]] = {}
    updated_count = 0
    deleted_count = 0

    for row in rows:
        row_id = row.get("id")
        username = str(row.get("username", ""))
        unit = str(row.get("unit", ""))
        group_key = (username, unit)

        seen = seen_by_group.setdefault(group_key, set())
        numbers = parse_problem_numbers(row.get("problem", ""))

        new_numbers = [number for number in numbers if number not in seen]

        if not new_numbers:
            (
                supabase.table("wrong_answers")
                .delete()
                .eq("id", row_id)
                .execute()
            )
            deleted_count += 1
            continue

        normalized_problem = format_problem_numbers(new_numbers)
        original_problem = str(row.get("problem", "")).strip()

        if normalized_problem != original_problem:
            (
                supabase.table("wrong_answers")
                .update({"problem": normalized_problem})
                .eq("id", row_id)
                .execute()
            )
            updated_count += 1

        seen.update(new_numbers)

    return {
        "updated": updated_count,
        "deleted": deleted_count,
    }


def get_my_wrong_answers(username: str) -> pd.DataFrame:
    rows = fetch_all_rows(
        "wrong_answers",
        "unit,problem,memo,created_at,id",
        filters=[("username", "eq", username)],
        order_column="id",
        desc=True
    )

    if not rows:
        return pd.DataFrame(
            columns=["교재", "문제번호", "비고", "작성일시"]
        )

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "unit": "교재",
            "problem": "문제번호",
            "memo": "비고",
            "created_at": "작성일시"
        }
    )

    return df[["교재", "문제번호", "비고", "작성일시"]]


def get_wrong_answer_edit_records() -> pd.DataFrame:
    rows = fetch_all_rows(
        "wrong_answers",
        "id,username,unit,problem,memo,created_at",
        order_column="id",
        desc=True,
    )

    if not rows:
        return pd.DataFrame(
            columns=["기록ID", "학생", "교재", "문제번호", "비고", "작성일시"]
        )

    return pd.DataFrame(
        [
            {
                "기록ID": row.get("id"),
                "학생": row.get("username", ""),
                "교재": row.get("unit", ""),
                "문제번호": row.get("problem", ""),
                "비고": row.get("memo", ""),
                "작성일시": row.get("created_at", ""),
            }
            for row in rows
        ]
    )


def update_wrong_answer_book(record_id: int, new_book: str):
    (
        supabase.table("wrong_answers")
        .update({"unit": new_book})
        .eq("id", int(record_id))
        .execute()
    )
    cleanup_duplicate_wrong_answers()


def render_wrong_answer_book_editor(key_prefix: str):
    records_df = get_wrong_answer_edit_records()

    if records_df.empty:
        st.info("수정할 오답 기록이 없습니다.")
        return

    students = ["전체"] + sorted(
        records_df["학생"].dropna().astype(str).unique().tolist()
    )

    selected_student = st.selectbox(
        "학생 선택",
        students,
        key=f"{key_prefix}_student",
    )

    filtered_df = records_df.copy()
    if selected_student != "전체":
        filtered_df = filtered_df[filtered_df["학생"] == selected_student]

    option_map = {}
    for _, row in filtered_df.iterrows():
        date_text = str(row["작성일시"])[:10]
        label = (
            f"{row['학생']} | {date_text} | "
            f"{row['교재']} | {row['문제번호']} | ID {row['기록ID']}"
        )
        option_map[label] = int(row["기록ID"])

    selected_label = st.selectbox(
        "수정할 기록",
        list(option_map.keys()),
        key=f"{key_prefix}_record",
    )

    record_id = option_map[selected_label]
    selected_row = filtered_df[
        filtered_df["기록ID"] == record_id
    ].iloc[0]

    current_book = str(selected_row["교재"])
    current_index = BOOKS.index(current_book) if current_book in BOOKS else 0

    st.caption(
        f"현재 교재: {current_book} · 문제번호: {selected_row['문제번호']}"
    )

    new_book = st.selectbox(
        "변경할 교재",
        BOOKS,
        index=current_index,
        key=f"{key_prefix}_new_book",
    )

    confirm = st.checkbox(
        "선택한 기록의 교재를 변경합니다.",
        key=f"{key_prefix}_confirm",
    )

    if st.button(
        "교재 수정",
        key=f"{key_prefix}_button",
        type="primary",
    ):
        if not confirm:
            st.warning("수정 확인 항목에 체크해주세요.")
        elif new_book == current_book:
            st.info("현재 교재와 변경할 교재가 같습니다.")
        else:
            update_wrong_answer_book(record_id, new_book)
            st.success(
                f"{selected_row['학생']} 학생의 교재를 "
                f"'{current_book}'에서 '{new_book}'으로 변경했습니다."
            )
            st.rerun()


def get_all_wrong_answers() -> pd.DataFrame:
    answer_rows = fetch_all_rows(
        "wrong_answers",
        "id,username,unit,problem,memo,created_at",
        order_column="id",
        desc=True
    )

    if not answer_rows:
        return pd.DataFrame(
            columns=["학생", "학년", "교재", "문제번호", "비고", "작성일시"]
        )

    user_rows = fetch_all_rows("users", "username,grade")
    grade_map = {
        row.get("username", ""): row.get("grade") or "미지정"
        for row in user_rows
    }

    records = []

    for row in answer_rows:
        username = row.get("username", "")
        records.append(
            {
                "학생": username,
                "학년": grade_map.get(username, "미지정"),
                "교재": row.get("unit", ""),
                "문제번호": row.get("problem", ""),
                "비고": row.get("memo", ""),
                "작성일시": row.get("created_at", "")
            }
        )

    return pd.DataFrame(records)


def merge_wrong_answers_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    같은 학생이 같은 날짜에 같은 교재로 여러 번 입력한 오답 기록을 한 줄로 합칩니다.
    문제번호는 중복 없이 입력 순서대로 합치고, 비고도 중복 문구를 제거해 합칩니다.
    """
    output_columns = ["학생", "학년", "교재", "문제번호", "비고", "작성일시"]

    if df.empty:
        return pd.DataFrame(columns=output_columns)

    working = df.copy()
    working["작성일시"] = working["작성일시"].fillna("").astype(str)
    working["작성날짜"] = working["작성일시"].str.slice(0, 10)

    # 날짜 형식이 없는 예외 데이터는 기존 작성일시를 사용합니다.
    working.loc[
        working["작성날짜"].str.len() != 10,
        "작성날짜"
    ] = working["작성일시"]

    merged_records = []

    grouped = working.groupby(
        ["학생", "학년", "교재", "작성날짜"],
        sort=False,
        dropna=False,
    )

    for (student, grade, book, created_date), group in grouped:
        merged_numbers = []
        merged_memos = []

        for _, row in group.iterrows():
            for number in parse_problem_numbers(row.get("문제번호", "")):
                if number not in merged_numbers:
                    merged_numbers.append(number)

            memo = str(row.get("비고", "") or "").strip()
            if memo and memo.lower() != "nan" and memo not in merged_memos:
                merged_memos.append(memo)

        merged_records.append(
            {
                "학생": student,
                "학년": grade,
                "교재": book,
                "문제번호": format_problem_numbers(merged_numbers),
                "비고": " / ".join(merged_memos),
                "작성일시": created_date,
            }
        )

    return pd.DataFrame(merged_records, columns=output_columns)



def get_print_status_rows(
    teacher_name: str | None = None
) -> pd.DataFrame:
    """출력 관리 상태를 조회합니다."""
    filters = []

    if teacher_name and teacher_name != ALL_TEACHER_ADMIN:
        filters.append(("teacher_name", "eq", teacher_name))

    rows = fetch_all_rows(
        "print_status",
        (
            "id,teacher_name,class_name,student_name,book_name,"
            "month,week,is_printed,printed_at,memo,created_at"
        ),
        filters=filters,
        order_column="id",
        desc=True,
    )

    columns = [
        "기록ID", "담당선생님", "반명", "학생명", "교재",
        "월", "주차", "출력완료", "출력일시", "메모", "등록일시"
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "기록ID": row.get("id"),
                "담당선생님": row.get("teacher_name", ""),
                "반명": row.get("class_name", ""),
                "학생명": row.get("student_name", ""),
                "교재": row.get("book_name", ""),
                "월": row.get("month"),
                "주차": row.get("week"),
                "출력완료": bool(row.get("is_printed", False)),
                "출력일시": row.get("printed_at", ""),
                "메모": row.get("memo", ""),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ],
        columns=columns,
    )


def ensure_print_status_records(
    teacher_name: str,
    class_name: str,
    month: int,
    week: int,
):
    """
    선택한 선생님·반·월·주차의 학생들을 출력 관리 목록에 생성합니다.
    이미 존재하는 학생은 중복 생성하지 않습니다.
    """
    roster = get_roster_df()

    target = roster[
        (roster["담당선생님"] == teacher_name)
        & (roster["반명"] == class_name)
    ].copy()

    if target.empty:
        return 0

    existing_rows = fetch_all_rows(
        "print_status",
        "student_name,book_name",
        filters=[
            ("teacher_name", "eq", teacher_name),
            ("class_name", "eq", class_name),
            ("month", "eq", int(month)),
            ("week", "eq", int(week)),
        ],
    )

    existing_keys = {
        (
            str(row.get("student_name", "")).strip(),
            str(row.get("book_name", "")).strip(),
        )
        for row in existing_rows
    }

    insert_rows = []

    for _, row in target.iterrows():
        key = (
            str(row["학생명"]).strip(),
            str(row["매칭교재"]).strip(),
        )

        if key in existing_keys:
            continue

        insert_rows.append(
            {
                "teacher_name": teacher_name,
                "class_name": class_name,
                "student_name": row["학생명"],
                "book_name": row["매칭교재"],
                "month": int(month),
                "week": int(week),
                "is_printed": False,
                "printed_at": None,
                "memo": "",
                "created_at": now_kst_iso(),
            }
        )

    if insert_rows:
        supabase.table("print_status").insert(insert_rows).execute()

    return len(insert_rows)



def ensure_selected_print_status_records(
    teacher_name: str,
    class_name: str,
    student_names: list[str],
    book_name: str,
    month: int,
    week: int,
) -> int:
    """
    오답노트 생성 대상으로 선택된 학생만 출력 관리 목록에 등록합니다.
    이미 등록된 학생·교재·월·주차 조합은 중복 생성하지 않습니다.
    """
    clean_students = [
        str(name).strip()
        for name in student_names
        if str(name).strip()
    ]

    if not clean_students:
        return 0

    roster = get_roster_df()

    target = roster[
        (roster["담당선생님"] == teacher_name)
        & (roster["반명"] == class_name)
        & (roster["학생명"].isin(clean_students))
    ].copy()

    if target.empty:
        return 0

    existing_rows = fetch_all_rows(
        "print_status",
        "student_name,book_name",
        filters=[
            ("teacher_name", "eq", teacher_name),
            ("class_name", "eq", class_name),
            ("month", "eq", int(month)),
            ("week", "eq", int(week)),
        ],
    )

    existing_keys = {
        (
            str(row.get("student_name", "")).strip(),
            str(row.get("book_name", "")).strip(),
        )
        for row in existing_rows
    }

    insert_rows = []

    for _, row in target.iterrows():
        student_name = str(row["학생명"]).strip()
        selected_book_name = str(book_name).strip()
        key = (student_name, selected_book_name)

        if key in existing_keys:
            continue

        insert_rows.append(
            {
                "teacher_name": teacher_name,
                "class_name": class_name,
                "student_name": student_name,
                "book_name": selected_book_name,
                "month": int(month),
                "week": int(week),
                "is_printed": False,
                "printed_at": None,
                "memo": "",
                "created_at": now_kst_iso(),
            }
        )

    if insert_rows:
        supabase.table("print_status").insert(insert_rows).execute()

    return len(insert_rows)


def register_print_queue_on_download(
    teacher_name: str,
    class_name: str,
    student_names: list[str],
    book_name: str,
    month: int,
    week: int,
):
    """
    Claude Code용 오답노트 엑셀 다운로드 버튼을 누를 때
    선택 학생을 출력 대기 목록에 자동 등록합니다.
    """
    try:
        created_count = ensure_selected_print_status_records(
            teacher_name,
            class_name,
            student_names,
            book_name,
            month,
            week,
        )
        st.session_state["print_auto_register_result"] = {
            "created_count": created_count,
            "student_count": len(student_names),
            "teacher_name": teacher_name,
            "class_name": class_name,
            "month": month,
            "week": week,
        }
    except Exception as error:
        st.session_state["print_auto_register_error"] = str(error)


def update_print_status_bulk(
    record_ids: list[int],
    is_printed: bool,
) -> int:
    """여러 출력 관리 기록을 한 번에 완료 또는 미완료로 변경합니다."""
    clean_ids = sorted(
        {
            int(record_id)
            for record_id in record_ids
            if record_id is not None
        }
    )

    if not clean_ids:
        return 0

    payload = {
        "is_printed": bool(is_printed),
        "printed_at": now_kst_iso() if is_printed else None,
    }

    updated_count = 0

    # Supabase Python 클라이언트 버전 차이를 피하기 위해
    # 한 건씩 안정적으로 업데이트합니다.
    for record_id in clean_ids:
        response = (
            supabase.table("print_status")
            .update(payload)
            .eq("id", record_id)
            .execute()
        )
        updated_count += len(response.data or [])

    return updated_count


def update_print_status(
    record_id: int,
    *,
    is_printed: bool,
    memo: str,
):
    """출력 완료 여부와 메모를 저장합니다."""
    payload = {
        "is_printed": bool(is_printed),
        "memo": str(memo or "").strip(),
        "printed_at": now_kst_iso() if is_printed else None,
    }

    (
        supabase.table("print_status")
        .update(payload)
        .eq("id", int(record_id))
        .execute()
    )


def delete_print_status_record(record_id: int):
    (
        supabase.table("print_status")
        .delete()
        .eq("id", int(record_id))
        .execute()
    )


def render_print_management():
    """선생님 및 전체 관리자용 출력 관리 화면입니다."""
    current_teacher = st.session_state.teacher_name
    roster = get_roster_df()

    if roster.empty:
        st.info("등록된 학생 명단이 없습니다.")
        return

    if current_teacher == ALL_TEACHER_ADMIN:
        teacher_options = sorted(
            roster["담당선생님"].dropna().astype(str).unique().tolist()
        )

        if not teacher_options:
            st.info("등록된 담당 선생님이 없습니다.")
            return

        selected_teacher = st.selectbox(
            "담당 선생님",
            teacher_options,
            key="print_manage_teacher",
        )
    else:
        selected_teacher = current_teacher
        st.markdown(f"**담당 선생님:** {selected_teacher}")

    teacher_roster = roster[
        roster["담당선생님"] == selected_teacher
    ].copy()

    if teacher_roster.empty:
        st.info("담당 학생 명단이 없습니다.")
        return

    class_options = sorted(
        teacher_roster["반명"].dropna().astype(str).unique().tolist()
    )

    if not class_options:
        st.info("등록된 반이 없습니다.")
        return

    selected_class = st.selectbox(
        "반 선택",
        class_options,
        key="print_manage_class",
    )

    col_month, col_week = st.columns(2)

    with col_month:
        month = st.selectbox(
            "월",
            list(range(1, 13)),
            index=datetime.now(KST).month - 1,
            key="print_manage_month",
        )

    with col_week:
        week = st.selectbox(
            "주차",
            [1, 2, 3, 4, 5],
            index=min((datetime.now(KST).day - 1) // 7, 4),
            key="print_manage_week",
        )

    col_load, col_refresh = st.columns([3, 1])

    with col_load:
        if st.button(
            "현재 반 전체 학생을 출력 목록에 등록",
            type="primary",
            key="print_manage_load",
            use_container_width=True,
        ):
            created_count = ensure_print_status_records(
                selected_teacher,
                selected_class,
                month,
                week,
            )

            if created_count:
                st.success(
                    f"출력 관리 목록에 {created_count}건을 추가했습니다."
                )
            else:
                st.info("이미 출력 관리 목록에 등록된 학생들입니다.")

            st.rerun()

    with col_refresh:
        if st.button(
            "새로고침",
            key="print_manage_refresh",
            use_container_width=True,
        ):
            st.rerun()

    status_df = get_print_status_rows(selected_teacher)

    if status_df.empty:
        st.info(
            "아직 생성된 출력 관리 목록이 없습니다. "
            "오답노트 엑셀을 다운로드하거나 위 버튼으로 목록을 등록해주세요."
        )
        return

    display_df = status_df[
        (status_df["반명"] == selected_class)
        & (status_df["월"] == int(month))
        & (status_df["주차"] == int(week))
    ].copy()

    if display_df.empty:
        st.info(
            "선택한 반·월·주차에 등록된 출력 목록이 없습니다. "
            "오답노트 생성 탭에서 엑셀을 다운로드하면 자동 등록됩니다."
        )
        return

    display_df = display_df.sort_values(
        by=["출력완료", "학생명", "교재"],
        ascending=[True, True, True],
    ).reset_index(drop=True)

    completed = int(display_df["출력완료"].sum())
    total = len(display_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("전체", total)
    col2.metric("출력 완료", completed)
    col3.metric("미출력", total - completed)

    status_filter = st.radio(
        "표시할 상태",
        ["전체", "미출력", "출력 완료"],
        horizontal=True,
        key="print_status_filter",
    )

    filtered_df = display_df.copy()

    if status_filter == "미출력":
        filtered_df = filtered_df[
            filtered_df["출력완료"] == False
        ].copy()
    elif status_filter == "출력 완료":
        filtered_df = filtered_df[
            filtered_df["출력완료"] == True
        ].copy()

    st.caption(
        "개별 저장도 가능하며, 아래에서 여러 학생을 선택해 "
        "출력 완료 또는 미출력 상태로 한 번에 변경할 수 있습니다."
    )

    if filtered_df.empty:
        st.info(f"현재 '{status_filter}' 상태의 학생이 없습니다.")
        return

    option_map = {
        int(row["기록ID"]): (
            f"{row['학생명']} · {row['교재']}"
            + (" · 완료" if bool(row["출력완료"]) else " · 미출력")
        )
        for _, row in filtered_df.iterrows()
    }

    visible_ids = list(option_map.keys())

    selected_ids = st.multiselect(
        "일괄 처리할 학생 선택",
        options=visible_ids,
        default=[],
        format_func=lambda record_id: option_map.get(
            record_id,
            str(record_id),
        ),
        key=(
            f"print_bulk_selection_"
            f"{selected_teacher}_{selected_class}_{month}_{week}_{status_filter}"
        ),
        placeholder="학생을 여러 명 선택할 수 있습니다.",
    )

    col_all, col_none, col_complete, col_incomplete = st.columns(4)

    with col_all:
        if st.button(
            "현재 목록 전체 선택",
            key="print_select_all_help",
            use_container_width=True,
        ):
            st.info(
                "위 선택창을 클릭한 뒤 Ctrl+A 또는 학생을 여러 명 선택해주세요. "
                "Streamlit 기본 선택창 특성상 버튼으로 선택값을 강제 변경하지 않습니다."
            )

    with col_none:
        selected_count = len(selected_ids)
        st.metric("선택 인원", selected_count)

    with col_complete:
        if st.button(
            "선택 학생 출력 완료",
            type="primary",
            key="print_bulk_complete",
            use_container_width=True,
            disabled=not selected_ids,
        ):
            updated_count = update_print_status_bulk(
                selected_ids,
                True,
            )
            st.success(f"{updated_count}건을 출력 완료 처리했습니다.")
            st.rerun()

    with col_incomplete:
        if st.button(
            "선택 학생 미출력 처리",
            key="print_bulk_incomplete",
            use_container_width=True,
            disabled=not selected_ids,
        ):
            updated_count = update_print_status_bulk(
                selected_ids,
                False,
            )
            st.success(f"{updated_count}건을 미출력 상태로 변경했습니다.")
            st.rerun()

    st.divider()

    for _, row in filtered_df.iterrows():
        record_id = int(row["기록ID"])

        with st.container(border=True):
            col_info, col_check = st.columns([4, 1])

            with col_info:
                st.markdown(
                    f"**{row['학생명']}** · {row['교재']}"
                )

                if row["출력일시"]:
                    st.caption(f"최근 출력일시: {row['출력일시']}")

            with col_check:
                checked = st.checkbox(
                    "출력 완료",
                    value=bool(row["출력완료"]),
                    key=f"print_checked_{record_id}",
                )

            memo = st.text_input(
                "메모",
                value=str(row["메모"] or ""),
                placeholder="예: 재출력 필요, 결석으로 미전달",
                key=f"print_memo_{record_id}",
            )

            col_save, col_delete = st.columns([1, 1])

            with col_save:
                if st.button(
                    "저장",
                    key=f"print_save_{record_id}",
                    use_container_width=True,
                ):
                    update_print_status(
                        record_id,
                        is_printed=checked,
                        memo=memo,
                    )
                    st.success(
                        f"{row['학생명']} 학생의 출력 상태를 저장했습니다."
                    )
                    st.rerun()

            with col_delete:
                if st.button(
                    "목록 삭제",
                    key=f"print_delete_{record_id}",
                    use_container_width=True,
                ):
                    delete_print_status_record(record_id)
                    st.rerun()

    st.download_button(
        "현재 필터 결과 엑셀 다운로드",
        data=dataframe_to_excel_bytes(filtered_df),
        file_name=(
            f"{selected_teacher}_{selected_class}_"
            f"{month}월_{week}주차_{status_filter}_출력관리.xlsx"
        ),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_print_status",
    )



def get_monday(date_value: datetime | None = None) -> datetime:
    """입력 날짜가 포함된 주의 월요일 00:00을 반환합니다."""
    current = date_value or datetime.now(KST).replace(tzinfo=None)
    current = current.replace(hour=0, minute=0, second=0, microsecond=0)
    return current - timedelta(days=current.weekday())


def build_week_options(weeks_back: int = 12) -> dict[str, datetime]:
    """이번 주부터 과거 주차까지 선택 가능한 목록을 생성합니다."""
    current_monday = get_monday()
    options: dict[str, datetime] = {}

    for offset in range(weeks_back):
        week_start = current_monday - timedelta(weeks=offset)
        week_end = week_start + timedelta(days=6)
        month_week = ((week_start.day - 1) // 7) + 1

        prefix = "이번 주 · " if offset == 0 else ""
        label = (
            f"{prefix}{week_start.month}월 {month_week}주차 "
            f"({week_start.month}/{week_start.day} 월 ~ "
            f"{week_end.month}/{week_end.day} 일)"
        )
        options[label] = week_start

    return options


def parse_created_at_to_datetime(value) -> datetime | None:
    """Supabase 작성일시 문자열을 비교 가능한 datetime으로 변환합니다."""
    raw = str(value or "").strip()

    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))

        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(KST).replace(tzinfo=None)

        return parsed
    except Exception:
        return None


def get_weekly_submission_df(
    current_teacher: str,
    week_start: datetime,
) -> pd.DataFrame:
    """
    명단 학생을 기준으로 해당 주 월요일~일요일의 제출 여부를 계산합니다.
    해당 기간에 문제번호를 1개 이상 저장하면 제출로 처리합니다.
    """
    roster = get_roster_df()

    output_columns = [
        "담당선생님", "반명", "학생명", "학교명", "학년",
        "제출여부", "제출문제수", "제출교재", "최근제출일시",
    ]

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    if current_teacher != ALL_TEACHER_ADMIN:
        roster = roster[
            roster["담당선생님"] == current_teacher
        ].copy()

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    # 같은 학생이 같은 반에서 여러 교재로 명단에 등록된 경우 한 명으로 통합합니다.
    roster_students = (
        roster[
            ["담당선생님", "반명", "학생명", "학교명", "학년"]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    answer_rows = fetch_all_rows(
        "wrong_answers",
        "username,unit,problem,created_at",
        order_column="id",
        desc=False,
    )

    week_end_exclusive = week_start + timedelta(days=7)
    submission_map: dict[str, dict] = {}

    for row in answer_rows:
        created_dt = parse_created_at_to_datetime(row.get("created_at"))

        if created_dt is None:
            continue

        if not (week_start <= created_dt < week_end_exclusive):
            continue

        username = str(row.get("username", "")).strip()
        if not username:
            continue

        info = submission_map.setdefault(
            username,
            {
                "numbers": [],
                "books": [],
                "latest_dt": None,
                "latest_text": "",
            },
        )

        for number in parse_problem_numbers(row.get("problem", "")):
            if number not in info["numbers"]:
                info["numbers"].append(number)

        book = str(row.get("unit", "")).strip()
        if book and book not in info["books"]:
            info["books"].append(book)

        if info["latest_dt"] is None or created_dt > info["latest_dt"]:
            info["latest_dt"] = created_dt
            info["latest_text"] = created_dt.strftime("%Y.%m.%d %H:%M")

    records = []

    for _, student in roster_students.iterrows():
        student_name = str(student["학생명"]).strip()
        submission = submission_map.get(
            student_name,
            {
                "numbers": [],
                "books": [],
                "latest_text": "",
            },
        )
        problem_count = len(submission["numbers"])

        records.append(
            {
                "담당선생님": student["담당선생님"],
                "반명": student["반명"],
                "학생명": student_name,
                "학교명": student["학교명"],
                "학년": student["학년"],
                "제출여부": "O" if problem_count > 0 else "X",
                "제출문제수": problem_count,
                "제출교재": ", ".join(submission["books"]),
                "최근제출일시": submission["latest_text"],
            }
        )

    return pd.DataFrame(records, columns=output_columns)


def render_week_selector(key_prefix: str) -> tuple[datetime, str]:
    """주차 선택과 새로고침 UI를 공통으로 표시합니다."""
    week_options = build_week_options(weeks_back=12)
    labels = list(week_options.keys())

    col_week, col_refresh = st.columns([5, 1])

    with col_week:
        selected_label = st.selectbox(
            "조회 주차",
            labels,
            index=0,
            key=f"{key_prefix}_week_selector",
        )

    with col_refresh:
        st.write("")
        st.write("")
        if st.button(
            "새로고침",
            key=f"{key_prefix}_refresh",
            use_container_width=True,
        ):
            st.rerun()

    return week_options[selected_label], selected_label


def render_weekly_submission_status():
    """선생님용 주간 제출 현황 탭을 표시합니다."""
    current_teacher = st.session_state.teacher_name
    week_start, selected_label = render_week_selector(
        "weekly_submission"
    )
    week_end = week_start + timedelta(days=6)

    st.caption(
        f"조회 기간: {week_start.strftime('%Y.%m.%d')} 월요일 00:00부터 "
        f"{week_end.strftime('%Y.%m.%d')} 일요일 23:59까지"
    )
    st.info(
        "해당 기간에 문제번호를 1개 이상 저장한 학생을 제출 완료로 계산합니다. "
        "학생이 오답을 저장한 뒤 새로고침하면 바로 반영됩니다."
    )

    weekly_df = get_weekly_submission_df(
        current_teacher,
        week_start,
    )

    if weekly_df.empty:
        st.info("조회할 담당 학생 명단이 없습니다.")
        return

    total_students = weekly_df["학생명"].nunique()
    submitted_students = weekly_df.loc[
        weekly_df["제출여부"] == "O",
        "학생명",
    ].nunique()
    missing_students = max(total_students - submitted_students, 0)
    submission_rate = (
        round(submitted_students / total_students * 100, 1)
        if total_students
        else 0.0
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 학생", total_students)
    col2.metric("제출 학생", submitted_students)
    col3.metric("미제출 학생", missing_students)
    col4.metric("제출률", f"{submission_rate}%")

    status_filter = st.radio(
        "제출 상태",
        ["전체", "제출 완료", "미제출"],
        horizontal=True,
        key="weekly_submission_status_filter",
    )

    if status_filter == "제출 완료":
        weekly_df = weekly_df[
            weekly_df["제출여부"] == "O"
        ].copy()
    elif status_filter == "미제출":
        weekly_df = weekly_df[
            weekly_df["제출여부"] == "X"
        ].copy()

    if current_teacher == ALL_TEACHER_ADMIN:
        weekly_df["관리용반명"] = (
            weekly_df["담당선생님"].astype(str)
            + " · "
            + weekly_df["반명"].astype(str)
        )
    else:
        weekly_df["관리용반명"] = weekly_df["반명"].astype(str)

    class_names = sorted(
        weekly_df["관리용반명"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if not class_names:
        st.info(f"현재 '{status_filter}' 조건에 해당하는 학생이 없습니다.")
        return

    tab_labels = ["전체"] + class_names
    class_tabs = st.tabs(tab_labels)

    for tab_index, (class_tab, tab_name) in enumerate(
        zip(class_tabs, tab_labels)
    ):
        with class_tab:
            if tab_name == "전체":
                tab_df = weekly_df.copy()
            else:
                tab_df = weekly_df[
                    weekly_df["관리용반명"] == tab_name
                ].copy()

            tab_df = tab_df.sort_values(
                by=["제출여부", "반명", "학생명"],
                ascending=[True, True, True],
            )

            class_total = tab_df["학생명"].nunique()
            class_submitted = tab_df.loc[
                tab_df["제출여부"] == "O",
                "학생명",
            ].nunique()
            class_missing = max(
                class_total - class_submitted,
                0,
            )

            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("학생", class_total)
            metric2.metric("제출", class_submitted)
            metric3.metric("미제출", class_missing)

            display_columns = [
                "담당선생님", "반명", "학생명", "학교명", "학년",
                "제출여부", "제출문제수", "제출교재", "최근제출일시",
            ]

            st.dataframe(
                tab_df[display_columns],
                use_container_width=True,
                hide_index=True,
                height=520,
            )

            safe_tab_name = re.sub(
                r"[^0-9A-Za-z가-힣_-]+",
                "_",
                tab_name,
            )

            st.download_button(
                f"{tab_name} 주간 제출 현황 엑셀 다운로드",
                data=dataframe_to_excel_bytes(
                    tab_df[display_columns]
                ),
                file_name=(
                    f"{current_teacher}_{safe_tab_name}_"
                    f"{week_start.strftime('%Y%m%d')}_주간제출현황.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key=f"weekly_submission_download_{tab_index}",
            )


def render_weekly_missing_students():
    """선생님용 미제출 학생 전용 탭을 표시합니다."""
    current_teacher = st.session_state.teacher_name
    week_start, selected_label = render_week_selector(
        "weekly_missing"
    )
    week_end = week_start + timedelta(days=6)

    st.caption(
        f"조회 기간: {week_start.strftime('%Y.%m.%d')} 월요일부터 "
        f"{week_end.strftime('%Y.%m.%d')} 일요일까지"
    )

    weekly_df = get_weekly_submission_df(
        current_teacher,
        week_start,
    )

    if weekly_df.empty:
        st.info("조회할 담당 학생 명단이 없습니다.")
        return

    missing_df = weekly_df[
        weekly_df["제출여부"] == "X"
    ].copy()

    if missing_df.empty:
        st.success("선택한 주차에는 미제출 학생이 없습니다.")
        return

    if current_teacher == ALL_TEACHER_ADMIN:
        teacher_options = ["전체"] + sorted(
            missing_df["담당선생님"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        selected_teacher = st.selectbox(
            "담당 선생님 필터",
            teacher_options,
            key="weekly_missing_teacher_filter",
        )

        if selected_teacher != "전체":
            missing_df = missing_df[
                missing_df["담당선생님"] == selected_teacher
            ].copy()

    class_options = ["전체"] + sorted(
        missing_df["반명"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_class = st.selectbox(
        "반 필터",
        class_options,
        key="weekly_missing_class_filter",
    )

    if selected_class != "전체":
        missing_df = missing_df[
            missing_df["반명"] == selected_class
        ].copy()

    st.metric(
        "현재 조건 미제출 학생",
        missing_df["학생명"].nunique(),
    )

    display_columns = [
        "담당선생님", "반명", "학생명", "학교명", "학년",
        "제출여부", "제출문제수", "제출교재", "최근제출일시",
    ]

    st.dataframe(
        missing_df[display_columns],
        use_container_width=True,
        hide_index=True,
        height=560,
    )

    st.download_button(
        "미제출 학생 엑셀 다운로드",
        data=dataframe_to_excel_bytes(
            missing_df[display_columns]
        ),
        file_name=(
            f"{current_teacher}_"
            f"{week_start.strftime('%Y%m%d')}_미제출학생.xlsx"
        ),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="weekly_missing_download",
        type="primary",
    )


def get_student_signup_status_df(
    current_teacher: str,
) -> pd.DataFrame:
    """
    학생 명단과 실제 users 계정을 비교하여 가입 상태를 계산합니다.

    상태:
    - 가입 완료: 명단 학생명과 계정명이 정확히 일치
    - 유사 계정 있음: 이름 뒤에 학교명·숫자 등이 붙은 유사 계정 존재
    - 미가입: 정확하거나 유사한 계정이 없음
    """
    roster = get_roster_df()

    output_columns = [
        "담당선생님",
        "학생명",
        "학교명",
        "학년",
        "소속반",
        "가입상태",
        "계정명",
        "가입일시",
        "오답개수",
    ]

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    if current_teacher != ALL_TEACHER_ADMIN:
        normalized_current_teacher = normalize_teacher_name(
            current_teacher
        )
        roster = roster[
            roster["담당선생님"].apply(normalize_teacher_name)
            == normalized_current_teacher
        ].copy()

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    users_df = get_all_users()

    if users_df.empty:
        users_df = pd.DataFrame(
            columns=["학생", "학년", "가입일시", "오답개수"]
        )

    account_map = {
        str(row["학생"]).strip(): {
            "가입일시": row.get("가입일시", ""),
            "오답개수": int(row.get("오답개수", 0) or 0),
        }
        for _, row in users_df.iterrows()
        if str(row.get("학생", "")).strip()
    }

    account_names = sorted(
        account_map.keys(),
        key=lambda value: (len(value), value),
    )

    grouped_roster = (
        roster.groupby(
            [
                "담당선생님",
                "학생명",
                "학교명",
                "학년",
            ],
            dropna=False,
            sort=False,
        )["반명"]
        .apply(
            lambda values: ", ".join(
                dict.fromkeys(
                    str(value).strip()
                    for value in values
                    if str(value).strip()
                )
            )
        )
        .reset_index(name="소속반")
    )

    records = []

    for _, student in grouped_roster.iterrows():
        student_name = str(student["학생명"]).strip()
        compact_student_name = re.sub(r"\\s+", "", student_name)

        exact_account = (
            student_name
            if student_name in account_map
            else None
        )

        similar_accounts = []

        if exact_account is None:
            for account_name in account_names:
                compact_account_name = re.sub(
                    r"\\s+",
                    "",
                    account_name,
                )

                if not compact_account_name:
                    continue

                if (
                    compact_account_name.startswith(
                        compact_student_name
                    )
                    or compact_student_name.startswith(
                        compact_account_name
                    )
                ):
                    similar_accounts.append(account_name)

        if exact_account:
            signup_status = "가입 완료"
            account_display = exact_account
            joined_at = account_map[exact_account]["가입일시"]
            answer_count = account_map[exact_account]["오답개수"]
        elif similar_accounts:
            signup_status = "유사 계정 있음"
            account_display = ", ".join(similar_accounts)
            joined_at = ", ".join(
                str(account_map[name]["가입일시"])
                for name in similar_accounts
                if str(account_map[name]["가입일시"]).strip()
            )
            answer_count = sum(
                int(account_map[name]["오답개수"])
                for name in similar_accounts
            )
        else:
            signup_status = "미가입"
            account_display = ""
            joined_at = ""
            answer_count = 0

        records.append(
            {
                "담당선생님": normalize_teacher_name(
                    student["담당선생님"]
                ),
                "학생명": student_name,
                "학교명": student["학교명"],
                "학년": student["학년"],
                "소속반": student["소속반"],
                "가입상태": signup_status,
                "계정명": account_display,
                "가입일시": joined_at,
                "오답개수": answer_count,
            }
        )

    return pd.DataFrame(records, columns=output_columns)


def render_student_signup_status():
    """선생님 및 전체 관리자용 담당 학생 가입 현황 화면입니다."""
    current_teacher = st.session_state.teacher_name
    status_df = get_student_signup_status_df(current_teacher)

    st.info(
        "학생 명단과 실제 가입 계정을 비교합니다. "
        "명단 이름과 정확히 일치하면 가입 완료, "
        "이름 뒤에 학교명이나 숫자가 붙은 계정은 유사 계정으로 표시됩니다."
    )

    if status_df.empty:
        st.info("확인할 담당 학생 명단이 없습니다.")
        return

    total_count = len(status_df)
    joined_count = int(
        (status_df["가입상태"] == "가입 완료").sum()
    )
    similar_count = int(
        (status_df["가입상태"] == "유사 계정 있음").sum()
    )
    missing_count = int(
        (status_df["가입상태"] == "미가입").sum()
    )
    joined_rate = (
        round(joined_count / total_count * 100, 1)
        if total_count
        else 0.0
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("담당 학생", total_count)
    col2.metric("가입 완료", joined_count)
    col3.metric("유사 계정", similar_count)
    col4.metric("미가입", missing_count)
    col5.metric("정상 가입률", f"{joined_rate}%")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        status_filter = st.selectbox(
            "가입 상태 필터",
            [
                "전체",
                "가입 완료",
                "유사 계정 있음",
                "미가입",
            ],
            key="student_signup_status_filter",
        )

    with filter_col2:
        class_options = ["전체"] + sorted(
            {
                class_name.strip()
                for class_list in status_df["소속반"].fillna("")
                for class_name in str(class_list).split(",")
                if class_name.strip()
            }
        )

        class_filter = st.selectbox(
            "반 필터",
            class_options,
            key="student_signup_class_filter",
        )

    display_df = status_df.copy()

    if status_filter != "전체":
        display_df = display_df[
            display_df["가입상태"] == status_filter
        ].copy()

    if class_filter != "전체":
        display_df = display_df[
            display_df["소속반"]
            .fillna("")
            .astype(str)
            .str.split(",")
            .apply(
                lambda values: class_filter
                in [value.strip() for value in values]
            )
        ].copy()

    if display_df.empty:
        st.info("현재 필터 조건에 해당하는 학생이 없습니다.")
        return

    status_order = {
        "유사 계정 있음": 0,
        "미가입": 1,
        "가입 완료": 2,
    }

    display_df["_상태정렬"] = display_df["가입상태"].map(
        status_order
    ).fillna(9)

    display_df = (
        display_df.sort_values(
            by=["_상태정렬", "소속반", "학생명"],
            ascending=[True, True, True],
        )
        .drop(columns=["_상태정렬"])
        .reset_index(drop=True)
    )

    st.caption(
        "유사 계정은 관리자 화면의 '오답 계정 이전' 기능으로 "
        "본인 이름 계정에 기록을 옮길 수 있습니다."
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=560,
        column_config={
            "가입상태": st.column_config.TextColumn(
                "가입상태",
                help=(
                    "가입 완료: 정확한 이름 계정 존재 / "
                    "유사 계정 있음: 학교명·숫자 등이 붙은 계정 존재 / "
                    "미가입: 관련 계정 없음"
                ),
            ),
            "오답개수": st.column_config.NumberColumn(
                "오답개수",
                format="%d",
            ),
        },
    )

    st.download_button(
        "현재 가입 현황 엑셀 다운로드",
        data=dataframe_to_excel_bytes(display_df),
        file_name=(
            "전체관리자_학생가입현황.xlsx"
            if current_teacher == ALL_TEACHER_ADMIN
            else f"{normalize_teacher_name(current_teacher)}_담당학생가입현황.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key="download_student_signup_status",
    )

    issue_df = status_df[
        status_df["가입상태"].isin(
            ["유사 계정 있음", "미가입"]
        )
    ].copy()

    if not issue_df.empty:
        st.download_button(
            "유사 계정·미가입 학생만 엑셀 다운로드",
            data=dataframe_to_excel_bytes(issue_df),
            file_name=(
                "전체관리자_유사계정_미가입학생.xlsx"
                if current_teacher == ALL_TEACHER_ADMIN
                else (
                    f"{normalize_teacher_name(current_teacher)}_"
                    "유사계정_미가입학생.xlsx"
                )
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            key="download_student_signup_issues",
            type="primary",
        )



# ============================================================
# 교재 마스터 관리
# ============================================================
def parse_book_bulk_text(raw_text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_rows = []
    error_rows = []

    lines = [
        line.strip()
        for line in str(raw_text or "").splitlines()
        if line.strip()
    ]

    for line_number, line in enumerate(lines, start=1):
        try:
            if "|" in line:
                parts = [part.strip() for part in line.split("|")]
            elif "\t" in line:
                parts = [part.strip() for part in line.split("\t")]
            else:
                parts = [line]

            parts += [""] * (6 - len(parts))
            book_name, grade, subject, publisher, count_raw, category = parts[:6]

            book_name = str(book_name).strip()
            category = str(category).strip() or "교재"

            if not book_name:
                raise ValueError("교재명이 비어 있습니다.")

            if str(count_raw).strip():
                digits = re.sub(r"[^0-9]", "", str(count_raw))
                if not digits:
                    raise ValueError("문항 수를 숫자로 입력해주세요.")
                question_count = int(digits)
            else:
                question_count = None

            valid_rows.append(
                {
                    "줄번호": line_number,
                    "교재명": book_name,
                    "학년": str(grade).strip(),
                    "과목": str(subject).strip(),
                    "출판사": str(publisher).strip(),
                    "문항수": question_count,
                    "분류": category,
                    "원문": line,
                }
            )
        except Exception as error:
            error_rows.append(
                {
                    "줄번호": line_number,
                    "원문": line,
                    "오류": str(error),
                }
            )

    return (
        pd.DataFrame(valid_rows),
        pd.DataFrame(error_rows),
    )


def register_book_rows(valid_df: pd.DataFrame) -> dict:
    if valid_df.empty:
        return {"created": 0, "skipped": 0}

    existing_df = get_book_master_df(active_only=False)
    existing_names = set(
        existing_df.get("교재명", pd.Series(dtype=str))
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    rows = []
    skipped = 0

    for _, row in valid_df.iterrows():
        book_name = str(row["교재명"]).strip()

        if book_name in existing_names:
            skipped += 1
            continue

        rows.append(
            {
                "book_name": book_name,
                "grade": str(row.get("학년", "") or "").strip(),
                "subject": str(row.get("과목", "") or "").strip(),
                "publisher": str(row.get("출판사", "") or "").strip(),
                "question_count": (
                    int(row["문항수"])
                    if pd.notna(row.get("문항수"))
                    else None
                ),
                "category": str(row.get("분류", "교재") or "교재").strip(),
                "is_active": True,
                "created_at": now_kst_iso(),
            }
        )
        existing_names.add(book_name)

    if rows:
        supabase.table("book_master").insert(rows).execute()

    return {"created": len(rows), "skipped": skipped}


def set_book_active(book_id: int, is_active: bool):
    (
        supabase.table("book_master")
        .update({"is_active": bool(is_active)})
        .eq("id", int(book_id))
        .execute()
    )


def update_book_master(
    book_id: int,
    book_name: str,
    grade: str,
    subject: str,
    publisher: str,
    question_count: int | None,
    category: str,
):
    current = (
        supabase.table("book_master")
        .select("book_name")
        .eq("id", int(book_id))
        .limit(1)
        .execute()
    )

    if not current.data:
        raise ValueError("수정할 교재를 찾을 수 없습니다.")

    old_name = str(current.data[0].get("book_name", "")).strip()
    new_name = str(book_name or "").strip()

    if not new_name:
        raise ValueError("교재명을 입력해주세요.")

    (
        supabase.table("book_master")
        .update(
            {
                "book_name": new_name,
                "grade": str(grade or "").strip(),
                "subject": str(subject or "").strip(),
                "publisher": str(publisher or "").strip(),
                "question_count": question_count,
                "category": str(category or "교재").strip(),
            }
        )
        .eq("id", int(book_id))
        .execute()
    )

    if old_name and old_name != new_name:
        supabase.table("wrong_answers").update(
            {"unit": new_name}
        ).eq("unit", old_name).execute()

        supabase.table("print_status").update(
            {"book_name": new_name}
        ).eq("book_name", old_name).execute()


def initialize_default_books() -> int:
    existing_df = get_book_master_df(active_only=False)
    existing_names = set(
        existing_df.get("교재명", pd.Series(dtype=str))
        .dropna()
        .astype(str)
        .tolist()
    )

    rows = []

    for name in BOOKS:
        if name in existing_names:
            continue

        rows.append(
            {
                "book_name": name,
                "grade": "",
                "subject": "",
                "publisher": "",
                "question_count": None,
                "category": "기존 교재",
                "is_active": True,
                "created_at": now_kst_iso(),
            }
        )

    if rows:
        supabase.table("book_master").insert(rows).execute()

    return len(rows)


def render_book_admin():
    st.subheader("📚 교재 관리")

    st.warning(
        "교재명을 수정하면 기존 오답 기록의 교재명도 함께 변경됩니다. "
        "선택한 교재가 맞는지 반드시 확인해주세요."
    )

    if st.button(
        "기존 기본 교재 목록 불러오기",
        key="book_default_import",
        use_container_width=True,
    ):
        count = initialize_default_books()
        if count:
            st.success(f"기존 교재 {count}개를 등록했습니다.")
        else:
            st.info("기존 기본 교재가 이미 등록되어 있습니다.")
        st.rerun()

    bulk_tab, edit_tab, status_tab = st.tabs(
        ["📋 복붙 등록", "✏️ 교재 수정", "👁️ 사용 여부"]
    )

    with bulk_tab:
        st.caption(
            "형식: 교재명 | 학년 | 과목 | 출판사 | 문항수 | 분류"
        )
        st.code(
            "고쟁이 미적분2 | 고2 | 미적분2 | 이투스 | 724 | 내신교재\n"
            "RPM 공통수학2 | 고1 | 공통수학2 | 천재교육 | 560 | 내신교재\n"
            "교재명만 입력",
            language="text",
        )

        raw_text = st.text_area(
            "교재 목록 복붙",
            height=220,
            key="book_bulk_text",
        )

        if st.button(
            "교재 미리보기",
            key="book_bulk_preview",
            use_container_width=True,
        ):
            valid_df, error_df = parse_book_bulk_text(raw_text)
            st.session_state["book_valid_preview"] = valid_df
            st.session_state["book_error_preview"] = error_df

        valid_df = st.session_state.get("book_valid_preview", pd.DataFrame())
        error_df = st.session_state.get("book_error_preview", pd.DataFrame())

        if not valid_df.empty:
            st.success(f"정상 인식: {len(valid_df)}건")
            st.dataframe(valid_df, use_container_width=True, hide_index=True)

        if not error_df.empty:
            st.error(f"오류 행: {len(error_df)}건")
            st.dataframe(error_df, use_container_width=True, hide_index=True)

        confirm = st.checkbox(
            "정상 인식된 교재를 등록합니다.",
            key="book_bulk_confirm",
        )

        if st.button(
            "교재 일괄 등록",
            type="primary",
            key="book_bulk_register",
            disabled=valid_df.empty,
            use_container_width=True,
        ):
            if not confirm:
                st.warning("등록 확인에 체크해주세요.")
            else:
                result = register_book_rows(valid_df)
                st.success(
                    f"신규 {result['created']}건 등록, "
                    f"중복 {result['skipped']}건 제외"
                )
                st.session_state.pop("book_valid_preview", None)
                st.session_state.pop("book_error_preview", None)
                st.rerun()

    book_df = get_book_master_df(active_only=False)

    with edit_tab:
        if book_df.empty:
            st.info("등록된 교재가 없습니다.")
        else:
            options = {
                int(row["교재ID"]): row["교재명"]
                for _, row in book_df.iterrows()
            }

            book_id = st.selectbox(
                "수정할 교재",
                options=list(options.keys()),
                format_func=lambda value: options[value],
                key="book_edit_id",
            )

            row = book_df[book_df["교재ID"] == book_id].iloc[0]

            name = st.text_input(
                "교재명",
                value=str(row["교재명"]),
                key="book_edit_name",
            )
            grade = st.text_input(
                "학년",
                value=str(row["학년"] or ""),
                key="book_edit_grade",
            )
            subject = st.text_input(
                "과목",
                value=str(row["과목"] or ""),
                key="book_edit_subject",
            )
            publisher = st.text_input(
                "출판사",
                value=str(row["출판사"] or ""),
                key="book_edit_publisher",
            )
            count = st.number_input(
                "문항 수",
                min_value=0,
                value=(
                    int(row["문항수"])
                    if pd.notna(row["문항수"])
                    else 0
                ),
                key="book_edit_count",
            )
            category = st.text_input(
                "분류",
                value=str(row["분류"] or "교재"),
                key="book_edit_category",
            )

            edit_confirm = st.checkbox(
                f"'{row['교재명']}' 교재가 맞는지 확인했습니다.",
                key="book_edit_confirm",
            )

            if st.button(
                "교재 정보 저장",
                type="primary",
                key="book_edit_save",
                use_container_width=True,
            ):
                if not edit_confirm:
                    st.error("수정할 교재가 맞는지 확인 후 체크해주세요.")
                else:
                    update_book_master(
                        book_id,
                        name,
                        grade,
                        subject,
                        publisher,
                        int(count) if count > 0 else None,
                        category,
                    )
                    st.success("교재 정보를 수정했습니다.")
                    st.rerun()

    with status_tab:
        if book_df.empty:
            st.info("등록된 교재가 없습니다.")
        else:
            st.dataframe(
                book_df,
                use_container_width=True,
                hide_index=True,
                height=450,
            )

            options = {
                int(row["교재ID"]): (
                    f"{row['교재명']} · "
                    + ("사용중" if row["사용중"] else "숨김")
                )
                for _, row in book_df.iterrows()
            }

            book_id = st.selectbox(
                "사용 여부 변경",
                options=list(options.keys()),
                format_func=lambda value: options[value],
                key="book_status_id",
            )

            active = bool(
                book_df.loc[
                    book_df["교재ID"] == book_id,
                    "사용중",
                ].iloc[0]
            )

            if st.button(
                "학생 화면에서 숨기기" if active else "다시 표시",
                key="book_status_toggle",
                use_container_width=True,
            ):
                set_book_active(book_id, not active)
                st.rerun()

# ============================================================
# 학교 기출 관리
# ============================================================
def make_school_exam_display_name(
    exam_year: int,
    school_name: str,
    subject: str,
    exam_type: str,
) -> str:
    parts = [
        str(exam_year).strip(),
        str(subject or "").strip(),
        str(school_name or "").strip(),
        str(exam_type or "").strip(),
    ]
    return " ".join(part for part in parts if part)


def normalize_exam_year(value) -> int:
    raw = re.sub(r"[^0-9]", "", str(value or ""))

    if not raw:
        raise ValueError("연도를 확인할 수 없습니다.")

    year = int(raw)

    if year < 100:
        year += 2000

    if year < 2000 or year > 2100:
        raise ValueError("연도는 2000~2100 사이로 입력해주세요.")

    return year


def parse_school_exam_bulk_text(raw_text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    관리자 메모장 복붙 내용을 학교 기출 목록으로 변환합니다.

    권장 형식:
    연도 | 학교 | 과목 | 시험구분 | 문항수 | 범위

    예:
    2025 | 울산고 | 미적분1 | 2학기 중간 | 30 | 함수의 극한~접선
    2025 | 학성고 | 미적분1 | 2학기 중간 | 28 |

    탭 또는 쉼표 구분도 허용합니다.
    간단 형식 '2025 미적분1 울산고 시험'도 인식하지만,
    정확한 등록을 위해 구분자 형식을 권장합니다.
    """
    valid_rows = []
    error_rows = []

    lines = [
        line.strip()
        for line in str(raw_text or "").splitlines()
        if line.strip()
    ]

    for line_number, line in enumerate(lines, start=1):
        try:
            if "|" in line:
                parts = [part.strip() for part in line.split("|")]
            elif "\t" in line:
                parts = [part.strip() for part in line.split("\t")]
            elif "," in line and line.count(",") >= 3:
                parts = [part.strip() for part in line.split(",")]
            else:
                # 간단 문장형 보조 인식
                tokens = line.split()
                if len(tokens) < 4:
                    raise ValueError(
                        "항목이 부족합니다. 연도 | 학교 | 과목 | 시험구분 형식으로 입력해주세요."
                    )

                year_token = tokens[0]
                school_index = next(
                    (
                        index
                        for index, token in enumerate(tokens[1:], start=1)
                        if token.endswith(("고", "여고", "외고", "중"))
                    ),
                    None,
                )

                if school_index is None:
                    raise ValueError("학교명을 확인할 수 없습니다.")

                subject = tokens[1] if school_index != 1 else (
                    tokens[2] if len(tokens) > 2 else ""
                )
                school_name = tokens[school_index]
                exam_tokens = [
                    token
                    for index, token in enumerate(tokens[1:], start=1)
                    if index not in {school_index}
                    and token != subject
                ]

                parts = [
                    year_token,
                    school_name,
                    subject,
                    " ".join(exam_tokens) or "시험",
                    "",
                    "",
                ]

            parts += [""] * (6 - len(parts))
            year_raw, school_name, subject, exam_type, question_count_raw, scope = parts[:6]

            exam_year = normalize_exam_year(year_raw)
            school_name = str(school_name).strip()
            subject = str(subject).strip()
            exam_type = str(exam_type).strip() or "시험"
            scope = str(scope).strip()

            if not school_name:
                raise ValueError("학교가 비어 있습니다.")
            if not subject:
                raise ValueError("과목이 비어 있습니다.")

            if str(question_count_raw).strip():
                question_count = int(
                    re.sub(r"[^0-9]", "", str(question_count_raw))
                )
                if question_count <= 0:
                    raise ValueError("문항 수는 1 이상이어야 합니다.")
            else:
                question_count = None

            display_name = make_school_exam_display_name(
                exam_year,
                school_name,
                subject,
                exam_type,
            )

            valid_rows.append(
                {
                    "줄번호": line_number,
                    "연도": exam_year,
                    "학교": school_name,
                    "과목": subject,
                    "시험구분": exam_type,
                    "문항수": question_count,
                    "범위": scope,
                    "표시명": display_name,
                    "원문": line,
                }
            )
        except Exception as error:
            error_rows.append(
                {
                    "줄번호": line_number,
                    "원문": line,
                    "오류": str(error),
                }
            )

    valid_df = pd.DataFrame(
        valid_rows,
        columns=[
            "줄번호", "연도", "학교", "과목", "시험구분",
            "문항수", "범위", "표시명", "원문",
        ],
    )
    error_df = pd.DataFrame(
        error_rows,
        columns=["줄번호", "원문", "오류"],
    )

    return valid_df, error_df


def get_school_exam_master_df(active_only: bool = True) -> pd.DataFrame:
    filters = [("is_active", "eq", True)] if active_only else []

    rows = fetch_all_rows(
        "school_exam_master",
        (
            "id,exam_year,school_name,subject,exam_type,"
            "question_count,scope,display_name,is_active,created_at"
        ),
        filters=filters,
        order_column="exam_year",
        desc=True,
    )

    columns = [
        "기출ID", "연도", "학교", "과목", "시험구분",
        "문항수", "범위", "표시명", "사용중", "등록일시",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "기출ID": row.get("id"),
                "연도": row.get("exam_year"),
                "학교": row.get("school_name", ""),
                "과목": row.get("subject", ""),
                "시험구분": row.get("exam_type", ""),
                "문항수": row.get("question_count"),
                "범위": row.get("scope", ""),
                "표시명": row.get("display_name", ""),
                "사용중": bool(row.get("is_active", True)),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ],
        columns=columns,
    )


def register_school_exam_rows(valid_df: pd.DataFrame) -> dict:
    if valid_df.empty:
        return {"created": 0, "skipped": 0}

    existing_df = get_school_exam_master_df(active_only=False)
    existing_keys = {
        (
            int(row["연도"]),
            str(row["학교"]).strip(),
            str(row["과목"]).strip(),
            str(row["시험구분"]).strip(),
        )
        for _, row in existing_df.iterrows()
    }

    insert_rows = []
    skipped = 0

    for _, row in valid_df.iterrows():
        key = (
            int(row["연도"]),
            str(row["학교"]).strip(),
            str(row["과목"]).strip(),
            str(row["시험구분"]).strip(),
        )

        if key in existing_keys:
            skipped += 1
            continue

        insert_rows.append(
            {
                "exam_year": int(row["연도"]),
                "school_name": str(row["학교"]).strip(),
                "subject": str(row["과목"]).strip(),
                "exam_type": str(row["시험구분"]).strip(),
                "question_count": (
                    int(row["문항수"])
                    if pd.notna(row["문항수"])
                    else None
                ),
                "scope": str(row["범위"] or "").strip(),
                "display_name": str(row["표시명"]).strip(),
                "is_active": True,
                "created_at": now_kst_iso(),
            }
        )
        existing_keys.add(key)

    if insert_rows:
        supabase.table("school_exam_master").insert(insert_rows).execute()

    return {
        "created": len(insert_rows),
        "skipped": skipped,
    }


def set_school_exam_active(exam_id: int, is_active: bool):
    (
        supabase.table("school_exam_master")
        .update({"is_active": bool(is_active)})
        .eq("id", int(exam_id))
        .execute()
    )


def get_existing_school_exam_numbers(
    username: str,
    exam_id: int,
) -> set[str]:
    rows = fetch_all_rows(
        "school_exam_wrong_answers",
        "problem",
        filters=[
            ("username", "eq", username),
            ("exam_id", "eq", int(exam_id)),
        ],
    )

    numbers = set()

    for row in rows:
        numbers.update(parse_problem_numbers(row.get("problem", "")))

    return numbers


def add_school_exam_wrong_answer(
    username: str,
    exam_id: int,
    problem_number: str,
    memo: str,
) -> dict:
    submitted_numbers = parse_problem_numbers(problem_number)

    if not submitted_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": [],
            "message": "저장할 기출 오답번호가 없습니다.",
        }

    existing_numbers = get_existing_school_exam_numbers(
        username,
        exam_id,
    )

    new_numbers = [
        number
        for number in submitted_numbers
        if number not in existing_numbers
    ]
    duplicate_numbers = [
        number
        for number in submitted_numbers
        if number in existing_numbers
    ]

    if not new_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": duplicate_numbers,
            "message": "입력한 기출 오답번호가 모두 이미 저장되어 있습니다.",
        }

    (
        supabase.table("school_exam_wrong_answers")
        .insert(
            {
                "username": username,
                "exam_id": int(exam_id),
                "problem": format_problem_numbers(new_numbers),
                "memo": str(memo or "").strip(),
                "created_at": now_kst_iso(),
            }
        )
        .execute()
    )

    return {
        "saved": True,
        "new_numbers": new_numbers,
        "duplicate_numbers": duplicate_numbers,
        "message": "학교 기출 오답을 저장했습니다.",
    }


def get_school_exam_wrong_answers_df() -> pd.DataFrame:
    answer_rows = fetch_all_rows(
        "school_exam_wrong_answers",
        "id,username,exam_id,problem,memo,created_at",
        order_column="id",
        desc=True,
    )
    exam_df = get_school_exam_master_df(active_only=False)

    columns = [
        "기록ID", "학생", "기출ID", "연도", "학교", "과목",
        "시험구분", "기출명", "문제번호", "비고", "작성일시",
    ]

    if not answer_rows:
        return pd.DataFrame(columns=columns)

    exam_map = {
        int(row["기출ID"]): row
        for _, row in exam_df.iterrows()
    }

    records = []

    for row in answer_rows:
        exam_id = int(row.get("exam_id"))
        exam = exam_map.get(exam_id, {})

        records.append(
            {
                "기록ID": row.get("id"),
                "학생": row.get("username", ""),
                "기출ID": exam_id,
                "연도": exam.get("연도", ""),
                "학교": exam.get("학교", ""),
                "과목": exam.get("과목", ""),
                "시험구분": exam.get("시험구분", ""),
                "기출명": exam.get("표시명", f"기출 ID {exam_id}"),
                "문제번호": row.get("problem", ""),
                "비고": row.get("memo", ""),
                "작성일시": row.get("created_at", ""),
            }
        )

    return pd.DataFrame(records, columns=columns)


def get_my_school_exam_wrong_answers(username: str) -> pd.DataFrame:
    df = get_school_exam_wrong_answers_df()

    if df.empty:
        return df

    return df[df["학생"] == username].copy()


def merge_school_exam_answers_for_paper(
    df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "학생명", "연도", "학교", "과목", "시험구분",
        "기출명", "문제번호", "비고", "PDF상단제목", "파일명",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    records = []

    grouped = df.groupby(
        ["학생", "연도", "학교", "과목", "시험구분", "기출명"],
        sort=False,
        dropna=False,
    )

    for (
        student,
        year,
        school,
        subject,
        exam_type,
        exam_name,
    ), group in grouped:
        numbers = []
        memos = []

        for _, row in group.iterrows():
            for number in parse_problem_numbers(row["문제번호"]):
                if number not in numbers:
                    numbers.append(number)

            memo = str(row.get("비고", "") or "").strip()
            if memo and memo not in memos:
                memos.append(memo)

        title = f"{year} {subject} {school} {exam_type} 학교 기출 오답 Paper"

        records.append(
            {
                "학생명": student,
                "연도": year,
                "학교": school,
                "과목": subject,
                "시험구분": exam_type,
                "기출명": exam_name,
                "문제번호": format_problem_numbers(numbers),
                "비고": " / ".join(memos),
                "PDF상단제목": title,
                "파일명": (
                    f"[학교기출오답][{school}][{student}]"
                    f"[{year}_{subject}_{exam_type}].pdf"
                ),
            }
        )

    return pd.DataFrame(records, columns=columns)


def render_student_school_exam_wrong_answer():
    st.subheader("🏫 학교 기출 오답 작성")

    st.warning(
        "⚠️ 주의: 각 학교와 시험을 정확히 확인한 뒤 오답번호를 작성하세요. "
        "잘못된 학교 기출을 선택하면 오답 Paper가 다른 시험으로 생성될 수 있습니다."
    )

    exam_df = get_school_exam_master_df(active_only=True)

    if exam_df.empty:
        st.info("현재 등록된 학교 기출 시험이 없습니다. 관리자에게 문의해주세요.")
        return

    school_options = sorted(
        exam_df["학교"].dropna().astype(str).unique().tolist()
    )

    selected_school = st.selectbox(
        "1. 학교 선택",
        school_options,
        key="student_school_exam_school",
    )

    school_df = exam_df[
        exam_df["학교"] == selected_school
    ].copy()

    exam_option_map = {
        int(row["기출ID"]): str(row["표시명"])
        for _, row in school_df.sort_values(
            by=["연도", "과목", "시험구분"],
            ascending=[False, True, True],
        ).iterrows()
    }

    selected_exam_id = st.selectbox(
        "2. 학교 기출 시험 선택",
        options=list(exam_option_map.keys()),
        format_func=lambda exam_id: exam_option_map[exam_id],
        key="student_school_exam_exam",
    )

    selected_exam = school_df[
        school_df["기출ID"] == selected_exam_id
    ].iloc[0]

    st.info(
        f"현재 선택: **{selected_exam['표시명']}**"
        + (
            f" · 범위: {selected_exam['범위']}"
            if str(selected_exam["범위"]).strip()
            else ""
        )
    )

    problem_number = st.text_input(
        "3. 기출 오답번호",
        placeholder="예: 3, 7, 12, 18",
        key="student_school_exam_problem",
    )

    memo = st.text_area(
        "4. 비고",
        placeholder="예: 계산 실수, 다시 질문 필요, 서술형 풀이 확인",
        key="student_school_exam_memo",
    )

    confirm_exam = st.checkbox(
        (
            f"'{selected_exam['학교']}'의 "
            f"'{selected_exam['표시명']}' 시험이 맞는지 확인했습니다."
        ),
        key="student_school_exam_confirm",
    )

    if st.button(
        "학교 기출 오답 저장",
        type="primary",
        key="student_school_exam_save",
        use_container_width=True,
    ):
        if not problem_number.strip():
            st.warning("기출 오답번호를 입력해주세요.")
        elif not confirm_exam:
            st.error(
                "학교와 시험을 다시 확인한 뒤 확인 항목에 체크해주세요."
            )
        else:
            result = add_school_exam_wrong_answer(
                st.session_state.student_user,
                int(selected_exam_id),
                problem_number,
                memo,
            )

            if result["saved"]:
                st.success(
                    "학교 기출 오답을 저장했습니다: "
                    + ", ".join(result["new_numbers"])
                )

                if result["duplicate_numbers"]:
                    st.info(
                        "이미 저장된 번호는 제외했습니다: "
                        + ", ".join(result["duplicate_numbers"])
                    )

                st.rerun()
            else:
                st.warning(result["message"])

    st.divider()
    st.subheader("내 학교 기출 오답 목록")

    my_df = get_my_school_exam_wrong_answers(
        st.session_state.student_user
    )

    if my_df.empty:
        st.info("아직 저장한 학교 기출 오답이 없습니다.")
    else:
        st.dataframe(
            my_df[
                [
                    "연도", "학교", "과목", "시험구분",
                    "기출명", "문제번호", "비고", "작성일시",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_teacher_school_exam_management():
    st.subheader("🏫 학교 기출 오답 현황·Paper")

    current_teacher = st.session_state.teacher_name
    answer_df = get_school_exam_wrong_answers_df()

    if answer_df.empty:
        st.info("아직 등록된 학교 기출 오답이 없습니다.")
        return

    if current_teacher != ALL_TEACHER_ADMIN:
        roster = get_roster_df()
        teacher_students = set(
            roster.loc[
                roster["담당선생님"].apply(normalize_teacher_name)
                == normalize_teacher_name(current_teacher),
                "학생명",
            ]
            .dropna()
            .astype(str)
            .tolist()
        )
        answer_df = answer_df[
            answer_df["학생"].isin(teacher_students)
        ].copy()

    if answer_df.empty:
        st.info("현재 담당 학생의 학교 기출 오답이 없습니다.")
        return

    filter1, filter2, filter3 = st.columns(3)

    with filter1:
        school_filter = st.selectbox(
            "학교 필터",
            ["전체"] + sorted(
                answer_df["학교"].dropna().astype(str).unique().tolist()
            ),
            key="teacher_school_exam_school_filter",
        )

    filtered_df = answer_df.copy()

    if school_filter != "전체":
        filtered_df = filtered_df[
            filtered_df["학교"] == school_filter
        ].copy()

    with filter2:
        subject_filter = st.selectbox(
            "과목 필터",
            ["전체"] + sorted(
                filtered_df["과목"].dropna().astype(str).unique().tolist()
            ),
            key="teacher_school_exam_subject_filter",
        )

    if subject_filter != "전체":
        filtered_df = filtered_df[
            filtered_df["과목"] == subject_filter
        ].copy()

    with filter3:
        exam_filter = st.selectbox(
            "시험 필터",
            ["전체"] + sorted(
                filtered_df["기출명"].dropna().astype(str).unique().tolist()
            ),
            key="teacher_school_exam_exam_filter",
        )

    if exam_filter != "전체":
        filtered_df = filtered_df[
            filtered_df["기출명"] == exam_filter
        ].copy()

    student_options = sorted(
        filtered_df["학생"].dropna().astype(str).unique().tolist()
    )

    selected_students = st.multiselect(
        "Paper를 만들 학생 선택",
        student_options,
        default=student_options,
        key="teacher_school_exam_students",
    )

    display_df = filtered_df[
        filtered_df["학생"].isin(selected_students)
    ].copy()

    if display_df.empty:
        st.info("현재 조건에 해당하는 기록이 없습니다.")
        return

    st.dataframe(
        display_df[
            [
                "학생", "연도", "학교", "과목", "시험구분",
                "기출명", "문제번호", "비고", "작성일시",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    paper_df = merge_school_exam_answers_for_paper(display_df)

    st.download_button(
        "학교 기출 오답 Paper 생성용 엑셀 다운로드",
        data=dataframe_to_excel_bytes(paper_df),
        file_name="학교_기출_오답Paper_생성용.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="teacher_school_exam_paper_download",
        type="primary",
    )


def render_school_exam_admin():
    st.subheader("🏫 학교 기출 관리")

    st.warning(
        "등록 전에 연도·학교·과목·시험구분을 반드시 확인하세요. "
        "학생은 여기에서 등록된 학교와 시험을 선택해 오답번호를 작성합니다."
    )

    st.markdown("#### 여러 기출 복붙 등록")
    st.caption(
        "권장 형식: 연도 | 학교 | 과목 | 시험구분 | 문항수 | 범위"
    )
    st.code(
        "2025 | 울산고 | 미적분1 | 2학기 중간 | 30 | 함수의 극한~접선\n"
        "2025 | 학성고 | 미적분1 | 2학기 중간 | 28 |",
        language="text",
    )

    raw_text = st.text_area(
        "메모장 내용을 그대로 붙여넣으세요.",
        height=220,
        key="school_exam_bulk_text",
        placeholder=(
            "2025 | 울산고 | 미적분1 | 2학기 중간 | 30 | 함수의 극한~접선\n"
            "2025 | 학성고 | 미적분1 | 2학기 중간 | 28 |"
        ),
    )

    if st.button(
        "복붙 내용 미리보기",
        key="school_exam_preview",
        use_container_width=True,
    ):
        valid_df, error_df = parse_school_exam_bulk_text(raw_text)
        st.session_state["school_exam_valid_preview"] = valid_df
        st.session_state["school_exam_error_preview"] = error_df

    valid_df = st.session_state.get(
        "school_exam_valid_preview",
        pd.DataFrame(),
    )
    error_df = st.session_state.get(
        "school_exam_error_preview",
        pd.DataFrame(),
    )

    if not valid_df.empty:
        st.success(f"정상 인식: {len(valid_df)}건")
        st.dataframe(
            valid_df[
                [
                    "줄번호", "연도", "학교", "과목",
                    "시험구분", "문항수", "범위", "표시명",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    if not error_df.empty:
        st.error(f"오류 행: {len(error_df)}건")
        st.dataframe(
            error_df,
            use_container_width=True,
            hide_index=True,
        )

    register_confirm = st.checkbox(
        "미리보기의 정상 항목을 학교 기출 목록에 등록합니다.",
        key="school_exam_register_confirm",
    )

    if st.button(
        "정상 항목 일괄 등록",
        type="primary",
        key="school_exam_register",
        use_container_width=True,
        disabled=valid_df.empty,
    ):
        if not register_confirm:
            st.warning("등록 확인 항목에 체크해주세요.")
        else:
            result = register_school_exam_rows(valid_df)
            st.success(
                f"신규 {result['created']}건 등록, "
                f"중복 {result['skipped']}건 제외했습니다."
            )
            st.session_state.pop("school_exam_valid_preview", None)
            st.session_state.pop("school_exam_error_preview", None)
            st.rerun()

    st.divider()
    st.markdown("#### 현재 학교 기출 목록")

    exam_df = get_school_exam_master_df(active_only=False)

    if exam_df.empty:
        st.info("등록된 학교 기출이 없습니다.")
        return

    st.dataframe(
        exam_df,
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    option_map = {
        int(row["기출ID"]): (
            f"{row['표시명']} · "
            + ("사용중" if row["사용중"] else "숨김")
        )
        for _, row in exam_df.iterrows()
    }

    selected_exam_id = st.selectbox(
        "상태를 변경할 기출",
        options=list(option_map.keys()),
        format_func=lambda exam_id: option_map[exam_id],
        key="school_exam_admin_selected",
    )

    selected_active = bool(
        exam_df.loc[
            exam_df["기출ID"] == selected_exam_id,
            "사용중",
        ].iloc[0]
    )

    if st.button(
        "학생 화면에서 숨기기" if selected_active else "학생 화면에 다시 표시",
        key="school_exam_toggle_active",
        use_container_width=True,
    ):
        set_school_exam_active(
            selected_exam_id,
            not selected_active,
        )
        st.rerun()

def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="오답현황")

    output.seek(0)
    return output.getvalue()


# ---------------------- 회원 관리 ----------------------
def get_all_users() -> pd.DataFrame:
    user_rows = fetch_all_rows(
        "users",
        "username,grade,created_at",
        order_column="created_at",
        desc=True
    )

    if not user_rows:
        return pd.DataFrame(
            columns=["학생", "학년", "가입일시", "오답개수"]
        )

    answer_rows = fetch_all_rows("wrong_answers", "username")
    answer_counts = Counter(
        row.get("username", "")
        for row in answer_rows
        if row.get("username")
    )

    records = []

    for row in user_rows:
        username = row.get("username", "")
        records.append(
            {
                "학생": username,
                "학년": row.get("grade") or "미지정",
                "가입일시": row.get("created_at", ""),
                "오답개수": answer_counts.get(username, 0)
            }
        )

    return pd.DataFrame(records)


def delete_user(username: str, delete_answers: bool = True):
    """
    users → wrong_answers 외래키가 ON DELETE CASCADE로 설정되어 있으므로,
    계정을 삭제하면 해당 학생의 오답 기록도 함께 삭제됩니다.
    """
    if delete_answers:
        (
            supabase.table("wrong_answers")
            .delete()
            .eq("username", username)
            .execute()
        )

    (
        supabase.table("users")
        .delete()
        .eq("username", username)
        .execute()
    )


def reset_user_password(username: str, new_password: str):
    (
        supabase.table("users")
        .update(
            {
                "password_hash": hash_pw(new_password),
                "temp_password": new_password
            }
        )
        .eq("username", username)
        .execute()
    )


def update_user_grade(username: str, new_grade: str):
    (
        supabase.table("users")
        .update({"grade": new_grade})
        .eq("username", username)
        .execute()
    )



def username_exists(username: str, exclude_username: str | None = None) -> bool:
    """users 테이블에서 학생 이름의 중복 여부를 확인합니다."""
    username = str(username or "").strip()

    if not username:
        return False

    response = (
        supabase.table("users")
        .select("username")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    return username != str(exclude_username or "").strip()


def rename_student_everywhere(old_name: str, new_name: str) -> dict:
    """
    외래키 제약을 안전하게 지키면서 학생 이름을 변경합니다.

    처리 순서:
    1. 기존 users 계정 정보를 읽음
    2. 새 이름의 users 계정을 먼저 생성
    3. wrong_answers와 student_roster를 새 이름으로 변경
    4. 기존 users 계정 삭제

    users.username을 먼저 수정하면 wrong_answers 외래키 때문에
    PostgreSQL 오류 23503이 발생하므로 이 순서를 사용합니다.
    """
    old_name = str(old_name or "").strip()
    new_name = str(new_name or "").strip()

    if not old_name or not new_name:
        raise ValueError("현재 이름과 새 이름을 모두 입력해주세요.")

    if old_name == new_name:
        raise ValueError("현재 이름과 새 이름이 같습니다.")

    # 새 이름 중복 확인
    existing_new_user = (
        supabase.table("users")
        .select("username")
        .eq("username", new_name)
        .limit(1)
        .execute()
    )
    if existing_new_user.data:
        raise ValueError("새 이름으로 이미 가입된 학생 계정이 있습니다.")

    existing_new_roster = (
        supabase.table("student_roster")
        .select("id")
        .eq("student_name", new_name)
        .limit(1)
        .execute()
    )
    if existing_new_roster.data:
        raise ValueError(
            "새 이름과 동일한 학생이 명단에 이미 있습니다. "
            "동명이인이라면 이름 뒤에 숫자 등을 붙여 구분해주세요."
        )

    # 기존 계정 정보 읽기
    old_user_response = (
        supabase.table("users")
        .select("username,password_hash,grade,temp_password,created_at")
        .eq("username", old_name)
        .limit(1)
        .execute()
    )

    old_user = old_user_response.data[0] if old_user_response.data else None

    # 계정이 없는 학생도 명단/오답 이름 수정은 가능하게 처리
    new_user_created = False

    try:
        # 1) 새 부모(users) 행을 먼저 생성
        if old_user:
            new_user_payload = {
                "username": new_name,
                "password_hash": old_user.get("password_hash", ""),
                "grade": old_user.get("grade") or "미지정",
                "temp_password": old_user.get("temp_password") or "",
                "created_at": old_user.get("created_at") or now_kst_iso(),
            }

            (
                supabase.table("users")
                .insert(new_user_payload)
                .execute()
            )
            new_user_created = True

        # 2) 자식 테이블을 새 이름으로 이동
        answer_response = (
            supabase.table("wrong_answers")
            .update({"username": new_name})
            .eq("username", old_name)
            .execute()
        )

        roster_response = (
            supabase.table("student_roster")
            .update({"student_name": new_name})
            .eq("student_name", old_name)
            .execute()
        )

        # 3) 기존 부모(users) 행 삭제
        deleted_users = 0
        if old_user:
            delete_response = (
                supabase.table("users")
                .delete()
                .eq("username", old_name)
                .execute()
            )
            deleted_users = len(delete_response.data or [])

        return {
            "users_created": 1 if new_user_created else 0,
            "users_deleted": deleted_users,
            "wrong_answers": len(answer_response.data or []),
            "student_roster": len(roster_response.data or []),
        }

    except Exception:
        # 중간 실패 시 새 계정만 생성된 상태라면 가능한 범위에서 롤백
        # 자식 데이터가 이미 새 이름으로 이동한 경우에는 새 계정을 지우면
        # 다시 외래키 오류가 발생할 수 있으므로 현재 상태를 보존합니다.
        try:
            moved_answer_check = (
                supabase.table("wrong_answers")
                .select("id")
                .eq("username", new_name)
                .limit(1)
                .execute()
            )

            if new_user_created and not moved_answer_check.data:
                (
                    supabase.table("users")
                    .delete()
                    .eq("username", new_name)
                    .execute()
                )
        except Exception:
            pass

        raise


def update_roster_record(
    record_id: int,
    *,
    teacher_name: str,
    class_name: str,
    school_name: str,
    grade: str,
    book_name: str,
):
    """선택한 수강 등록 행의 담당 선생님·반·학교·학년·교재를 변경합니다."""
    payload = {
        "teacher_name": str(teacher_name or "").strip(),
        "class_name": str(class_name or "").strip(),
        "school_name": str(school_name or "").strip(),
        "grade": str(grade or "").strip(),
        "book_name": str(book_name or "").strip(),
    }

    if not payload["teacher_name"]:
        raise ValueError("담당 선생님을 선택해주세요.")
    if not payload["class_name"]:
        raise ValueError("반명을 입력해주세요.")
    if not payload["school_name"]:
        raise ValueError("학교명을 입력해주세요.")
    if not payload["grade"]:
        raise ValueError("학년을 선택해주세요.")
    if not payload["book_name"]:
        raise ValueError("교재를 선택해주세요.")

    (
        supabase.table("student_roster")
        .update(payload)
        .eq("id", int(record_id))
        .execute()
    )


def update_student_grade_everywhere(username: str, new_grade: str):
    """학생 계정 학년과 명단에 등록된 모든 학년을 함께 변경합니다."""
    username = str(username or "").strip()
    new_grade = str(new_grade or "").strip()

    (
        supabase.table("users")
        .update({"grade": new_grade})
        .eq("username", username)
        .execute()
    )

    (
        supabase.table("student_roster")
        .update({"grade": new_grade})
        .eq("student_name", username)
        .execute()
    )


def delete_student_management(
    username: str,
    *,
    delete_user_account: bool,
    delete_roster: bool,
    delete_answers: bool,
) -> dict:
    """선택 옵션에 따라 학생 계정·명단·오답 기록을 삭제합니다."""
    username = str(username or "").strip()
    result = {
        "users": 0,
        "student_roster": 0,
        "wrong_answers": 0,
    }

    if delete_answers:
        response = (
            supabase.table("wrong_answers")
            .delete()
            .eq("username", username)
            .execute()
        )
        result["wrong_answers"] = len(response.data or [])

    if delete_roster:
        response = (
            supabase.table("student_roster")
            .delete()
            .eq("student_name", username)
            .execute()
        )
        result["student_roster"] = len(response.data or [])

    if delete_user_account:
        response = (
            supabase.table("users")
            .delete()
            .eq("username", username)
            .execute()
        )
        result["users"] = len(response.data or [])

    return result



def get_account_wrong_answer_count(username: str) -> int:
    response = (
        supabase.table("wrong_answers")
        .select("id", count="exact")
        .eq("username", str(username or "").strip())
        .execute()
    )

    if getattr(response, "count", None) is not None:
        return int(response.count)

    return len(response.data or [])


def transfer_wrong_answers_between_accounts(
    old_username: str,
    new_username: str,
    *,
    delete_old_account: bool = False,
) -> dict:
    """
    이전 계정의 오답 기록을 새 계정으로 안전하게 이전합니다.

    - 새 계정에 이미 존재하는 동일 교재·문제번호는 중복 저장하지 않습니다.
    - 이전이 끝난 기존 오답 행은 삭제합니다.
    - 선택한 경우 오답이 모두 이전된 이전 계정도 삭제합니다.
    """
    old_username = str(old_username or "").strip()
    new_username = str(new_username or "").strip()

    if not old_username or not new_username:
        raise ValueError("이전 계정과 새 계정을 모두 선택해주세요.")

    if old_username == new_username:
        raise ValueError("이전 계정과 새 계정이 같습니다.")

    old_user = (
        supabase.table("users")
        .select("username")
        .eq("username", old_username)
        .limit(1)
        .execute()
    )

    new_user = (
        supabase.table("users")
        .select("username")
        .eq("username", new_username)
        .limit(1)
        .execute()
    )

    if not old_user.data:
        raise ValueError("이전 계정을 찾을 수 없습니다.")

    if not new_user.data:
        raise ValueError(
            "새 계정을 찾을 수 없습니다. "
            "학생이 새 이름으로 먼저 회원가입했는지 확인해주세요."
        )

    old_rows = fetch_all_rows(
        "wrong_answers",
        "id,unit,problem,memo,created_at",
        filters=[("username", "eq", old_username)],
        order_column="id",
        desc=False,
    )

    if not old_rows:
        raise ValueError("이전 계정에 옮길 오답 기록이 없습니다.")

    target_existing: dict[str, set[str]] = {}

    target_rows = fetch_all_rows(
        "wrong_answers",
        "unit,problem",
        filters=[("username", "eq", new_username)],
        order_column="id",
        desc=False,
    )

    for row in target_rows:
        book = str(row.get("unit", "")).strip()
        target_existing.setdefault(book, set()).update(
            parse_problem_numbers(row.get("problem", ""))
        )

    inserted_rows = 0
    deleted_rows = 0
    moved_numbers = 0
    skipped_duplicate_numbers = 0

    for row in old_rows:
        row_id = int(row["id"])
        book = str(row.get("unit", "")).strip()
        source_numbers = parse_problem_numbers(row.get("problem", ""))
        existing_numbers = target_existing.setdefault(book, set())

        new_numbers = [
            number
            for number in source_numbers
            if number not in existing_numbers
        ]

        skipped_duplicate_numbers += (
            len(source_numbers) - len(new_numbers)
        )

        if new_numbers:
            (
                supabase.table("wrong_answers")
                .insert(
                    {
                        "username": new_username,
                        "unit": book,
                        "problem": format_problem_numbers(new_numbers),
                        "memo": str(row.get("memo", "") or ""),
                        "created_at": (
                            row.get("created_at")
                            or now_kst_iso()
                        ),
                    }
                )
                .execute()
            )

            existing_numbers.update(new_numbers)
            moved_numbers += len(new_numbers)
            inserted_rows += 1

        # 새 계정에 이미 존재하는 문제까지 포함하여 이전 처리가 끝난 행 삭제
        (
            supabase.table("wrong_answers")
            .delete()
            .eq("id", row_id)
            .execute()
        )
        deleted_rows += 1

    old_account_deleted = False

    if delete_old_account:
        remaining = (
            supabase.table("wrong_answers")
            .select("id")
            .eq("username", old_username)
            .limit(1)
            .execute()
        )

        if remaining.data:
            raise ValueError(
                "이전 계정에 오답 기록이 남아 있어 계정을 삭제하지 않았습니다."
            )

        (
            supabase.table("users")
            .delete()
            .eq("username", old_username)
            .execute()
        )
        old_account_deleted = True

    cleanup_duplicate_wrong_answers()

    return {
        "inserted_rows": inserted_rows,
        "deleted_rows": deleted_rows,
        "moved_numbers": moved_numbers,
        "skipped_duplicate_numbers": skipped_duplicate_numbers,
        "old_account_deleted": old_account_deleted,
    }


def render_student_management():
    """관리자 전용 학생 통합 관리 화면입니다."""
    roster_df = get_roster_df()
    users_df = get_all_users()

    roster_names = (
        roster_df["학생명"].dropna().astype(str).tolist()
        if not roster_df.empty
        else []
    )
    user_names = (
        users_df["학생"].dropna().astype(str).tolist()
        if not users_df.empty
        else []
    )

    student_names = sorted(
        {
            name.strip()
            for name in roster_names + user_names
            if str(name).strip()
        }
    )

    if not student_names:
        st.info("관리할 학생이 없습니다.")
        return

    selected_student = st.selectbox(
        "관리할 학생",
        student_names,
        key="student_management_student",
    )

    selected_roster = (
        roster_df[roster_df["학생명"] == selected_student].copy()
        if not roster_df.empty
        else pd.DataFrame()
    )

    st.caption(
        "학생 이름 변경은 계정·오답 기록·학생 명단에 함께 반영됩니다. "
        "담당 선생님·반·학교·교재는 선택한 수강 등록 행에만 반영됩니다."
    )

    (
        tab_name,
        tab_roster,
        tab_transfer,
        tab_delete,
    ) = st.tabs(
        [
            "✏️ 이름·학년 수정",
            "🏫 담당·반·학교·교재",
            "🔄 오답 계정 이전",
            "🗑️ 학생 삭제",
        ]
    )

    with tab_name:
        st.markdown("#### 학생 이름 수정")

        new_student_name = st.text_input(
            "새 학생 이름",
            value=selected_student,
            key="student_management_new_name",
        )

        rename_confirm = st.checkbox(
            "계정·오답 기록·학생 명단의 이름을 모두 변경합니다.",
            key="student_management_rename_confirm",
        )

        if st.button(
            "학생 이름 변경",
            type="primary",
            key="student_management_rename_button",
        ):
            if not rename_confirm:
                st.warning("이름 변경 확인 항목에 체크해주세요.")
            else:
                try:
                    rename_student_everywhere(
                        selected_student,
                        new_student_name,
                    )
                    st.success(
                        f"'{selected_student}' 학생의 이름을 "
                        f"'{new_student_name.strip()}'으로 변경했습니다."
                    )
                    st.rerun()
                except Exception as error:
                    st.error(f"이름 변경 중 오류가 발생했습니다: {error}")

        st.divider()
        st.markdown("#### 학생 학년 일괄 수정")

        current_grade = "미지정"

        if not users_df.empty:
            grade_values = users_df.loc[
                users_df["학생"] == selected_student,
                "학년",
            ].tolist()
            if grade_values:
                current_grade = str(grade_values[0])

        if current_grade == "미지정" and not selected_roster.empty:
            current_grade = str(selected_roster.iloc[0]["학년"])

        grade_options = ["미지정"] + GRADES
        grade_index = (
            grade_options.index(current_grade)
            if current_grade in grade_options
            else 0
        )

        new_student_grade = st.selectbox(
            "새 학년",
            grade_options,
            index=grade_index,
            key="student_management_grade",
        )

        grade_confirm = st.checkbox(
            "학생 계정과 모든 수강 명단의 학년을 함께 변경합니다.",
            key="student_management_grade_confirm",
        )

        if st.button(
            "학생 학년 변경",
            key="student_management_grade_button",
        ):
            if not grade_confirm:
                st.warning("학년 변경 확인 항목에 체크해주세요.")
            else:
                try:
                    update_student_grade_everywhere(
                        selected_student,
                        new_student_grade,
                    )
                    st.success(
                        f"{selected_student} 학생의 학년을 "
                        f"{new_student_grade}(으)로 변경했습니다."
                    )
                    st.rerun()
                except Exception as error:
                    st.error(f"학년 변경 중 오류가 발생했습니다: {error}")

    with tab_roster:
        if selected_roster.empty:
            st.info(
                "이 학생은 학생 명단에 등록된 수강 정보가 없습니다. "
                "명단 엑셀 업로드로 먼저 등록해주세요."
            )
        else:
            option_map = {}

            for _, row in selected_roster.iterrows():
                label = (
                    f"{row['반명']} | {row['담당선생님']} | "
                    f"{row['학교명']} | {row['학년']} | "
                    f"{row['매칭교재']} | ID {row['기록ID']}"
                )
                option_map[label] = int(row["기록ID"])

            selected_label = st.selectbox(
                "수정할 수강 등록",
                list(option_map.keys()),
                key="student_management_roster_record",
            )

            selected_record_id = option_map[selected_label]
            selected_row = selected_roster[
                selected_roster["기록ID"] == selected_record_id
            ].iloc[0]

            teacher_options = list(
                dict.fromkeys(
                    TEACHERS
                    + sorted(
                        roster_df["담당선생님"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )
                )
            )
            current_teacher = str(selected_row["담당선생님"])
            if current_teacher not in teacher_options:
                teacher_options.append(current_teacher)

            teacher_index = teacher_options.index(current_teacher)

            new_teacher = st.selectbox(
                "담당 선생님",
                teacher_options,
                index=teacher_index,
                key="student_management_teacher",
            )

            new_class_name = st.text_input(
                "반명",
                value=str(selected_row["반명"]),
                key="student_management_class",
            )

            new_school_name = st.text_input(
                "학교명",
                value=str(selected_row["학교명"]),
                key="student_management_school",
            )

            roster_grade_options = ["미지정"] + GRADES
            current_roster_grade = str(selected_row["학년"])
            roster_grade_index = (
                roster_grade_options.index(current_roster_grade)
                if current_roster_grade in roster_grade_options
                else 0
            )

            new_roster_grade = st.selectbox(
                "학년",
                roster_grade_options,
                index=roster_grade_index,
                key="student_management_roster_grade",
            )

            book_options = list(
                dict.fromkeys(
                    BOOKS
                    + sorted(
                        roster_df["매칭교재"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )
                )
            )
            current_book = str(selected_row["매칭교재"])
            if current_book not in book_options:
                book_options.append(current_book)

            book_index = book_options.index(current_book)

            new_book = st.selectbox(
                "교재",
                book_options,
                index=book_index,
                key="student_management_book",
            )

            roster_confirm = st.checkbox(
                "선택한 수강 등록 정보를 변경합니다.",
                key="student_management_roster_confirm",
            )

            if st.button(
                "수강 정보 저장",
                type="primary",
                key="student_management_roster_button",
            ):
                if not roster_confirm:
                    st.warning("수강 정보 변경 확인 항목에 체크해주세요.")
                else:
                    try:
                        update_roster_record(
                            selected_record_id,
                            teacher_name=new_teacher,
                            class_name=new_class_name,
                            school_name=new_school_name,
                            grade=new_roster_grade,
                            book_name=new_book,
                        )

                        # users 테이블의 학년도 선택한 학년으로 맞춥니다.
                        (
                            supabase.table("users")
                            .update({"grade": new_roster_grade})
                            .eq("username", selected_student)
                            .execute()
                        )

                        st.success(
                            f"{selected_student} 학생의 선택한 수강 정보를 변경했습니다."
                        )
                        st.rerun()
                    except Exception as error:
                        st.error(f"수강 정보 변경 중 오류가 발생했습니다: {error}")

    with tab_transfer:
        st.markdown("#### 이전 계정의 오답을 새 계정으로 이전")
        st.info(
            "학생이 예전에 다른 이름으로 사용한 계정의 오답 기록을 "
            "현재 본인 이름 계정으로 옮깁니다. "
            "새 계정에 이미 있는 같은 교재·문제번호는 중복 저장하지 않습니다."
        )

        account_df = get_all_users()

        if account_df.empty or len(account_df) < 2:
            st.info("오답을 이전하려면 학생 계정이 2개 이상 필요합니다.")
        else:
            account_names = sorted(
                account_df["학생"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            old_account = st.selectbox(
                "1. 이전 계정",
                account_names,
                key="answer_transfer_old_account",
                help="오답 기록이 현재 저장되어 있는 예전 계정입니다.",
            )

            target_options = [
                name
                for name in account_names
                if name != old_account
            ]

            new_account = st.selectbox(
                "2. 새 계정",
                target_options,
                key="answer_transfer_new_account",
                help="오답 기록을 받을 현재 본인 이름 계정입니다.",
            )

            old_count = get_account_wrong_answer_count(old_account)
            new_count = get_account_wrong_answer_count(new_account)

            count_col1, count_col2 = st.columns(2)
            count_col1.metric(
                f"{old_account} 기존 오답 행",
                old_count,
            )
            count_col2.metric(
                f"{new_account} 현재 오답 행",
                new_count,
            )

            delete_old_after_transfer = st.checkbox(
                "이전 완료 후 예전 계정도 삭제합니다.",
                value=False,
                key="answer_transfer_delete_old",
                help=(
                    "오답만 옮기고 계정은 유지하려면 체크하지 마세요. "
                    "체크하면 이전 완료 후 예전 로그인 계정이 삭제됩니다."
                ),
            )

            transfer_confirm_text = st.text_input(
                f"실행하려면 새 계정 이름 '{new_account}'을 입력하세요.",
                key="answer_transfer_confirm_text",
            )

            if st.button(
                "오답 기록 이전 실행",
                type="primary",
                key="answer_transfer_execute",
                use_container_width=True,
            ):
                if old_count == 0:
                    st.warning("이전 계정에 옮길 오답 기록이 없습니다.")
                elif transfer_confirm_text.strip() != new_account:
                    st.warning("새 계정 이름을 정확히 입력해주세요.")
                else:
                    try:
                        result = transfer_wrong_answers_between_accounts(
                            old_account,
                            new_account,
                            delete_old_account=delete_old_after_transfer,
                        )

                        st.success(
                            f"{old_account} → {new_account} 오답 이전을 완료했습니다."
                        )
                        st.write(
                            f"- 새로 이전한 문제번호: "
                            f"**{result['moved_numbers']}개**"
                        )
                        st.write(
                            f"- 새 계정에 이미 있어 제외한 중복 번호: "
                            f"**{result['skipped_duplicate_numbers']}개**"
                        )
                        st.write(
                            f"- 처리한 이전 계정 오답 행: "
                            f"**{result['deleted_rows']}건**"
                        )

                        if result["old_account_deleted"]:
                            st.write("- 예전 계정도 삭제했습니다.")

                        st.rerun()
                    except Exception as error:
                        st.error(
                            f"오답 계정 이전 중 오류가 발생했습니다: {error}"
                        )

    with tab_delete:
        st.warning(
            "삭제는 되돌릴 수 없습니다. 삭제할 범위를 선택한 뒤 "
            "학생 이름을 정확히 입력해주세요."
        )

        delete_mode = st.radio(
            "삭제 범위",
            [
                "명단에서만 삭제",
                "계정만 삭제",
                "계정·명단·오답 전체 삭제",
            ],
            key="student_management_delete_mode",
        )

        if delete_mode == "명단에서만 삭제":
            delete_account = False
            delete_roster = True
            delete_answers = False
            st.info("학생 계정과 기존 오답은 유지하고 수강 명단만 삭제합니다.")
        elif delete_mode == "계정만 삭제":
            delete_account = True
            delete_roster = False
            delete_answers = False
            st.info(
                "학생 계정만 삭제합니다. DB 외래키 설정에 따라 오답이 함께 "
                "삭제될 수 있으므로 전체 삭제가 필요한 경우 아래 옵션을 권장합니다."
            )
        else:
            delete_account = True
            delete_roster = True
            delete_answers = True
            st.error("학생 계정, 모든 수강 명단, 모든 오답 기록을 삭제합니다.")

        delete_confirmation = st.text_input(
            f"삭제하려면 '{selected_student}'을(를) 그대로 입력하세요.",
            key="student_management_delete_confirmation",
        )

        if st.button(
            "선택한 범위 삭제",
            type="primary",
            key="student_management_delete_button",
        ):
            if delete_confirmation != selected_student:
                st.warning("입력한 학생 이름이 일치하지 않습니다.")
            else:
                try:
                    delete_student_management(
                        selected_student,
                        delete_user_account=delete_account,
                        delete_roster=delete_roster,
                        delete_answers=delete_answers,
                    )
                    st.success(
                        f"{selected_student} 학생의 선택한 정보를 삭제했습니다."
                    )
                    st.rerun()
                except Exception as error:
                    st.error(f"학생 삭제 중 오류가 발생했습니다: {error}")


def normalize_excel_datetime(value) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return now_kst_iso()

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return now_kst_iso()

    return parsed.to_pydatetime().replace(tzinfo=None).isoformat(timespec="seconds")


def restore_users_from_excel(
    uploaded_file,
    temporary_password: str = "sg2026"
):
    """
    회원목록 엑셀을 읽어 Supabase users 테이블에 계정을 일괄 복구합니다.

    지원 열:
    - 학생
    - 학년
    - 임시비밀번호
    - 기존가입일시
    """
    df = pd.read_excel(uploaded_file)

    required_columns = {"학생", "학년"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "필수 열이 없습니다: " + ", ".join(sorted(missing_columns))
        )

    existing_rows = fetch_all_rows("users", "username")
    existing_names = {
        row.get("username", "")
        for row in existing_rows
        if row.get("username")
    }

    restore_rows: list[dict] = []
    created_count = 0
    updated_count = 0
    skipped_count = 0
    restored_names: list[str] = []

    for _, row in df.iterrows():
        username = str(row.get("학생", "")).strip()

        if not username or username.lower() == "nan":
            skipped_count += 1
            continue

        grade_value = row.get("학년", "미지정")
        grade = (
            "미지정"
            if pd.isna(grade_value) or str(grade_value).strip() == ""
            else str(grade_value).strip()
        )

        password_value = row.get("임시비밀번호", temporary_password)
        password = (
            temporary_password
            if pd.isna(password_value) or str(password_value).strip() == ""
            else str(password_value).strip()
        )

        created_at = normalize_excel_datetime(
            row.get("기존가입일시", "")
        )

        restore_rows.append(
            {
                "username": username,
                "password_hash": hash_pw(password),
                "grade": grade,
                "temp_password": password,
                "created_at": created_at
            }
        )

        if username in existing_names:
            updated_count += 1
        else:
            created_count += 1

        restored_names.append(username)

    if restore_rows:
        (
            supabase.table("users")
            .upsert(restore_rows, on_conflict="username")
            .execute()
        )

    return {
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "total": created_count + updated_count,
        "names": restored_names
    }


# ---------------------- 초기화 ----------------------
verify_supabase_connection()

try:
    cleanup_duplicate_wrong_answers()
except Exception as cleanup_error:
    st.warning(f"기존 중복 오답 정리 중 오류가 발생했습니다: {cleanup_error}")

apply_global_style()


# ---------------------- 세션 상태 ----------------------
if "role" not in st.session_state:
    st.session_state.role = None

if "student_user" not in st.session_state:
    st.session_state.student_user = None

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "teacher_name" not in st.session_state:
    st.session_state.teacher_name = None


if "is_superadmin" not in st.session_state:
    st.session_state.is_superadmin = False


# ---------------------- 시작 화면 ----------------------
def show_role_select():
    show_banner()
    show_account_notice()

    st.markdown(
        '<div class="sg-role-title">📝 SG 고등관 오답노트</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sg-role-subtitle">역할을 선택해주세요.</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        if st.button(
            "👩‍🎓 학생으로 입장\n(학생 계정 로그인)",
            use_container_width=True,
            key="enter_student"
        ):
            st.session_state.role = "student"
            st.rerun()

    with col2:
        if st.button(
            "👨‍🏫 선생님으로 입장\n(선생님 계정 로그인)",
            use_container_width=True,
            key="enter_teacher"
        ):
            st.session_state.role = "admin"
            st.rerun()

    st.write("")

    if st.button(
        "🔐 관리자로 입장\n(관리자 계정 로그인)",
        use_container_width=True,
        key="enter_superadmin"
    ):
        st.session_state.role = "superadmin"
        st.rerun()

    st.markdown(
        """
        <div class="sg-info-box">
            ℹ️ 관리자 기능은 학원 관리자만 이용 가능합니다.<br>
            ℹ️ 비밀번호를 분실한 경우 학원 관리자에게 문의해주세요.
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------- 학생 화면 ----------------------
def show_student():
    if st.session_state.student_user is None:
        show_banner()
        show_account_notice()

        st.title("👩‍🎓 학생 로그인")

        tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

        with tab_login:
            username = st.text_input("학생", key="login_id")
            password = st.text_input("비밀번호", type="password", key="login_pw")

            if st.button("로그인"):
                if check_user(username.strip(), password):
                    st.session_state.student_user = username.strip()
                    st.rerun()
                else:
                    st.error("학생 또는 비밀번호가 올바르지 않습니다.")

        with tab_signup:
            new_username = st.text_input("학생", key="signup_id")
            new_grade = st.selectbox("학년", GRADES, key="signup_grade")
            new_password = st.text_input("비밀번호", type="password", key="signup_pw")
            new_password2 = st.text_input("비밀번호 확인", type="password", key="signup_pw2")

            qr_code = get_qr_signup_code()
            qr_code_ok = (
                STUDENT_SIGNUP_CODE is not None
                and qr_code == STUDENT_SIGNUP_CODE
            )

            if qr_code_ok:
                st.success("SG 고등관 QR 접속이 확인되었습니다.")
                signup_code = qr_code
            else:
                signup_code = st.text_input(
                    "학원 가입 코드",
                    type="password",
                    key="signup_code",
                    placeholder="학원에서 안내받은 가입 코드를 입력하세요."
                )

            if st.button("회원가입"):
                if STUDENT_SIGNUP_CODE is None:
                    st.error("학원 가입 코드가 설정되지 않았습니다. 선생님께 문의해주세요.")
                elif signup_code != STUDENT_SIGNUP_CODE:
                    st.error("학원 가입 코드가 올바르지 않습니다.")
                elif not new_username.strip() or not new_password.strip():
                    st.warning("학생과 비밀번호를 입력해주세요.")
                elif new_password != new_password2:
                    st.warning("비밀번호가 일치하지 않습니다.")
                else:
                    signup_conflict = find_signup_name_conflict(
                        new_username.strip()
                    )

                    if signup_conflict:
                        matched_name = signup_conflict["matched_name"]
                        school_name = signup_conflict.get("school_name", "")
                        matched_text = (
                            f"{matched_name} ({school_name})"
                            if school_name
                            else matched_name
                        )

                        st.error(
                            "중복 이름 계정으로 가입을 시도했습니다. "
                            "관리자에게 오픈채팅으로 문의한 후 "
                            "임시 비밀번호를 안내받아주세요."
                        )
                        st.caption(
                            f"확인된 기존 이름 또는 계정: {matched_text}"
                        )
                    elif create_user(
                        new_username.strip(),
                        new_password,
                        new_grade,
                    ):
                        st.success(
                            "회원가입이 완료되었습니다. "
                            "로그인 탭에서 로그인해주세요."
                        )
                    else:
                        st.error(
                            "계정을 생성하지 못했습니다. "
                            "하단 오픈채팅으로 문의해주세요."
                        )

        st.divider()

        if st.button("← 처음으로"):
            st.session_state.role = None
            st.rerun()

    else:
        show_banner()

        st.title("📝 내 오답노트")
        st.write(f"환영합니다, **{st.session_state.student_user}**님!")

        st.divider()

        st.subheader("오답 작성")

        allowed_books = get_student_allowed_books(
            st.session_state.student_user
        )

        st.warning(
            "⚠️ 주의: 선택한 교재가 실제로 오답번호를 작성할 교재가 맞는지 "
            "반드시 확인해주세요. 잘못 선택하면 다른 교재의 오답 Paper에 반영될 수 있습니다."
        )

        book = st.selectbox(
            "교재 선택",
            allowed_books,
            help="관리자가 등록한 사용 중 교재 목록입니다."
        )

        st.info(f"현재 선택한 교재: **{book}**")

        problem_number = st.text_input(
            "문제 번호",
            placeholder="예: 032, 128, 45, 54, 65"
        )

        note = st.text_area(
            "비고",
            placeholder="예: 계산 실수, 개념 헷갈림, 다시 질문 필요, 변형문제 필요 등"
        )

        book_confirm = st.checkbox(
            f"'{book}' 교재가 맞는지 확인했습니다.",
            key="student_book_confirm",
        )

        if st.button("오답 저장"):
            if problem_number.strip() == "":
                st.warning("문제 번호를 입력해주세요.")
            elif not book_confirm:
                st.error("선택한 교재가 맞는지 확인한 후 체크해주세요.")
            else:
                result = add_wrong_answer(
                    st.session_state.student_user,
                    book,
                    problem_number.strip(),
                    note.strip()
                )

                if result["saved"]:
                    saved_text = ", ".join(result["new_numbers"])
                    st.success(f"새 문제번호 {saved_text}이(가) 저장되었습니다.")

                    if result["duplicate_numbers"]:
                        duplicate_text = ", ".join(result["duplicate_numbers"])
                        st.info(
                            f"이미 저장된 문제번호 {duplicate_text}은(는) "
                            "중복 저장하지 않았습니다."
                        )

                    st.rerun()
                else:
                    st.warning(result["message"])

                    if result.get("duplicate_numbers"):
                        duplicate_text = ", ".join(
                            result["duplicate_numbers"]
                        )
                        st.info(
                            f"중복 감지된 문제번호: {duplicate_text}\n\n"
                            "같은 학생·같은 교재에 이미 등록된 번호이므로 "
                            "추가 저장하지 않았습니다."
                        )

        st.divider()


        with st.expander("🏫 학교 기출 오답 작성", expanded=True):
            render_student_school_exam_wrong_answer()

        st.divider()

        with st.expander("🔐 비밀번호 변경", expanded=False):
            st.caption(
                "임시 비밀번호로 로그인한 경우 본인만 아는 새 비밀번호로 변경해주세요."
            )

            current_pw = st.text_input(
                "현재 비밀번호",
                type="password",
                key="student_current_pw"
            )

            new_pw1 = st.text_input(
                "새 비밀번호",
                type="password",
                key="student_new_pw1"
            )

            new_pw2 = st.text_input(
                "새 비밀번호 확인",
                type="password",
                key="student_new_pw2"
            )

            if st.button("내 비밀번호 변경", key="student_change_pw"):
                if not current_pw or not new_pw1 or not new_pw2:
                    st.warning("현재 비밀번호와 새 비밀번호를 모두 입력해주세요.")
                elif len(new_pw1) < 4:
                    st.warning("새 비밀번호는 4자 이상으로 설정해주세요.")
                elif new_pw1 != new_pw2:
                    st.warning("새 비밀번호가 서로 일치하지 않습니다.")
                elif change_my_password(
                    st.session_state.student_user,
                    current_pw,
                    new_pw1
                ):
                    st.success(
                        "비밀번호가 변경되었습니다. 다음 로그인부터 새 비밀번호를 사용해주세요."
                    )
                else:
                    st.error("현재 비밀번호가 올바르지 않습니다.")

        st.divider()

        st.subheader("내 오답 목록")

        df = get_my_wrong_answers(st.session_state.student_user)

        if df.empty:
            st.info("아직 기록된 오답이 없습니다.")
        else:
            book_filter = st.selectbox(
                "교재 필터",
                ["전체"] + BOOKS,
                key="my_book_filter"
            )

            if book_filter == "전체":
                display_df = df
            else:
                display_df = df[df["교재"] == book_filter]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

        st.divider()

        if st.button("로그아웃"):
            st.session_state.student_user = None
            st.session_state.role = None
            st.rerun()


# ---------------------- 선생님 관리 화면 ----------------------
def show_admin():
    if not st.session_state.is_admin:
        show_banner()
        show_account_notice()

        st.title("👨‍🏫 선생님 로그인")

        selected_teacher_login = st.selectbox(
            "담당 선생님",
            TEACHERS + [ALL_TEACHER_ADMIN],
            key="teacher_login_name"
        )

        pw = st.text_input(
            "선생님 공용 비밀번호",
            type="password",
            key="teacher_login_password"
        )

        if st.button("로그인", key="teacher_login_button"):
            if selected_teacher_login == ALL_TEACHER_ADMIN:
                if SUPERADMIN_PASSWORD is None:
                    st.error("전체 관리자 비밀번호가 설정되지 않았습니다.")
                elif pw == SUPERADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.session_state.teacher_name = ALL_TEACHER_ADMIN
                    st.rerun()
                else:
                    st.error("전체 관리자 비밀번호가 올바르지 않습니다.")
            else:
                if ADMIN_PASSWORD is None:
                    st.error("선생님 비밀번호가 설정되지 않았습니다.")
                elif pw == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.session_state.teacher_name = selected_teacher_login
                    st.rerun()
                else:
                    st.error("비밀번호가 틀렸습니다.")

        st.divider()

        if st.button("← 처음으로"):
            st.session_state.role = None
            st.rerun()

        return

    show_banner()
    st.title("👨‍🏫 선생님 관리")
    st.caption(f"현재 로그인: {st.session_state.teacher_name or '선생님 미지정'}")

    (
        tab_answers,
        tab_weekly_submission,
        tab_weekly_missing,
        tab_signup_status,
        tab_teacher_students,
        tab_paper,
        tab_school_exam,
        tab_print,
    ) = st.tabs(
        [
            "📋 전체 오답 현황",
            "📅 주간 제출 현황",
            "🚨 미제출 학생 보기",
            "👤 가입 현황",
            "🏫 내 반 학생",
            "🧾 오답노트 만들기",
            "🏫 학교 기출 오답",
            "🖨️ 출력 관리",
        ]
    )

    with tab_answers:
        df = get_all_wrong_answers()
        roster = get_roster_df()
        current_teacher = st.session_state.teacher_name

        if not current_teacher:
            st.warning("로그인한 선생님 정보가 없습니다. 로그아웃 후 다시 로그인해주세요.")
            df = pd.DataFrame()
        elif current_teacher == ALL_TEACHER_ADMIN:
            # 전체 관리자는 모든 학생의 오답 기록을 확인합니다.
            df = merge_wrong_answers_by_day(df)
        elif roster.empty:
            st.info("등록된 학생 명단이 없습니다.")
            df = pd.DataFrame()
        else:
            teacher_roster = roster[
                roster["담당선생님"] == current_teacher
            ][["학생명", "매칭교재"]].drop_duplicates()

            # 같은 이름의 다른 학생 또는 다른 교재 기록이 섞이지 않도록
            # 학생명 + 교재를 함께 기준으로 로그인한 선생님의 기록만 표시합니다.
            df = df.merge(
                teacher_roster,
                left_on=["학생", "교재"],
                right_on=["학생명", "매칭교재"],
                how="inner"
            ).drop(columns=["학생명", "매칭교재"])

            # 같은 학생이 같은 날 같은 교재에 여러 번 입력한 기록은 한 줄로 통합합니다.
            df = merge_wrong_answers_by_day(df)

        if df.empty:
            st.info(f"{current_teacher or '해당 선생님'} 담당 학생의 오답 기록이 없습니다.")
        else:
            df["학년"] = df["학년"].fillna("미지정")

            col1, col2, col3 = st.columns(3)

            with col1:
                student_filter = st.selectbox(
                    "학생 필터",
                    ["전체"] + sorted(df["학생"].unique().tolist()),
                    key="answer_student_filter",
                )

            with col2:
                grade_filter = st.selectbox(
                    "학년 필터",
                    ["전체"] + sorted(df["학년"].unique().tolist()),
                    key="answer_grade_filter",
                )

            with col3:
                book_filter = st.selectbox(
                    "교재 필터",
                    ["전체"] + BOOKS,
                    key="answer_book_filter",
                )

            display_df = df.copy()

            if student_filter != "전체":
                display_df = display_df[display_df["학생"] == student_filter]
            if grade_filter != "전체":
                display_df = display_df[display_df["학년"] == grade_filter]
            if book_filter != "전체":
                display_df = display_df[display_df["교재"] == book_filter]

            if current_teacher == ALL_TEACHER_ADMIN:
                st.caption(
                    "전체 학생의 오답 기록이 표시되며, "
                    "같은 날짜·교재의 입력은 한 줄로 합쳐집니다."
                )
            else:
                st.caption(
                    f"{current_teacher} 담당 학생의 기록만 표시되며, "
                    "같은 날짜·교재의 입력은 한 줄로 합쳐집니다."
                )
            st.write(f"총 {len(display_df)}건")
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=520
            )

            st.download_button(
                "엑셀로 다운로드",
                data=dataframe_to_excel_bytes(display_df),
                file_name=("전체관리자_전체오답현황.xlsx" if current_teacher == ALL_TEACHER_ADMIN else f"{current_teacher}_전체오답현황.xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_all_answers",
            )

            with st.expander("🧩 변형문제 필요 학생", expanded=False):
                variant_df = display_df[
                    display_df["비고"].fillna("").str.contains(
                        "변형", case=False, na=False, regex=False
                    )
                ].copy()

                if variant_df.empty:
                    st.info("비고에 '변형'이 포함된 기록이 없습니다.")
                else:
                    st.dataframe(
                        variant_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    st.download_button(
                        "변형문제 필요 학생 엑셀 다운로드",
                        data=dataframe_to_excel_bytes(variant_df),
                        file_name="변형문제_필요학생.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_variant_students",
                    )


    with tab_weekly_submission:
        render_weekly_submission_status()

    with tab_weekly_missing:
        render_weekly_missing_students()

    with tab_signup_status:
        render_student_signup_status()

    with tab_teacher_students:
        status_df = get_teacher_student_status_df()
        current_teacher = st.session_state.teacher_name

        if not current_teacher:
            st.warning("로그인한 선생님 정보가 없습니다. 로그아웃 후 다시 로그인해주세요.")
        elif status_df.empty:
            st.info(
                "등록된 학생 명단이 없습니다. 관리자 화면에서 최종 명단 엑셀을 먼저 업로드해주세요."
            )
        else:
            if current_teacher == ALL_TEACHER_ADMIN:
                teacher_df = status_df.copy()
                section_title = "전체 선생님 담당 반"
            else:
                teacher_df = status_df[
                    status_df["담당선생님"] == current_teacher
                ].copy()
                section_title = f"{current_teacher} 담당 반"

            if teacher_df.empty:
                st.info("등록된 반 또는 학생이 없습니다.")
            else:
                st.markdown(f"### {section_title}")
                st.caption("반 이름을 눌러 각 반의 학생 현황을 따로 확인할 수 있습니다.")

                if current_teacher == ALL_TEACHER_ADMIN:
                    teacher_df["관리용반명"] = (
                        teacher_df["담당선생님"].astype(str)
                        + " · "
                        + teacher_df["반명"].astype(str)
                    )
                    class_names = sorted(
                        teacher_df["관리용반명"].dropna().unique().tolist()
                    )
                else:
                    teacher_df["관리용반명"] = teacher_df["반명"].astype(str)
                    class_names = sorted(
                        teacher_df["관리용반명"].dropna().unique().tolist()
                    )

                tab_labels = ["전체"] + class_names
                class_tabs = st.tabs(tab_labels)

                def render_class_status(
                    class_df: pd.DataFrame,
                    tab_name: str,
                    tab_index: int
                ):
                    unique_students = class_df["학생명"].nunique()
                    completed_students = class_df.loc[
                        class_df["작성여부"] == "O", "학생명"
                    ].nunique()
                    incomplete_students = max(
                        unique_students - completed_students,
                        0
                    )

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("고유 학생", unique_students)
                    col2.metric("수강 등록", len(class_df))
                    col3.metric("작성 학생", completed_students)
                    col4.metric("미작성 학생", incomplete_students)

                    display_columns = [
                        "반명", "학생명", "학교명", "학년",
                        "매칭교재", "작성여부", "작성문제수", "최근작성일시"
                    ]

                    st.dataframe(
                        class_df[display_columns],
                        use_container_width=True,
                        hide_index=True,
                        height=520,
                    )

                    safe_tab_name = re.sub(
                        r"[^0-9A-Za-z가-힣_-]+",
                        "_",
                        tab_name
                    )

                    st.download_button(
                        f"{tab_name} 학생 현황 엑셀 다운로드",
                        data=dataframe_to_excel_bytes(class_df),
                        file_name=(
                            f"{current_teacher}_{safe_tab_name}_학생현황.xlsx"
                        ),
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                        key=f"download_class_status_{tab_index}",
                    )

                for tab_index, (tab, tab_name) in enumerate(
                    zip(class_tabs, tab_labels)
                ):
                    with tab:
                        if tab_name == "전체":
                            tab_df = teacher_df.copy()
                        else:
                            tab_df = teacher_df[
                                teacher_df["관리용반명"] == tab_name
                            ].copy()

                        render_class_status(
                            tab_df,
                            tab_name,
                            tab_index
                        )

    with tab_paper:
        roster = get_roster_df()

        if roster.empty:
            st.info(
                "등록된 학생 명단이 없습니다. 관리자 화면에서 명단 엑셀을 먼저 업로드해주세요."
            )
        else:
            current_teacher = st.session_state.teacher_name

            if current_teacher == ALL_TEACHER_ADMIN:
                teacher_options = sorted(
                    roster["담당선생님"].dropna().astype(str).unique().tolist()
                )
                selected_teacher = st.selectbox(
                    "1. 담당 선생님",
                    teacher_options,
                    key="paper_admin_teacher",
                )
                teacher_roster = roster[
                    roster["담당선생님"] == selected_teacher
                ].copy()
            else:
                teacher_roster = roster[
                    roster["담당선생님"] == current_teacher
                ].copy()
                selected_teacher = current_teacher
                st.markdown(f"**담당 선생님:** {selected_teacher}")

            class_options = sorted(
                teacher_roster["반명"].dropna().unique().tolist()
            )

            selected_class = st.selectbox(
                "2. 반 선택",
                class_options,
                key="paper_class",
            )

            class_roster = teacher_roster[
                teacher_roster["반명"] == selected_class
            ].copy()

            student_options = sorted(
                class_roster["학생명"].dropna().unique().tolist()
            )

            selected_students = st.multiselect(
                "3. 오답노트를 만들 학생",
                student_options,
                default=student_options,
                key="paper_students",
            )

            col_month, col_week = st.columns(2)

            with col_month:
                month = st.selectbox(
                    "5. 월",
                    list(range(1, 13)),
                    index=datetime.now(KST).month - 1,
                    key="paper_month",
                )

            with col_week:
                week = st.selectbox(
                    "6. 주차",
                    [1, 2, 3, 4, 5],
                    index=min((datetime.now(KST).day - 1) // 7, 4),
                    key="paper_week",
                )

            if not class_roster.empty:
                sample = class_roster.iloc[0]
                title_preview = build_paper_title(
                    selected_teacher,
                    selected_class,
                    sample["학년"],
                    selected_book,
                    month,
                    week,
                )

                st.markdown("#### PDF 상단 제목 미리보기")
                st.code(title_preview, language="text")
                st.caption(
                    "기존의 ‘이주백T 고1 미적분1 오답 Paper’ 부분을 "
                    "선생님·반·교재 정보에 맞춰 자동 생성합니다."
                )

            if selected_students:
                export_df = build_claude_export_df(
                    selected_teacher,
                    selected_class,
                    selected_students,
                    selected_book,
                    month,
                    week,
                )

                st.dataframe(
                    export_df,
                    use_container_width=True,
                    hide_index=True,
                )

                if "print_auto_register_error" in st.session_state:
                    st.error(
                        "최근 출력 목록 자동 등록 중 오류가 발생했습니다: "
                        f"{st.session_state.pop('print_auto_register_error')}"
                    )

                if "print_auto_register_result" in st.session_state:
                    auto_result = st.session_state.pop(
                        "print_auto_register_result"
                    )
                    created_count = auto_result["created_count"]

                    if created_count:
                        st.success(
                            f"선택한 학생 중 {created_count}건을 "
                            "출력 관리의 미출력 목록에 자동 등록했습니다."
                        )
                    else:
                        st.info(
                            "선택한 학생은 이미 해당 월·주차의 "
                            "출력 관리 목록에 등록되어 있습니다."
                        )

                st.download_button(
                    "Claude Code 자동생성용 엑셀 다운로드",
                    data=dataframe_to_excel_bytes(export_df),
                    file_name=(
                        f"{selected_teacher}_{selected_class}_"
                        f"{month}월_{week}주차_오답노트생성.xlsx"
                    ),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_claude_export",
                    type="primary",
                    on_click=register_print_queue_on_download,
                    args=(
                        selected_teacher,
                        selected_class,
                        selected_students,
                        selected_book,
                        month,
                        week,
                    ),
                    help=(
                        "다운로드와 동시에 선택 학생을 출력 관리의 "
                        "미출력 목록에 자동 등록합니다."
                    ),
                )

                st.caption(
                    "이 버튼을 누르면 엑셀 다운로드와 동시에 선택 학생이 "
                    "출력 관리 탭의 미출력 목록에 자동 등록됩니다."
                )
            else:
                st.warning("오답노트를 만들 학생을 한 명 이상 선택해주세요.")

    with tab_school_exam:
        render_teacher_school_exam_management()

    with tab_print:
        render_print_management()

    st.divider()

    with st.expander("🔑 담당 학생 비밀번호 초기화", expanded=False):
        current_teacher = st.session_state.teacher_name
        roster_df = get_roster_df()
        users_df = get_all_users()

        if users_df.empty:
            st.info("초기화할 학생 계정이 없습니다.")
        else:
            if current_teacher == ALL_TEACHER_ADMIN:
                allowed_students = sorted(
                    users_df["학생"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )
                st.caption(
                    "전체 관리자는 가입된 모든 학생의 비밀번호를 초기화할 수 있습니다."
                )
            else:
                if roster_df.empty:
                    allowed_students = []
                else:
                    teacher_student_names = set(
                        roster_df.loc[
                            roster_df["담당선생님"] == current_teacher,
                            "학생명",
                        ]
                        .dropna()
                        .astype(str)
                        .tolist()
                    )

                    allowed_students = sorted(
                        users_df.loc[
                            users_df["학생"].isin(teacher_student_names),
                            "학생",
                        ]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                st.caption(
                    f"{current_teacher} 선생님의 담당 학생 계정만 표시됩니다."
                )

            if not allowed_students:
                st.info("현재 비밀번호를 초기화할 수 있는 담당 학생 계정이 없습니다.")
            else:
                selected_reset_student = st.selectbox(
                    "학생 선택",
                    allowed_students,
                    key="teacher_reset_password_student",
                )

                new_reset_password = st.text_input(
                    "새 임시 비밀번호",
                    type="password",
                    placeholder="4자 이상 입력",
                    key="teacher_reset_password_new",
                )

                confirm_reset_password = st.text_input(
                    "새 임시 비밀번호 확인",
                    type="password",
                    placeholder="동일한 비밀번호를 다시 입력",
                    key="teacher_reset_password_confirm",
                )

                reset_password_check = st.checkbox(
                    f"{selected_reset_student} 학생의 기존 비밀번호를 초기화합니다.",
                    key="teacher_reset_password_check",
                )

                if st.button(
                    "담당 학생 비밀번호 초기화",
                    type="primary",
                    key="teacher_reset_password_button",
                    use_container_width=True,
                ):
                    if len(new_reset_password.strip()) < 4:
                        st.warning("새 임시 비밀번호는 4자 이상 입력해주세요.")
                    elif new_reset_password != confirm_reset_password:
                        st.warning("새 임시 비밀번호가 서로 일치하지 않습니다.")
                    elif not reset_password_check:
                        st.warning("비밀번호 초기화 확인 항목에 체크해주세요.")
                    else:
                        try:
                            reset_user_password(
                                selected_reset_student,
                                new_reset_password.strip(),
                            )
                            st.success(
                                f"{selected_reset_student} 학생의 비밀번호를 "
                                "새 임시 비밀번호로 초기화했습니다."
                            )
                            st.rerun()
                        except Exception as error:
                            st.error(
                                f"비밀번호 초기화 중 오류가 발생했습니다: {error}"
                            )

    st.divider()

    if st.button("로그아웃", key="teacher_logout"):
        st.session_state.is_admin = False
        st.session_state.teacher_name = None
        st.session_state.role = None
        st.rerun()


# ---------------------- 별도 관리자 화면 ----------------------
def show_superadmin():
    if not st.session_state.is_superadmin:
        show_banner()
        show_account_notice()

        st.title("🔐 관리자 로그인")
        st.caption("학생 계정, 비밀번호 및 회원 복구 전용 화면입니다.")

        admin_pw = st.text_input(
            "관리자 비밀번호",
            type="password",
            key="superadmin_login_password"
        )

        if st.button("관리자 로그인", key="superadmin_login_button"):
            if SUPERADMIN_PASSWORD is None:
                st.error("관리자 비밀번호가 설정되지 않았습니다.")
            elif admin_pw == SUPERADMIN_PASSWORD:
                st.session_state.is_superadmin = True
                st.rerun()
            else:
                st.error("관리자 비밀번호가 올바르지 않습니다.")

        st.divider()

        if st.button("← 처음으로", key="superadmin_back"):
            st.session_state.role = None
            st.rerun()

    else:
        show_banner()

        st.title("🔐 관리자 전용")
        st.caption("학생 계정 복구, 비밀번호 확인·초기화 및 회원 관리를 진행할 수 있습니다.")

        st.divider()

        with st.expander("📚 학생 명단·반·교재 등록", expanded=True):
            st.info(
                "최종 명단 엑셀을 업로드하면 담당 선생님·반·학생·교재 정보가 "
                "Supabase에 저장됩니다. 학생 화면에는 담당 선생님 정보가 표시되지 않습니다."
            )

            roster_file = st.file_uploader(
                "최종 명단 엑셀 업로드",
                type=["xlsx"],
                key="roster_excel_upload",
            )

            roster_confirm = st.checkbox(
                "기존 명단을 업로드한 최신 명단으로 교체합니다.",
                key="roster_replace_confirm",
            )

            if st.button(
                "학생 명단 반영",
                type="primary",
                key="import_roster_button",
            ):
                if roster_file is None:
                    st.warning("최종 명단 엑셀을 업로드해주세요.")
                elif not roster_confirm:
                    st.warning("명단 교체 확인 항목에 체크해주세요.")
                else:
                    try:
                        result = import_roster_from_excel(roster_file)
                        st.success(
                            f"명단 {result['count']}건을 저장했습니다. "
                            f"선생님 {len(result['teachers'])}명, "
                            f"반 {len(result['classes'])}개가 반영되었습니다."
                        )
                        st.rerun()
                    except Exception as error:
                        st.error(f"명단 반영 중 오류가 발생했습니다: {error}")

            roster_df = get_roster_df()

            if not roster_df.empty:
                st.dataframe(
                    roster_df[
                        [
                            "반명", "담당선생님", "학생명",
                            "학교명", "학년", "매칭교재"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "현재 명단 엑셀 다운로드",
                    data=dataframe_to_excel_bytes(roster_df),
                    file_name="현재_학생명단.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_current_roster",
                )

        st.divider()

        with st.expander("📚 교재 관리", expanded=False):
            render_book_admin()

        st.divider()

        with st.expander("🏫 학교 기출 관리", expanded=False):
            render_school_exam_admin()

        st.divider()

        with st.expander("👥 회원 관리", expanded=False):
            st.subheader("📥 회원목록 일괄 복구")

            st.info(
                "회원목록 엑셀을 업로드하면 학생 계정을 한꺼번에 복구합니다. "
                "기존 계정이 있으면 삭제하지 않고 학년과 비밀번호만 갱신합니다."
            )

            restore_file = st.file_uploader(
                "회원목록 복구용 엑셀 업로드",
                type=["xlsx"],
                key="restore_users_excel"
            )

            restore_password = st.text_input(
                "기본 임시 비밀번호",
                value="sg2026",
                key="restore_default_password"
            )

            restore_confirm = st.checkbox(
                "학생 계정을 복구하고 임시 비밀번호를 적용하는 것에 동의합니다.",
                key="restore_confirm"
            )

            if st.button("회원 계정 일괄 복구", type="primary"):
                if restore_file is None:
                    st.warning("회원목록 엑셀 파일을 업로드해주세요.")
                elif not restore_password.strip():
                    st.warning("임시 비밀번호를 입력해주세요.")
                elif not restore_confirm:
                    st.warning("복구 확인 항목에 체크해주세요.")
                else:
                    try:
                        result = restore_users_from_excel(
                            restore_file,
                            restore_password.strip()
                        )

                        st.session_state["last_restore_result"] = result
                        st.rerun()

                    except Exception as e:
                        st.error(f"회원 복구 중 오류가 발생했습니다: {e}")

            if "last_restore_result" in st.session_state:
                result = st.session_state["last_restore_result"]

                st.success(
                    f"최근 복구 결과: 총 {result['total']}명 처리 "
                    f"(신규 {result['created']}명 / "
                    f"갱신 {result['updated']}명 / "
                    f"건너뜀 {result['skipped']}명)"
                )

                with st.expander("최근 복구 학생 이름 보기"):
                    for name in result["names"]:
                        st.write(f"- {name}")

                if st.button("최근 복구 결과 닫기"):
                    del st.session_state["last_restore_result"]
                    st.rerun()

            st.divider()

            st.subheader("🔐 학생 임시 비밀번호 현황")

            st.warning(
                "관리자는 복구·초기화 때 설정한 임시 비밀번호만 확인할 수 있습니다. "
                "학생이 직접 변경한 새 비밀번호는 보안상 확인할 수 없습니다."
            )

            password_status_df = get_admin_password_status()

            if password_status_df.empty:
                st.info("확인할 학생 계정이 없습니다.")
            else:
                st.dataframe(
                    password_status_df,
                    use_container_width=True,
                    hide_index=True
                )

                password_excel = dataframe_to_excel_bytes(password_status_df)

                st.download_button(
                    "임시 비밀번호 현황 엑셀 다운로드",
                    data=password_excel,
                    file_name="학생_임시비밀번호_현황.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.divider()

            with st.expander("🔑 학생 비밀번호 초기화", expanded=False):
                st.caption(
                    "관리자가 선택한 학생의 비밀번호를 새 임시 비밀번호로 변경합니다."
                )

                reset_users_df = get_all_users()

                if reset_users_df.empty:
                    st.info("비밀번호를 초기화할 학생 계정이 없습니다.")
                else:
                    reset_user_options = sorted(
                        reset_users_df["학생"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                    selected_reset_user = st.selectbox(
                        "학생 선택",
                        reset_user_options,
                        key="admin_reset_password_user",
                    )

                    new_temp_password = st.text_input(
                        "새 임시 비밀번호",
                        type="password",
                        placeholder="4자 이상 입력",
                        key="admin_reset_password_new",
                    )

                    confirm_temp_password = st.text_input(
                        "새 임시 비밀번호 확인",
                        type="password",
                        placeholder="같은 비밀번호를 다시 입력",
                        key="admin_reset_password_confirm",
                    )

                    reset_confirm = st.checkbox(
                        f"{selected_reset_user} 학생의 기존 비밀번호를 초기화합니다.",
                        key="admin_reset_password_confirm_check",
                    )

                    if st.button(
                        "비밀번호 초기화",
                        type="primary",
                        key="admin_reset_password_button",
                        use_container_width=True,
                    ):
                        if len(new_temp_password.strip()) < 4:
                            st.warning("새 임시 비밀번호는 4자 이상 입력해주세요.")
                        elif new_temp_password != confirm_temp_password:
                            st.warning("새 임시 비밀번호가 서로 일치하지 않습니다.")
                        elif not reset_confirm:
                            st.warning("비밀번호 초기화 확인 항목에 체크해주세요.")
                        else:
                            try:
                                reset_user_password(
                                    selected_reset_user,
                                    new_temp_password.strip(),
                                )
                                st.success(
                                    f"{selected_reset_user} 학생의 비밀번호를 "
                                    "새 임시 비밀번호로 초기화했습니다."
                                )
                                st.rerun()
                            except Exception as error:
                                st.error(
                                    f"비밀번호 초기화 중 오류가 발생했습니다: {error}"
                                )

            st.divider()

            users_df = get_all_users()

            if users_df.empty:
                st.info("가입된 학생이 없습니다.")
            else:
                users_df["학년"] = users_df["학년"].fillna("미지정")

                st.write(f"가입 학생 수: **{len(users_df)}명**")

                st.dataframe(
                    users_df,
                    use_container_width=True,
                    hide_index=True
                )

                users_excel = dataframe_to_excel_bytes(users_df)

                st.download_button(
                    "회원 목록 엑셀 다운로드",
                    data=users_excel,
                    file_name="회원목록.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.divider()




        st.divider()

        with st.expander("🧑‍🎓 학생 통합 관리", expanded=False):
            st.info(
                "학생 이름, 담당 선생님, 반, 학교, 학년, 교재를 수정하거나 "
                "학생 계정·명단·오답 기록을 삭제할 수 있습니다."
            )
            render_student_management()

        st.divider()

        with st.expander("✏️ 오답 기록 교재 수정", expanded=False):
            st.info("학생이 잘못 선택한 교재를 수정할 수 있습니다.")
            render_wrong_answer_book_editor("superadmin")

        st.divider()

        if st.button("관리자 로그아웃", key="superadmin_logout"):
            st.session_state.is_superadmin = False
            st.session_state.role = None
            st.rerun()


# ---------------------- 라우팅 ----------------------
if st.session_state.role is None:
    show_role_select()
elif st.session_state.role == "student":
    show_student()
elif st.session_state.role == "admin":
    show_admin()

elif st.session_state.role == "superadmin":
    show_superadmin()

# 모든 화면에 하단 고정 안내 표시
show_global_footer()
