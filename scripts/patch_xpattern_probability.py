from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

start_marker = '    "X-패턴 확통": {'
end_marker = '    },\n}\n\n\ndef format_xpattern_display_numbers'

start = text.index(start_marker)
end = text.index(end_marker, start)

new_block = '''    "X-패턴 확통": {
        # 2024: 원본 PDF Contents 순서대로 500~3200번대 배정
        "24 강남고": [{"offset": 500, "max": 19, "exam_type": '1학기중간'}],
        "24 다운고": [{"offset": 600, "max": 22, "exam_type": '1학기중간'}],
        "24 달천고": [{"offset": 700, "max": 21, "exam_type": '2학기중간'}],
        "24 대송고": [{"offset": 800, "max": 19, "exam_type": '2학기중간'}],
        "24 매곡고": [{"offset": 900, "max": 22, "exam_type": '1학기중간'}],
        "24 무거고": [{"offset": 1000, "max": 23, "exam_type": '1학기중간'}],
        "24 무룡고": [{"offset": 1100, "max": 21, "exam_type": '2학기중간'}],
        "24 삼산고": [{"offset": 1200, "max": 22, "exam_type": '2학기중간'}],
        "24 성광여고": [{"offset": 1300, "max": 19, "exam_type": '1학기중간'}],
        "24 신선여고": [{"offset": 1400, "max": 21, "exam_type": '1학기중간'}],
        "24 약사고": [{"offset": 1500, "max": 20, "exam_type": '1학기중간'}],
        "24 우신고": [
            {"offset": 1600, "max": 20, "exam_type": '1학기중간'},
            {"offset": 1700, "max": 20, "exam_type": '2학기중간'},
        ],
        "24 울산고": [{"offset": 1800, "max": 24, "exam_type": '2학기중간'}],
        "24 울산여고": [{"offset": 1900, "max": 24, "exam_type": '2학기중간'}],
        "24 울산외고": [{"offset": 2000, "max": 18, "exam_type": '1학기중간'}],
        "24 제일고": [{"offset": 2100, "max": 22, "exam_type": '1학기중간'}],
        "24 중앙고": [{"offset": 2200, "max": 24, "exam_type": '2학기중간'}],
        "24 천상고": [{"offset": 2300, "max": 21, "exam_type": '2학기중간'}],
        "24 학성고": [
            {"offset": 2400, "max": 20, "exam_type": '1학기중간'},
            {"offset": 2500, "max": 20, "exam_type": '2학기중간'},
        ],
        "24 학성여고": [{"offset": 2600, "max": 19, "exam_type": '1학기중간'}],
        "24 현대고": [
            {"offset": 2700, "max": 22, "exam_type": '1학기중간'},
            {"offset": 2800, "max": 22, "exam_type": '2학기중간'},
        ],
        "24 호계고": [{"offset": 2900, "max": 20, "exam_type": '1학기중간'}],
        "24 화봉고": [{"offset": 3000, "max": 22, "exam_type": '2학기중간'}],
        "24 화암고": [{"offset": 3100, "max": 19, "exam_type": '1학기중간'}],
        "24 효정고": [{"offset": 3200, "max": 22, "exam_type": '1학기중간'}],

        # 2023: 원본 PDF Contents 순서대로 3300~4000번대 배정
        "23 삼산고": [{"offset": 3300, "max": 21, "exam_type": '2학기중간'}],
        "23 울산고": [{"offset": 3400, "max": 16, "exam_type": '2학기중간'}],
        "23 울산여고": [{"offset": 3500, "max": 20, "exam_type": '2학기중간'}],
        "23 울산외고": [{"offset": 3600, "max": 23, "exam_type": '1학기중간'}],
        "23 제일고": [{"offset": 3700, "max": 18, "exam_type": '1학기중간'}],
        "23 학성고": [
            {"offset": 3800, "max": 21, "exam_type": '1학기중간'},
            {"offset": 3900, "max": 21, "exam_type": '2학기중간'},
        ],
        "23 함월고": [{"offset": 4000, "max": 22, "exam_type": '1학기중간'}],
'''

new_text = text[:start] + new_block + text[end:]
path.write_text(new_text, encoding="utf-8")

print("X-패턴 확통 매핑을 PDF 기준으로 교체했습니다.")
