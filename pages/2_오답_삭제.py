import re

import pandas as pd
import streamlit as st
from supabase import create_client


st.set_page_config(
    page_title="내 오답 수정·삭제",
    page_icon="✏️",
    layout="centered",
)


# X-패턴은 DB에 학교별 offset이 더해진 내부번호로 저장됩니다.
# 대부분 100단위 offset을 사용하며, 일부 교재만 예외 offset을 사용합니다.
XPATTERN_SPECIAL_OFFSETS = {
    "X-패턴 공통수학2": [3008],
    "X-패턴 미적분1": [1816, 2115],
}


def get_supabase_client():
    try:
        url = str(st.secrets["SUPABASE_URL"]).strip().rstrip("/")
        key = str(st.secrets["SUPABASE_KEY"]).strip()
    except Exception:
        st.error("Supabase 연결 정보가 없습니다. 관리자에게 문의해주세요.")
        st.stop()

    return create_client(url, key)


def fetch_my_wrong_answers(client, username: str) -> pd.DataFrame:
    response = (
        client.table("wrong_answers")
        .select("id,username,unit,problem,memo,created_at")
        .eq("username", username)
        .order("id", desc=True)
        .execute()
    )
    rows = response.data or []

    if not rows:
        return pd.DataFrame(
            columns=["id", "username", "unit", "problem", "memo", "created_at"]
        )

    return pd.DataFrame(rows)


def fetch_active_book_names(client) -> list[str]:
    """관리자가 book_master에서 활성화한 교재를 수정 선택지로 불러옵니다."""
    try:
        response = (
            client.table("book_master")
            .select("book_name,is_active")
            .eq("is_active", True)
            .order("book_name")
            .execute()
        )
        rows = response.data or []
        return list(
            dict.fromkeys(
                str(row.get("book_name", "")).strip()
                for row in rows
                if str(row.get("book_name", "")).strip()
            )
        )
    except Exception:
        return []


def parse_numbers(value: str) -> list[int]:
    return [int(number) for number in re.findall(r"\d+", str(value or ""))]


def infer_xpattern_offset(book: str, problem: str) -> int | None:
    """저장된 내부번호 묶음에서 사용 중인 X-패턴 offset을 추정합니다."""
    if not str(book).startswith("X-패턴"):
        return None

    numbers = parse_numbers(problem)
    if not numbers:
        return None

    regular_offsets = list(range(500, 3901, 100))
    candidates = regular_offsets + XPATTERN_SPECIAL_OFFSETS.get(str(book), [])

    valid_offsets = [
        offset
        for offset in candidates
        if all(1 <= number - offset <= 100 for number in numbers)
    ]

    return max(valid_offsets) if valid_offsets else None


def xpattern_original_problem(book: str, problem: str) -> tuple[str, int | None]:
    """DB 내부번호를 학생이 보는 원래 시험지 번호로 변환합니다."""
    offset = infer_xpattern_offset(book, problem)
    numbers = parse_numbers(problem)

    if offset is None or not numbers:
        return str(problem or ""), None

    original_numbers = [number - offset for number in numbers]
    return ", ".join(str(number) for number in original_numbers), offset


def xpattern_internal_problem(problem: str, offset: int) -> str:
    """학생이 입력한 원래 번호를 DB 저장용 내부번호로 변환합니다."""
    numbers = parse_numbers(problem)
    return ", ".join(str(offset + number) for number in numbers)


def record_is_mine(client, username: str, record_id: int) -> bool:
    response = (
        client.table("wrong_answers")
        .select("id")
        .eq("id", int(record_id))
        .eq("username", username)
        .limit(1)
        .execute()
    )
    return bool(response.data or [])


def update_my_wrong_answer(
    client,
    username: str,
    record_id: int,
    book: str,
    problem: str,
    memo: str,
) -> None:
    # id와 username을 동시에 조건으로 걸어 본인 기록만 수정합니다.
    (
        client.table("wrong_answers")
        .update(
            {
                "unit": book.strip(),
                "problem": problem.strip(),
                "memo": memo.strip(),
            }
        )
        .eq("id", int(record_id))
        .eq("username", username)
        .execute()
    )


