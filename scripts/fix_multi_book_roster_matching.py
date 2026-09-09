from pathlib import Path

path = Path('app.py')
text = path.read_text(encoding='utf-8')

helper = '''\n\ndef split_roster_books(value) -> list[str]:\n    \"\"\"학생 명단의 쉼표 구분 교재 문자열을 개별 교재명으로 분리합니다.\"\"\"\n    raw = str(value or \"\").strip()\n    if not raw:\n        return []\n    return [part.strip() for part in raw.split(',') if part.strip()]\n'''

anchor = 'def get_teacher_student_status_df() -> pd.DataFrame:\n'
if 'def split_roster_books(value)' not in text:
    idx = text.index(anchor)
    text = text[:idx] + helper + '\n' + text[idx:]

old_status_loop = '''    records = []\n\n    for _, row in roster.iterrows():\n        key = (str(row[\"학생명\"]), str(row[\"매칭교재\"]))\n        answer = answer_map.get(key, {\"numbers\": [], \"latest\": \"\"})\n        count = len(answer[\"numbers\"])\n\n        records.append(\n            {\n                \"담당선생님\": row[\"담당선생님\"],\n                \"반명\": row[\"반명\"],\n                \"학생명\": row[\"학생명\"],\n                \"학교명\": row[\"학교명\"],\n                \"학년\": row[\"학년\"],\n                \"매칭교재\": row[\"매칭교재\"],\n                \"작성여부\": \"O\" if count > 0 else \"X\",\n                \"작성문제수\": count,\n                \"최근작성일시\": answer[\"latest\"],\n            }\n        )\n'''
new_status_loop = '''    records = []\n\n    for _, row in roster.iterrows():\n        roster_books = split_roster_books(row[\"매칭교재\"]) or [str(row[\"매칭교재\"]).strip()]\n\n        for roster_book in roster_books:\n            key = (str(row[\"학생명\"]).strip(), roster_book)\n            answer = answer_map.get(key, {\"numbers\": [], \"latest\": \"\"})\n            count = len(answer[\"numbers\"])\n\n            records.append(\n                {\n                    \"담당선생님\": row[\"담당선생님\"],\n                    \"반명\": row[\"반명\"],\n                    \"학생명\": row[\"학생명\"],\n                    \"학교명\": row[\"학교명\"],\n                    \"학년\": row[\"학년\"],\n                    \"매칭교재\": roster_book,\n                    \"작성여부\": \"O\" if count > 0 else \"X\",\n                    \"작성문제수\": count,\n                    \"최근작성일시\": answer[\"latest\"],\n                }\n            )\n'''
if old_status_loop not in text:
    raise SystemExit('status loop target not found')
text = text.replace(old_status_loop, new_status_loop, 1)

old_teacher_roster = '''            teacher_roster = roster[\n                roster[\"담당선생님\"] == current_teacher\n            ][[\"학생명\", \"매칭교재\"]].drop_duplicates()\n\n            # 같은 이름의 다른 학생 또는 다른 교재 기록이 섞이지 않도록\n            # 학생명 + 교재를 함께 기준으로 로그인한 선생님의 기록만 표시합니다.\n            df = df.merge(\n                teacher_roster,\n                left_on=[\"학생\", \"교재\"],\n                right_on=[\"학생명\", \"매칭교재\"],\n                how=\"inner\"\n            ).drop(columns=[\"학생명\", \"매칭교재\"])\n'''
new_teacher_roster = '''            teacher_roster = roster[\n                roster[\"담당선생님\"] == current_teacher\n            ][[\"학생명\", \"매칭교재\"]].drop_duplicates()\n\n            # 한 학생의 명단 교재가 \"교재A, 교재B\"처럼 한 셀에 여러 개 들어간 경우\n            # 실제 wrong_answers.unit의 개별 교재명과 정상적으로 매칭되도록 행을 분리합니다.\n            expanded_rows = []\n            for _, roster_row in teacher_roster.iterrows():\n                books = split_roster_books(roster_row[\"매칭교재\"])\n                for roster_book in books:\n                    expanded_rows.append(\n                        {\n                            \"학생명\": str(roster_row[\"학생명\"]).strip(),\n                            \"매칭교재\": roster_book,\n                        }\n                    )\n\n            teacher_roster_expanded = pd.DataFrame(\n                expanded_rows,\n                columns=[\"학생명\", \"매칭교재\"],\n            ).drop_duplicates()\n\n            # 같은 이름의 다른 학생 또는 다른 교재 기록이 섞이지 않도록\n            # 학생명 + 개별 교재를 함께 기준으로 로그인한 선생님의 기록만 표시합니다.\n            df = df.merge(\n                teacher_roster_expanded,\n                left_on=[\"학생\", \"교재\"],\n                right_on=[\"학생명\", \"매칭교재\"],\n                how=\"inner\"\n            ).drop(columns=[\"학생명\", \"매칭교재\"])\n'''
if old_teacher_roster not in text:
    raise SystemExit('teacher roster merge target not found')
text = text.replace(old_teacher_roster, new_teacher_roster, 1)

path.write_text(text, encoding='utf-8')
print('multi-book roster matching fixed')
