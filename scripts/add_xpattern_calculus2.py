from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

# BOOKS fallback 목록에도 추가
if '    "X-패턴 미적분2",\n' not in text:
    anchor = '    "미적분2 쎈",\n'
    if anchor not in text:
        raise SystemExit("BOOKS 삽입 위치를 찾지 못했습니다.")
    text = text.replace(anchor, anchor + '    "X-패턴 미적분2",\n', 1)

block = '''    "X-패턴 미적분2": {
        # 원본 Contents의 연도 표기는 한 해씩 밀려 있으므로 본문 실제 시험 연도를 기준으로 함.
        # 2025: PDF 첫 묶음(Contents의 2024 영역), 원본 순서대로 500~1700번대 배정
        "25 강남고": [{"offset": 500, "max": 18, "exam_type": '1학기중간'}],
        "25 다운고": [{"offset": 600, "max": 20, "exam_type": '1학기중간'}],
        "25 대현고": [{"offset": 700, "max": 16, "exam_type": '1학기중간'}],
        "25 무거고": [{"offset": 800, "max": 22, "exam_type": '1학기중간'}],
        "25 성광여고": [{"offset": 900, "max": 20, "exam_type": '1학기중간'}],
        "25 성신고": [{"offset": 1000, "max": 22, "exam_type": '1학기중간'}],
        "25 신정고": [{"offset": 1100, "max": 24, "exam_type": '1학기중간'}],
        "25 우신고": [{"offset": 1200, "max": 20, "exam_type": '1학기중간'}],
        "25 울산고": [{"offset": 1300, "max": 24, "exam_type": '2학기중간'}],
        "25 울산여고": [{"offset": 1400, "max": 23, "exam_type": '2학기중간'}],
        "25 중앙고": [{"offset": 1500, "max": 20, "exam_type": '2학기중간'}],
        "25 천상고": [{"offset": 1600, "max": 20, "exam_type": '1학기중간'}],
        "25 학성고": [{"offset": 1700, "max": 20, "exam_type": '1학기중간'}],

        # 2024: PDF 두 번째 묶음(Contents의 2023 영역), 원본 순서대로 1800~2900번대 배정
        "24 강남고": [
            {"offset": 1800, "max": 20, "exam_type": '2학기중간'},
            {"offset": 1900, "max": 20, "exam_type": '1학기중간'},
        ],
        "24 무거고": [{"offset": 2000, "max": 22, "exam_type": '1학기중간'}],
        "24 삼산고": [{"offset": 2100, "max": 16, "exam_type": '2학기중간'}],
        "24 성광여고": [{"offset": 2200, "max": 20, "exam_type": '1학기중간'}],
        "24 성신고": [{"offset": 2300, "max": 17, "exam_type": '1학기중간'}],
        "24 우신고": [{"offset": 2400, "max": 19, "exam_type": '1학기중간'}],
        "24 울산고": [{"offset": 2500, "max": 20, "exam_type": '2학기중간'}],
        "24 울산여고": [{"offset": 2600, "max": 21, "exam_type": '2학기중간'}],
        "24 중앙고": [{"offset": 2700, "max": 20, "exam_type": '2학기중간'}],
        "24 학성고": [{"offset": 2800, "max": 20, "exam_type": '1학기중간'}],
        "24 함월고": [{"offset": 2900, "max": 20, "exam_type": '1학기중간'}],
    },
'''

start_marker = '    "X-패턴 미적분2": {'
next_marker = '    "X-패턴 확통": {'

if start_marker in text:
    start = text.index(start_marker)
    end = text.index(next_marker, start)
    text = text[:start] + block + text[end:]
else:
    insert_at = text.index(next_marker)
    text = text[:insert_at] + block + text[insert_at:]

path.write_text(text, encoding="utf-8")
print("X-패턴 미적분2 BOOKS 및 학교별 offset 매핑 반영 완료")
