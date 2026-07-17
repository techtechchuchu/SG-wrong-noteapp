import io
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------- 기본 설정 ----------------------
st.set_page_config(
    page_title="SG 고등관 오답노트",
    page_icon="📝",
    layout="centered"
)

DB_PATH = "wrong_answers.db"
BANNER_PATH = Path("sg_banner.png")

try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    ADMIN_PASSWORD = None

try:
    STUDENT_SIGNUP_CODE = st.secrets["STUDENT_SIGNUP_CODE"]
except Exception:
    STUDENT_SIGNUP_CODE = None


def get_qr_signup_code():
    try:
        return st.query_params.get("code", "")
    except Exception:
        return ""


# ---------------------- 배너 ----------------------
def show_banner():
    if BANNER_PATH.exists():
        st.image(str(BANNER_PATH), width=330)


# ---------------------- DB 연결 ----------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

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


def create_user(username: str, password: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_pw(password), datetime.now().strftime("%Y-%m-%d %H:%M"))
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
            username AS 학생,
            unit AS 교재,
            problem AS 문제번호,
            memo AS 비고,
            created_at AS 작성일시
        FROM wrong_answers
        ORDER BY id DESC
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


def get_all_users() -> pd.DataFrame:
    conn = get_conn()

    df = pd.read_sql_query(
        """
        SELECT 
            u.username AS 학생,
            u.created_at AS 가입일시,
            COUNT(w.id) AS 오답개수
        FROM users u
        LEFT JOIN wrong_answers w
        ON u.username = w.username
        GROUP BY u.username, u.created_at
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
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (hash_pw(new_password), username)
    )

    conn.commit()
    conn.close()


# ---------------------- 초기화 ----------------------
init_db()

# ---------------------- 초기화 ----------------------
init_db()

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


# ---------------------- 세션 상태 ----------------------
if "role" not in st.session_state:
    st.session_state.role = None

if "student_user" not in st.session_state:
    st.session_state.student_user = None

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


# ---------------------- 시작 화면 ----------------------
def show_role_select():
    show_banner()

    st.title("📝 SG 고등관 오답노트")
    st.write("역할을 선택해주세요.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👩‍🎓 학생으로 입장", use_container_width=True):
            st.session_state.role = "student"
            st.rerun()

    with col2:
        if st.button("👨‍🏫 선생님으로 입장", use_container_width=True):
            st.session_state.role = "admin"
            st.rerun()


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
                elif create_user(new_username.strip(), new_password):
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
            placeholder="예: 계산 실수, 개념 헷갈림, 다시 질문 필요 등"
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
            col1, col2 = st.columns(2)

            with col1:
                student_filter = st.selectbox(
                    "학생 필터",
                    ["전체"] + sorted(df["학생"].unique().tolist())
                )

            with col2:
                book_filter = st.selectbox(
                    "교재 필터",
                    ["전체"] + BOOKS
                )

            display_df = df.copy()

            if student_filter != "전체":
                display_df = display_df[display_df["학생"] == student_filter]

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

        with st.expander("👥 회원 관리", expanded=False):
            users_df = get_all_users()

            if users_df.empty:
                st.info("가입된 학생이 없습니다.")
            else:
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

        if st.button("로그아웃"):
            st.session_state.is_admin = False
            st.session_state.role = None
            st.rerun()

# ---------------------- 라우팅 ----------------------
if st.session_state.role is None:
    show_role_select()
elif st.session_state.role == "student":
    show_student()
elif st.session_state.role == "admin":
    show_admin()