def delete_my_wrong_answer(client, username: str, record_id: int) -> None:
    # id만 사용하지 않고 username도 함께 조건으로 걸어 다른 학생 기록 삭제를 방지합니다.
    (
        client.table("wrong_answers")
        .delete()
        .eq("id", int(record_id))
        .eq("username", username)
        .execute()
    )


st.title("✏️ 내 오답 수정·삭제")

username = st.session_state.get("student_user")

if not username:
    st.warning("학생 로그인 후 이용할 수 있습니다.")
    st.page_link("app.py", label="← 로그인 화면으로", icon="🏠")
    st.stop()

st.write(f"**{username}**님이 직접 저장한 오답만 수정하거나 삭제할 수 있습니다.")
st.caption("교재를 잘못 선택했거나 문제번호를 잘못 입력한 경우 아래에서 바로 수정할 수 있습니다.")

supabase = get_supabase_client()

try:
    df = fetch_my_wrong_answers(supabase, username)
except Exception as error:
    st.error("오답 목록을 불러오지 못했습니다.")
    st.code(f"{type(error).__name__}: {error}", language="text")
    st.stop()

if df.empty:
    st.info("수정하거나 삭제할 오답 기록이 없습니다.")
    st.page_link("app.py", label="← 내 오답노트로 돌아가기", icon="🏠")
    st.stop()

book_names = sorted(
    value
    for value in df["unit"].fillna("").astype(str).str.strip().unique().tolist()
    if value
)
book_filter = st.selectbox("교재 필터", ["전체"] + book_names)

filtered_df = df.copy()
if book_filter != "전체":
    filtered_df = filtered_df[filtered_df["unit"] == book_filter].copy()

if filtered_df.empty:
    st.info("선택한 교재에 수정하거나 삭제할 오답이 없습니다.")
    st.stop()

option_ids = filtered_df["id"].astype(int).tolist()
row_map = {
    int(row["id"]): row
    for _, row in filtered_df.iterrows()
}


def option_label(record_id: int) -> str:
    row = row_map[record_id]
    book = str(row.get("unit", "") or "교재 미지정")
    raw_problem = str(row.get("problem", "") or "문제번호 없음")
    display_problem, _ = xpattern_original_problem(book, raw_problem)
    created_at = str(row.get("created_at", "") or "")
    date_text = created_at[:10] if created_at else "날짜 없음"
    return f"{book} · {display_problem}번 · {date_text}"


selected_id = st.selectbox(
    "수정·삭제할 오답 기록",
    option_ids,
    format_func=option_label,
)
selected = row_map[int(selected_id)]

current_book = str(selected.get("unit", "") or "").strip()
current_raw_problem = str(selected.get("problem", "") or "")
current_display_problem, current_xpattern_offset = xpattern_original_problem(
    current_book,
    current_raw_problem,
)

st.markdown("#### 현재 저장된 기록")
preview = pd.DataFrame(
    [
        {
            "교재": current_book,
            "문제번호": current_display_problem,
            "메모": selected.get("memo", ""),
            "저장일시": selected.get("created_at", ""),
        }
    ]
)
st.dataframe(preview, use_container_width=True, hide_index=True)

edit_tab, delete_tab = st.tabs(["✏️ 수정", "🗑️ 삭제"])

