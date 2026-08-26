import pandas as pd
import streamlit as st
from supabase import create_client


st.set_page_config(
    page_title="내 오답 수정·삭제",
    page_icon="✏️",
    layout="centered",
)


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
    problem = str(row.get("problem", "") or "문제번호 없음")
    created_at = str(row.get("created_at", "") or "")
    date_text = created_at[:10] if created_at else "날짜 없음"
    return f"{book} · {problem}번 · {date_text}"


selected_id = st.selectbox(
    "수정·삭제할 오답 기록",
    option_ids,
    format_func=option_label,
)
selected = row_map[int(selected_id)]

st.markdown("#### 현재 저장된 기록")
preview = pd.DataFrame(
    [
        {
            "교재": selected.get("unit", ""),
            "문제번호": selected.get("problem", ""),
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
    current_book = str(selected.get("unit", "") or "").strip()
    selectable_books = list(dict.fromkeys(([current_book] if current_book else []) + active_books))

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
        value=str(selected.get("problem", "") or ""),
        key=f"edit_problem_{selected_id}",
        help="여러 문제를 한 기록에 저장한 경우 기존 입력 형식대로 작성해주세요.",
    )
    edited_memo = st.text_area(
        "메모",
        value=str(selected.get("memo", "") or ""),
        key=f"edit_memo_{selected_id}",
    )

    if current_book.startswith("X-패턴") or str(edited_book).startswith("X-패턴"):
        st.warning(
            "X-패턴 교재는 학교별 내부 문제번호 변환이 적용됩니다. "
            "X-패턴 기록의 교재 또는 문제번호를 수정할 때는 선생님에게 확인해주세요."
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
        else:
            try:
                if not record_is_mine(supabase, username, int(selected_id)):
                    st.error("수정 권한이 없거나 이미 삭제된 기록입니다.")
                else:
                    update_my_wrong_answer(
                        supabase,
                        username,
                        int(selected_id),
                        str(edited_book),
                        edited_problem,
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
