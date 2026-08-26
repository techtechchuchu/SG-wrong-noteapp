from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

old_ui = '''        # X-패턴 계열은 여러 학교 기출을 이어붙인 교재라, 학생이 시험지에 적힌
        # 원래 번호만 봐서는 내부 번호(학교별 500/600/700...번대)를 알 수 없다.
        # 학교(+시험)를 고르면 원래 번호를 그대로 입력해도 자동 변환해서 저장한다.
        xpattern_schools = XPATTERN_SCHOOL_MAP.get(book, {})
        selected_school = None
        selected_xpattern_block = None

        if xpattern_schools:
            st.info(
                "🏫 이 교재는 여러 학교 기출을 이어붙인 X-패턴 교재입니다. "
                "**학교(시험)를 먼저 선택**한 뒤, 문제 번호는 시험지에 적힌 "
                "원래 번호를 그대로 입력해주세요. 저장 시 자동으로 변환됩니다."
            )

            school_options = sorted(xpattern_schools.keys())
            selected_school = st.selectbox(
                "학교 선택 (X-패턴 전용)",
                school_options,
                key="xpattern_school_select",
            )

            blocks = xpattern_schools[selected_school]
            if len(blocks) == 1:
                selected_xpattern_block = blocks[0]
            else:
                block_labels = [
                    b["exam_type"] or f"{i + 1}번째 시험"
                    for i, b in enumerate(blocks)
                ]
                block_index = st.selectbox(
                    "시험 선택 (같은 학교가 이 교재에 시험을 여러 번 냈습니다)",
                    list(range(len(blocks))),
                    format_func=lambda i: block_labels[i],
                    key="xpattern_block_select",
                )
                selected_xpattern_block = blocks[block_index]

            st.caption(
                f"'{selected_school}'"
                + (f" ({selected_xpattern_block['exam_type']})" if selected_xpattern_block['exam_type'] else "")
                + f" 원래 시험지 번호는 1~{selected_xpattern_block['max']}번까지 있습니다. "
                "그 번호를 그대로 입력해주세요."
            )
'''

new_ui = '''        # X-패턴 계열은 학교별 기출을 이어붙인 교재입니다.
        # 같은 학교에 시험이 여러 개 있더라도 2단계 선택을 만들지 않고
        # "학교 + 시험"을 하나의 선택지로 펼쳐서 학생이 한 번에 고르게 합니다.
        xpattern_schools = XPATTERN_SCHOOL_MAP.get(book, {})
        selected_school = None
        selected_xpattern_block = None
        selected_xpattern_exam_label = ""
        requires_exam_confirm = False

        if xpattern_schools:
            st.info(
                "🏫 이 교재는 여러 학교 기출을 이어붙인 X-패턴 교재입니다. "
                "학교와 시험 시기를 한 번에 정확히 선택한 뒤, 문제 번호는 "
                "시험지에 적힌 원래 번호를 그대로 입력해주세요."
            )

            exam_options = []
            for school_name, blocks in xpattern_schools.items():
                multiple_exams = len(blocks) > 1
                for block_index, block in enumerate(blocks):
                    exam_type = str(block.get("exam_type", "") or "").strip()
                    color_icon = ""
                    if "1학기" in exam_type:
                        color_icon = "🟦 "
                    elif "2학기" in exam_type:
                        color_icon = "🟧 "

                    display_label = color_icon + school_name
                    if exam_type:
                        display_label += f" {exam_type}"

                    exam_options.append(
                        {
                            "label": display_label,
                            "school": school_name,
                            "block": block,
                            "multiple_exams": multiple_exams,
                            "block_index": block_index,
                        }
                    )

            exam_options = sorted(
                exam_options,
                key=lambda item: (
                    item["school"],
                    str(item["block"].get("exam_type", "")),
                ),
            )

            selected_exam_index = st.selectbox(
                "학교·시험 선택 (X-패턴 전용)",
                options=list(range(len(exam_options))),
                format_func=lambda i: exam_options[i]["label"],
                key="xpattern_school_exam_select",
            )

            selected_exam = exam_options[selected_exam_index]
            selected_school = selected_exam["school"]
            selected_xpattern_block = selected_exam["block"]
            selected_xpattern_exam_label = selected_exam["label"]
            requires_exam_confirm = bool(selected_exam["multiple_exams"])

            exam_type = str(selected_xpattern_block.get("exam_type", "") or "").strip()
            if "1학기" in exam_type:
                st.markdown(
                    "<div style='padding:12px 14px;border-radius:10px;"
                    "border:1px solid #3b82f6;background:rgba(59,130,246,.12);"
                    "font-weight:800;'>🟦 현재 선택: "
                    + html.escape(selected_school)
                    + (" · " + html.escape(exam_type) if exam_type else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )
            elif "2학기" in exam_type:
                st.markdown(
                    "<div style='padding:12px 14px;border-radius:10px;"
                    "border:1px solid #f59e0b;background:rgba(245,158,11,.12);"
                    "font-weight:800;'>🟧 현재 선택: "
                    + html.escape(selected_school)
                    + (" · " + html.escape(exam_type) if exam_type else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )

            st.caption(
                f"원래 시험지 번호는 1~{selected_xpattern_block['max']}번까지 있습니다. "
                "그 번호를 그대로 입력해주세요."
            )
'''