with edit_tab:
    st.markdown("#### 오답 기록 수정")

    active_books = fetch_active_book_names(supabase)
    selectable_books = list(
        dict.fromkeys(([current_book] if current_book else []) + active_books)
    )

    if not selectable_books:
        selectable_books = [current_book] if current_book else ["미지정"]

    current_book_index = (
        selectable_books.index(current_book)
        if current_book in selectable_books
        else 0
    )

    edited_book = st.selectbox(
        "교재",
        selectable_books,
        index=current_book_index,
        key=f"edit_book_{selected_id}",
    )

    edited_problem = st.text_input(
        "문제번호",
        value=current_display_problem,
        key=f"edit_problem_{selected_id}",
        help="쉼표나 띄어쓰기로 여러 문제번호를 입력할 수 있습니다.",
    )

    edited_memo = st.text_area(
        "메모",
        value=str(selected.get("memo", "") or ""),
        key=f"edit_memo_{selected_id}",
    )

    if current_book.startswith("X-패턴") and current_xpattern_offset is not None:
        st.info(
            "X-패턴도 직접 수정할 수 있습니다. 화면에는 원래 시험지 문제번호가 표시되며, "
            "저장할 때 앱이 내부번호로 자동 변환합니다."
        )

    update_confirm = st.checkbox(
        "위 내용으로 수정하는 것이 맞습니다.",
        key=f"update_confirm_{selected_id}",
    )

    if st.button(
        "수정 내용 저장",
        type="primary",
        use_container_width=True,
        disabled=not update_confirm,
        key=f"update_button_{selected_id}",
    ):
        if not str(edited_book).strip():
            st.warning("교재를 선택해주세요.")
        elif not edited_problem.strip():
            st.warning("문제번호를 입력해주세요.")
        elif not parse_numbers(edited_problem):
            st.warning("올바른 문제번호를 입력해주세요.")
        else:
            try:
                if not record_is_mine(supabase, username, int(selected_id)):
                    st.error("수정 권한이 없거나 이미 삭제된 기록입니다.")
                else:
                    problem_to_save = edited_problem.strip()

                    # 같은 X-패턴 교재 안에서 수정하는 경우 원래 번호를 내부번호로 자동 변환합니다.
                    if (
                        current_book.startswith("X-패턴")
                        and str(edited_book) == current_book
                        and current_xpattern_offset is not None
                    ):
                        original_numbers = parse_numbers(edited_problem)
                        if any(number < 1 or number > 100 for number in original_numbers):
                            st.warning("X-패턴 문제번호는 원래 시험지 번호로 입력해주세요.")
                            st.stop()
                        problem_to_save = xpattern_internal_problem(
                            edited_problem,
                            current_xpattern_offset,
                        )

                    # X-패턴 교재 자체를 다른 X-패턴 교재로 바꾸는 경우 학교별 offset을
                    # 자동 판단할 수 없으므로 교재 변경만 제한하고, 문제번호 수정은 허용합니다.
                    if (
                        current_book.startswith("X-패턴")
                        and str(edited_book).startswith("X-패턴")
                        and str(edited_book) != current_book
                    ):
                        st.warning(
                            "X-패턴 교재를 다른 X-패턴 교재로 바꾸는 경우에는 학교 정보가 달라질 수 있습니다. "
                            "기존 기록을 삭제한 뒤 새 교재에서 다시 저장해주세요."
                        )
                    else:
                        update_my_wrong_answer(
                            supabase,
                            username,
                            int(selected_id),
                            str(edited_book),
                            problem_to_save,
                            edited_memo,
                        )
                        st.success("오답 기록을 수정했습니다.")
                        st.rerun()
            except Exception as error:
                st.error("오답 수정 중 오류가 발생했습니다.")
                st.code(f"{type(error).__name__}: {error}", language="text")

with delete_tab:
    st.markdown("#### 오답 기록 삭제")
    st.warning("삭제한 기록은 앱에서 복구할 수 없습니다. 삭제 전에 교재와 문제번호를 다시 확인해주세요.")

    delete_confirm = st.checkbox(
        "위 기록을 삭제하는 것이 맞습니다.",
        key=f"delete_confirm_{selected_id}",
    )

    if st.button(
        "선택한 오답 삭제",
        use_container_width=True,
        disabled=not delete_confirm,
        key=f"delete_button_{selected_id}",
    ):
        try:
            if not record_is_mine(supabase, username, int(selected_id)):
                st.error("삭제 권한이 없거나 이미 삭제된 기록입니다.")
            else:
                delete_my_wrong_answer(supabase, username, int(selected_id))
                st.success("오답 기록을 삭제했습니다.")
                st.rerun()
        except Exception as error:
            st.error("오답 삭제 중 오류가 발생했습니다.")
            st.code(f"{type(error).__name__}: {error}", language="text")

st.divider()
st.page_link("app.py", label="← 내 오답노트로 돌아가기", icon="🏠")
