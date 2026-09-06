from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

start_marker = '    "X-패턴 공통수학2": {'
end_marker = '    "X-패턴 미적분1": {'
start = text.index(start_marker)
end = text.index(end_marker, start)
block = text[start:end]

original_1학기기말 = {
    "24 강남고", "24 다운고", "24 달천고", "24 동천고", "24 무거고",
    "24 성신고", "24 신정고", "24 가온고+매곡고", "24 중앙고+천상고",
    "24 울산여고", "24 제일고", "24 우신고", "24 성광여고", "24 신선여고",
    "24 대현고", "24 삼산고", "24 학성고", "24 범서고+현대고", "24 울산외고",
    "24 울산고", "24 함월고", "24 약사고",
}

updated = []
changed = 0
for line in block.splitlines(True):
    for school in original_1학기기말:
        if f'"{school}"' in line and '"exam_type": \'2학기중간\'' in line:
            line = line.replace("'2학기중간'", "'1학기기말'")
            changed += 1
            break
    updated.append(line)

if changed != len(original_1학기기말):
    raise SystemExit(f"복구 대상 {len(original_1학기기말)}개 중 {changed}개만 찾았습니다.")

new_block = ''.join(updated)
text = text[:start] + new_block + text[end:]
path.write_text(text, encoding="utf-8")
print(f"공통수학2 시험시기 {changed}개를 원래 1학기기말 값으로 복구했습니다. 무룡고는 2학기중간 유지.")