if old_ui not in text:
    raise SystemExit("학생 X-패턴 기존 선택 UI 블록을 찾지 못했습니다.")
text = text.replace(old_ui, new_ui, 1)

old_confirm = '''        book_confirm_label = f"'{book}' 교재가 맞는지 확인했습니다."
        if selected_school:
            book_confirm_label += f" (학교: {selected_school})"

        book_confirm = st.checkbox(
            book_confirm_label,
            key="student_book_confirm",
        )

        if st.button("오답 저장"):
            if problem_number.strip() == "":
                st.warning("문제 번호를 입력해주세요.")
            elif not book_confirm:
                st.error("선택한 교재가 맞는지 확인한 후 체크해주세요.")
            elif xpattern_schools and selected_xpattern_block is None:
                st.error("학교를 선택해주세요.")
            else:
'''

new_confirm = '''        book_confirm_label = f"'{book}' 교재가 맞는지 확인했습니다."
        if selected_school:
            exam_type = str(selected_xpattern_block.get("exam_type", "") or "").strip()
            selected_text = selected_school + (f" {exam_type}" if exam_type else "")
            book_confirm_label += f" (선택: {selected_text})"

        book_confirm = st.checkbox(
            book_confirm_label,
            key="student_book_confirm",
        )

        exam_period_confirm = True
        if xpattern_schools and requires_exam_confirm:
            st.warning(
                "⚠️ 같은 학교의 시험이 여러 개 등록되어 있습니다. "
                "저장 전에 학기를 반드시 다시 확인해주세요."
            )
            exam_period_confirm = st.checkbox(
                "<중요> 1학기 중간인지 2학기 중간인지 확인했습니다.",
                key="student_xpattern_exam_period_confirm",
            )

        if st.button("오답 저장"):
            if problem_number.strip() == "":
                st.warning("문제 번호를 입력해주세요.")
            elif not book_confirm:
                st.error("선택한 교재가 맞는지 확인한 후 체크해주세요.")
            elif xpattern_schools and selected_xpattern_block is None:
                st.error("학교·시험을 선택해주세요.")
            elif xpattern_schools and requires_exam_confirm and not exam_period_confirm:
                st.error("<중요> 시험 학기를 확인했다는 항목에 체크해주세요.")
            else:
'''

if old_confirm not in text:
    raise SystemExit("학생 X-패턴 확인 체크 블록을 찾지 못했습니다.")
text = text.replace(old_confirm, new_confirm, 1)

old_success = '''                            st.success(
                                f"'{selected_school}' 원래 번호 {problem_number.strip()} → "
                                f"저장 번호 {', '.join(result['new_numbers'])}(으)로 "
                                "변환되어 저장되었습니다."
                            )
'''
new_success = '''                            exam_type = str(selected_xpattern_block.get("exam_type", "") or "").strip()
                            selected_text = selected_school + (f" {exam_type}" if exam_type else "")
                            st.success(
                                f"'{selected_text}' 원래 번호 {problem_number.strip()} → "
                                f"저장 번호 {', '.join(result['new_numbers'])}(으)로 "
                                "변환되어 저장되었습니다."
                            )
'''

if old_success not in text:
    raise SystemExit("학생 X-패턴 저장 성공 문구 블록을 찾지 못했습니다.")
text = text.replace(old_success, new_success, 1)

path.write_text(text, encoding="utf-8")
print("X-패턴 학교·시험 단일 선택 UI와 중요 확인 체크를 반영했습니다.")
