import io
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# ---------------------- 기본 설정 ----------------------
st.set_page_config(
    page_title="SG 고등관 오답노트",
    page_icon="📝",
    layout="centered"
)

DB_PATH = "wrong_answers.db"
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
        </style>
        """,
        unsafe_allow_html=True
    )


# ---------------------- 배너 ----------------------
def show_banner():
    if BANNER_PATH.exists():
        st.image(str(BANNER_PATH), width=330)

    banner_html = """
    <div style="
        box-sizing:border-box;
        width:100%;
        margin:18px 0 26px 0;
        padding:28px 30px;
        border:1px solid #ead5cf;
        border-left:6px solid #a62c20;
        border-radius:16px;
        background:linear-gradient(135deg,#fffdfa 0%,#fff7f3 100%);
        color:#252b35;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;
        line-height:1.78;
        box-shadow:0 10px 28px rgba(87,49,38,0.08);
    ">
        <div style="display:flex; align-items:center; gap:10px; font-size:24px; font-weight:900; color:#8f241b; margin-bottom:18px; letter-spacing:-0.6px;">
            <span>📣</span><span>시스템 점검 및 계정 복구 안내</span>
        </div>

        <div style="font-size:16px; word-break:keep-all;">
            현재 SG 고등관 오답노트 앱의 안정적인 운영을 위해 시스템 점검과 데이터 백업 기능 개선 작업을 진행하고 있습니다.
            기존 계정 백업 과정에서 일부 데이터가 초기화되는 문제가 발생하여 학생 계정 복구를 완료하였습니다.
        </div>

        <div style="display:flex; align-items:center; gap:14px; margin:20px 0 22px 0; padding:15px 18px; border-radius:12px; background:#ffffff; border:1px solid #ead8d2;">
            <span style="font-size:22px;">🔐</span>
            <span style="font-size:16px; font-weight:800; color:#364152;">임시 비밀번호</span>
            <span style="padding:5px 12px; border-radius:9px; background:#fff0e8; color:#b3261e; font-size:21px; font-weight:900; letter-spacing:0.4px;">sg2026</span>
        </div>

        <div style="border-top:1px dashed #dfd8d3; padding-top:18px; margin-top:4px;">
            <div style="font-size:18px; font-weight:850; color:#174b87; margin-bottom:6px;">👤 로그인 안내</div>
            <div style="font-size:16px; word-break:keep-all;">
                기존에 사용하던 학생 이름과 위 임시 비밀번호로 로그인해주세요.
                로그인 후에는 <b style="color:#174b87;">주말에 작성했던 오답번호를 본인의 기존 작성 개수만큼 다시 입력</b>해주시기 바랍니다.
            </div>
        </div>

        <div style="border-top:1px dashed #dfd8d3; padding-top:18px; margin-top:18px;">
            <div style="font-size:18px; font-weight:850; color:#18713b; margin-bottom:6px;">🛡️ 계정 복구 및 비밀번호 변경 안내</div>
            <div style="font-size:16px; word-break:keep-all;">
                계정 복구는 완료되었으나 현재 오답번호 목록은 모두 초기화된 상태입니다.
                로그인 후에는 안전한 사용을 위해 <b style="color:#18713b;">임시 비밀번호를 본인이 사용할 비밀번호로 변경</b>해주시고,
                주말에 작성했던 <b style="color:#18713b;">기존 오답노트 번호도 본인의 기존 작성 개수만큼 다시 입력</b>해주시기 바랍니다.
            </div>
        </div>

        <div style="border-top:1px dashed #dfd8d3; padding-top:18px; margin-top:18px;">
            <div style="font-size:18px; font-weight:850; color:#c45112; margin-bottom:6px;">⚠️ 안내 말씀</div>
            <div style="font-size:16px; word-break:keep-all;">
                앱 이용에 불편을 드려 진심으로 죄송합니다.
                현재 초창기 버그와 오류를 보완하고 있으며, 앞으로는 데이터가 안전하게 보관될 수 있도록 백업 시스템을 개선하겠습니다.
                보다 안정적이고 편리한 오답노트 앱으로 운영할 수 있도록 지속적으로 노력하겠습니다.
            </div>
        </div>

        <div style="margin-top:22px; text-align:center; font-size:16px; font-weight:800; color:#303846;">
            - SG 고등관 조교 -
        </div>
    </div>
    """

    components.html(
        banner_html,
        height=760,
        scrolling=False
    )


# ---------------------- DB 연결 ----------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # users 테이블 생성
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            grade TEXT DEFAULT '미지정',
            temp_password TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    # 기존 users 테이블에 grade 컬럼이 없으면 추가
    cur.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cur.fetchall()]

    if "grade" not in user_columns:
        cur.execute("ALTER TABLE users ADD COLUMN grade TEXT DEFAULT '미지정'")

    if "temp_password" not in user_columns:
        cur.execute("ALTER TABLE users ADD COLUMN temp_password TEXT DEFAULT ''")

    # wrong_answers 테이블 생성
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wrong_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT '',
            unit TEXT NOT NULL DEFAULT '',
            problem TEXT NOT NULL DEFAULT '',
            memo TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT ''
        )
    """)

    # 기존 wrong_answers 테이블에 필요한 컬럼이 없으면 추가
    cur.execute("PRAGMA table_info(wrong_answers)")
    existing_columns = [row[1] for row in cur.fetchall()]

    required_columns = {
        "username": "TEXT NOT NULL DEFAULT ''",
        "unit": "TEXT NOT NULL DEFAULT ''",
        "problem": "TEXT NOT NULL DEFAULT ''",
        "memo": "TEXT DEFAULT ''",
        "created_at": "TEXT NOT NULL DEFAULT ''"
    }

    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            cur.execute(f"ALTER TABLE wrong_answers ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


# ---------------------- 비밀번호 처리 ----------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def create_user(username: str, password: str, grade: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO users (
                username, password_hash, grade, temp_password, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                username,
                hash_pw(password),
                grade,
                "",
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def check_user(username: str, password: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )

    row = cur.fetchone()
    conn.close()

    if row is None:
        return False

    return row[0] == hash_pw(password)



def change_my_password(username: str, current_password: str, new_password: str) -> bool:
    """학생 본인이 현재 비밀번호를 확인한 뒤 새 비밀번호로 변경합니다."""
    if not check_user(username, current_password):
        return False

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET password_hash = ?, temp_password = ''
        WHERE username = ?
        """,
        (hash_pw(new_password), username)
    )

    conn.commit()
    conn.close()
    return True


def get_admin_password_status() -> pd.DataFrame:
    """
    관리자에게 임시 비밀번호만 보여줍니다.
    학생이 직접 변경한 비밀번호는 해시로 저장되므로 확인할 수 없습니다.
    """
    conn = get_conn()

    df = pd.read_sql_query(
        """
        SELECT
            username AS 학생,
            COALESCE(grade, '미지정') AS 학년,
            CASE
                WHEN COALESCE(temp_password, '') = ''
                THEN '학생이 직접 변경함'
                ELSE temp_password
            END AS 비밀번호상태,
            created_at AS 가입일시
        FROM users
        ORDER BY created_at DESC
        """,
        conn
    )

    conn.close()
    return df


# ---------------------- 오답 저장/조회 ----------------------
def add_wrong_answer(username: str, book: str, problem_number: str, note: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO wrong_answers 
        (username, unit, problem, memo, created_at) 
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username,
            book,
            problem_number,
            note,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )

    conn.commit()
    conn.close()


def get_my_wrong_answers(username: str) -> pd.DataFrame:
    conn = get_conn()

    df = pd.read_sql_query(
        """
        SELECT 
            unit AS 교재,
            problem AS 문제번호,
            memo AS 비고,
            created_at AS 작성일시
        FROM wrong_answers
        WHERE username = ?
        ORDER BY id DESC
        """,
        conn,
        params=(username,)
    )

    conn.close()
    return df


def get_all_wrong_answers() -> pd.DataFrame:
    conn = get_conn()

    df = pd.read_sql_query(
        """
        SELECT 
            w.username AS 학생,
            COALESCE(u.grade, '미지정') AS 학년,
            w.unit AS 교재,
            w.problem AS 문제번호,
            w.memo AS 비고,
            w.created_at AS 작성일시
        FROM wrong_answers w
        LEFT JOIN users u
        ON w.username = u.username
        ORDER BY w.id DESC
        """,
        conn
    )

    conn.close()
    return df


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="오답현황")

    output.seek(0)
    return output.getvalue()


# ---------------------- 회원 관리 ----------------------
def get_all_users() -> pd.DataFrame:
    conn = get_conn()

    df = pd.read_sql_query(
        """
        SELECT 
            u.username AS 학생,
            COALESCE(u.grade, '미지정') AS 학년,
            u.created_at AS 가입일시,
            COUNT(w.id) AS 오답개수
        FROM users u
        LEFT JOIN wrong_answers w
        ON u.username = w.username
        GROUP BY u.username, u.grade, u.created_at
        ORDER BY u.created_at DESC
        """,
        conn
    )

    conn.close()
    return df


def delete_user(username: str, delete_answers: bool = True):
    conn = get_conn()
    cur = conn.cursor()

    if delete_answers:
        cur.execute(
            "DELETE FROM wrong_answers WHERE username = ?",
            (username,)
        )

    cur.execute(
        "DELETE FROM users WHERE username = ?",
        (username,)
    )

    conn.commit()
    conn.close()


def reset_user_password(username: str, new_password: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET password_hash = ?, temp_password = ?
        WHERE username = ?
        """,
        (hash_pw(new_password), new_password, username)
    )

    conn.commit()
    conn.close()


