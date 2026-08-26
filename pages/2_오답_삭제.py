import pandas as pd
import streamlit as st
from supabase import create_client


st.set_page_config(
    page_title="내 오답 삭제",
    page_icon="🗑️",
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


def delete_my_wrong_answer(client, username: str, record_id: int) -> None:
    # id만 사용하지 않고 username도 함께 조건으로 걸어 다른 학생 기록 삭제를 방지합니다.
    (
        client.table("wrong_answers")
        .delete()
        .eq("id", int(record_id))
        .eq("username", username)
        .execute()
    )


st.title("🗑️ 내 오답 삭제")

username = st.session_state.get("student_user")

if not username:
    st.warning("학생 로그인 후 이용할 수 있습니다.")
    st.page_link("app.py", label="← 로그인 화면으로", icon="🏠")
    st.stop()

st.write(f"**{username}**님이 직접 저장한 오답만 삭제할 수 있습니다.")
st.caption("잘못 저장한 교재 또는 문제를 선택한 뒤 삭제 확인을 체크해주세요.")

supabase = get_supabase_client()

try:
    df = fetch_my_wrong_answers(supabase, username)
except Exception as error:
    st.error("오답 목록을 불러오지 못했습니다.")
    st.code(f"{type(error).__name__}: {error}", language="text")
    st.stop()

if df.empty:
    st.info("삭제할 오답 기록이 없습니다.")
    st.page_link("app.py", label="← 내 오답노트로 돌아가기", icon="🏠")
    st.stop()

book_names = sorted(
    value for value in df["unit"].fillna("").astype(str).str.strip().unique().tolist()
    if value
)
book_filter = st.selectbox("교재 필터", ["전체"] + book_names)

filtered_df = df.copy()
if book_filter != "전체":
    filtered_df = filtered_df[filtered_df["unit"] == book_filter].copy()

if filtered_df.empty:
    st.info("선택한 교재에 삭제할 오답이 없습니다.")
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
    "삭제할 오답 기록",
    option_ids,
    format_func=option_label,
)
selected = row_map[int(selected_id)]

st.markdown("#### 삭제할 기록 확인")
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

confirm = st.checkbox(
    "위 기록을 삭제하는 것이 맞습니다.",
    key=f"delete_confirm_{selected_id}",
)

if st.button(
    "선택한 오답 삭제",
    type="primary",
    use_container_width=True,
    disabled=not confirm,
):
    try:
        # 삭제 직전에도 현재 로그인 학생의 기록인지 다시 확인합니다.
        ownership = (
            supabase.table("wrong_answers")
            .select("id")
            .eq("id", int(selected_id))
            .eq("username", username)
            .limit(1)
            .execute()
        )

        if not (ownership.data or []):
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
