from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

start_marker = '    "X-패턴 공통수학2": {'
end_marker = '    "X-패턴 미적분1": {'
start = text.index(start_marker)
end = text.index(end_marker, start)

block = text[start:end]
updated_lines = []
changed = 0

for line in block.splitlines(True):
    if '"24 ' in line and '"exam_type": \'1학기기말\'' in line:
        line = line.replace("'1학기기말'", "'2학기중간'")
        changed += 1
    updated_lines.append(line)

if changed == 0:
    raise SystemExit("변경할 2024 공통수학2 1학기기말 항목을 찾지 못했습니다.")

new_block = ''.join(updated_lines)
text = text[:start] + new_block + text[end:]
path.write_text(text, encoding="utf-8")
print(f"X-패턴 공통수학2 2024 시험시기 {changed}개를 2학기중간으로 변경했습니다.")
