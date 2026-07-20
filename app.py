import io
import re
import hashlib
from collections import Counter
from datetime import datetime
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
    SUPERADMIN_PASSWORD = "TY2003!!"



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
            padding-bottom: 3rem;
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

        .sg-footer {
            margin-top: 2rem;
            padding-top: 1.2rem;
            border-top: 1px solid #e7ebf0;
            text-align: center;
            color: #8791a2;
            font-size: 14px;
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
    if BANNER_PATH.exists():
        st.image(str(BANNER_PATH), width=280)

    banner_html = """
<div class="sg-notice-card">
<div class="sg-notice-title">
<span>📣</span>
<span>계정 복구 안내</span>
</div>

<div class="sg-notice-intro">
학생 계정 복구는 완료되었습니다.<br>
기존에 사용하던 학생 이름과 아래 임시 비밀번호로 로그인해주세요.
</div>

<div class="sg-temp-password">
<span class="sg-lock">🔐</span>
<span class="sg-temp-label">임시 비밀번호</span>
<span class="sg-temp-value">sg2026</span>
</div>

<div class="sg-action-box">
<div class="sg-action-title">로그인 후 꼭 진행해주세요</div>

<div class="sg-action-item">
<span class="sg-action-number">1</span>
<span>임시 비밀번호를 <strong>본인이 사용할 새 비밀번호로 변경</strong></span>
</div>

<div class="sg-action-item">
<span class="sg-action-number">2</span>
<span>주말에 작성했던 <strong>기존 오답번호를 다시 입력</strong></span>
</div>
</div>

<div class="sg-notice-foot">
현재 기존 오답번호 목록은 초기화된 상태입니다.<br>
본인이 작성했던 개수만큼 빠짐없이 다시 입력해주시기 바랍니다.<br>
이용에 불편을 드려 죄송합니다.
</div>

<div class="sg-signature">- SG 고등관 조교 -</div>
</div>
""".strip()

    st.html(banner_html)


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


# ---------------------- 비밀번호 처리 ----------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


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


if "is_superadmin" not in st.session_state:
    st.session_state.is_superadmin = False


# ---------------------- 시작 화면 ----------------------
def show_role_select():
    show_banner()

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
        <div class="sg-footer">
            Made by techtechchu
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------- 학생 화면 ----------------------
def show_student():
    if st.session_state.student_user is None:
        show_banner()

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
                elif create_user(new_username.strip(), new_password, new_grade):
                    st.success("회원가입이 완료되었습니다. 로그인 탭에서 로그인해주세요.")
                else:
                    st.error("이미 존재하는 학생입니다.")

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

        book = st.selectbox("교재 선택", BOOKS)

        problem_number = st.text_input(
            "문제 번호",
            placeholder="예: 032, 128, 45, 54, 65"
        )

        note = st.text_area(
            "비고",
            placeholder="예: 계산 실수, 개념 헷갈림, 다시 질문 필요, 변형문제 필요 등"
        )

        if st.button("오답 저장"):
            if problem_number.strip() == "":
                st.warning("문제 번호를 입력해주세요.")
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


# ---------------------- 관리자 화면 ----------------------
def show_admin():
    if not st.session_state.is_admin:
        show_banner()

        st.title("👨‍🏫 선생님 로그인")

        pw = st.text_input("관리자 비밀번호", type="password")

        if st.button("로그인"):
            if ADMIN_PASSWORD is None:
                st.error("관리자 비밀번호가 설정되지 않았습니다.")
            elif pw == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")

        st.divider()

        if st.button("← 처음으로"):
            st.session_state.role = None
            st.rerun()

    else:
        show_banner()

        st.title("📋 전체 오답 현황")

        df = get_all_wrong_answers()

        if df.empty:
            st.info("아직 기록된 오답이 없습니다.")
        else:
            df["학년"] = df["학년"].fillna("미지정")

            col1, col2, col3 = st.columns(3)

            with col1:
                student_filter = st.selectbox(
                    "학생 필터",
                    ["전체"] + sorted(df["학생"].unique().tolist())
                )

            with col2:
                grade_filter = st.selectbox(
                    "학년 필터",
                    ["전체"] + sorted(df["학년"].unique().tolist())
                )

            with col3:
                book_filter = st.selectbox(
                    "교재 필터",
                    ["전체"] + BOOKS
                )

            display_df = df.copy()

            if student_filter != "전체":
                display_df = display_df[display_df["학생"] == student_filter]

            if grade_filter != "전체":
                display_df = display_df[display_df["학년"] == grade_filter]

            if book_filter != "전체":
                display_df = display_df[display_df["교재"] == book_filter]

            st.write(f"총 {len(display_df)}건")

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            excel_data = dataframe_to_excel_bytes(display_df)

            st.download_button(
                "엑셀로 다운로드",
                data=excel_data,
                file_name="오답노트.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.divider()

            with st.expander("🧩 변형문제 필요 학생", expanded=False):
                variant_df = display_df[
                    display_df["비고"].fillna("").str.contains(
                        "변형",
                        case=False,
                        na=False,
                        regex=False
                    )
                ].copy()

                if variant_df.empty:
                    st.info("현재 필터 기준에서 비고에 '변형'이 포함된 기록이 없습니다.")
                else:
                    st.write(f"변형문제 필요 기록: **{len(variant_df)}건**")

                    st.dataframe(
                        variant_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    variant_excel = dataframe_to_excel_bytes(variant_df)

                    st.download_button(
                        "변형문제 필요 학생 엑셀 다운로드",
                        data=variant_excel,
                        file_name="변형문제_필요학생.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        st.divider()

        st.caption("학생 계정 및 비밀번호 관리는 아래의 별도 관리자 화면에서 진행합니다.")

        st.divider()

        if st.button("로그아웃"):
            st.session_state.is_admin = False
            st.session_state.role = None
            st.rerun()


# ---------------------- 별도 관리자 화면 ----------------------
def show_superadmin():
    if not st.session_state.is_superadmin:
        show_banner()

        st.title("🔐 관리자 로그인")
        st.caption("학생 계정, 비밀번호 및 회원 복구 전용 화면입니다.")

        admin_pw = st.text_input(
            "관리자 비밀번호",
            type="password",
            key="superadmin_login_password"
        )

        if st.button("관리자 로그인", key="superadmin_login_button"):
            if admin_pw == SUPERADMIN_PASSWORD:
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

                st.subheader("🏫 학생 학년 수정")

                grade_student = st.selectbox(
                    "학년을 수정할 학생",
                    users_df["학생"].tolist(),
                    key="grade_student"
                )

                current_grade_values = users_df.loc[
                    users_df["학생"] == grade_student,
                    "학년"
                ].tolist()

                current_grade = current_grade_values[0] if current_grade_values else "미지정"

                grade_options = ["미지정"] + GRADES

                if current_grade in grade_options:
                    current_index = grade_options.index(current_grade)
                else:
                    current_index = 0

                new_grade = st.selectbox(
                    "새 학년",
                    grade_options,
                    index=current_index,
                    key="new_grade"
                )

                if st.button("학년 수정"):
                    update_user_grade(grade_student, new_grade)
                    st.success(f"{grade_student} 학생의 학년이 {new_grade}(으)로 변경되었습니다.")
                    st.rerun()

                st.divider()

                st.subheader("🔑 학생 비밀번호 초기화")

                reset_student = st.selectbox(
                    "비밀번호를 초기화할 학생",
                    users_df["학생"].tolist(),
                    key="reset_student"
                )

                new_pw = st.text_input(
                    "새 비밀번호",
                    type="password",
                    key="new_student_password",
                    placeholder="새 비밀번호를 입력하세요."
                )

                if st.button("비밀번호 초기화"):
                    if not new_pw.strip():
                        st.warning("새 비밀번호를 입력해주세요.")
                    else:
                        reset_user_password(reset_student, new_pw.strip())
                        st.success(f"{reset_student} 학생의 비밀번호가 변경되었습니다.")

                st.divider()

                st.subheader("🗑️ 학생 계정 삭제")

                delete_student = st.selectbox(
                    "삭제할 학생",
                    users_df["학생"].tolist(),
                    key="delete_student"
                )

                delete_answers_too = st.checkbox(
                    "계정 삭제 시 해당 학생의 오답 기록도 함께 삭제됩니다.",
                    value=True,
                    disabled=True
                )

                confirm_delete = st.text_input(
                    "삭제하려면 학생 이름을 그대로 입력하세요.",
                    key="confirm_delete_student"
                )

                if st.button("학생 삭제"):
                    if confirm_delete != delete_student:
                        st.warning("학생 이름이 일치하지 않습니다.")
                    else:
                        delete_user(delete_student, delete_answers_too)
                        st.success(f"{delete_student} 학생 계정이 삭제되었습니다.")
                        st.rerun()


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