def update_user_grade(username: str, new_grade: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET grade = ? WHERE username = ?",
        (new_grade, username)
    )

    conn.commit()
    conn.close()



def restore_users_from_excel(uploaded_file, temporary_password: str = "sg2026"):
    """
    회원목록 엑셀을 읽어 학생 계정을 일괄 복구합니다.

    지원 열:
    - 학생
    - 학년
    - 임시비밀번호 (없으면 temporary_password 사용)
    - 기존가입일시 (없으면 현재 시각 사용)

    이미 존재하는 학생은 삭제하지 않고
    학년과 비밀번호만 갱신합니다.
    """
    df = pd.read_excel(uploaded_file)

    required_columns = {"학생", "학년"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "필수 열이 없습니다: " + ", ".join(sorted(missing_columns))
        )

    conn = get_conn()
    cur = conn.cursor()

    created_count = 0
    updated_count = 0
    skipped_count = 0
    restored_names = []

    try:
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

            created_at_value = row.get("기존가입일시", "")
            created_at = (
                datetime.now().strftime("%Y-%m-%d %H:%M")
                if pd.isna(created_at_value) or str(created_at_value).strip() == ""
                else str(created_at_value).strip()
            )

            cur.execute(
                "SELECT username FROM users WHERE username = ?",
                (username,)
            )
            exists = cur.fetchone() is not None

            if exists:
                cur.execute(
                    """
                    UPDATE users
                    SET password_hash = ?, grade = ?, temp_password = ?
                    WHERE username = ?
                    """,
                    (hash_pw(password), grade, password, username)
                )
                updated_count += 1
            else:
                cur.execute(
                    """
                    INSERT INTO users
                    (username, password_hash, grade, temp_password, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        hash_pw(password),
                        grade,
                        password,
                        created_at
                    )
                )
                created_count += 1

            restored_names.append(username)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "total": created_count + updated_count,
        "names": restored_names
    }


# ---------------------- 초기화 ----------------------
init_db()
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
            © SG 고등관 오답노트 | 안전한 학습 관리 시스템
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
                add_wrong_answer(
                    st.session_state.student_user,
                    book,
                    problem_number.strip(),
                    note.strip()
                )
                st.success("오답이 저장되었습니다.")
                st.rerun()

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
                    display_df["비고"].fillna("").str.contains("변형문제", case=False, na=False)
                ].copy()

                if variant_df.empty:
                    st.info("현재 필터 기준에서 비고에 '변형문제'가 적힌 기록이 없습니다.")
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
                    "해당 학생의 오답 기록도 함께 삭제",
                    value=True
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