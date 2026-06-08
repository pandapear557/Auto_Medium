"""로컬 테스트 진입점.

사용법:
    python run_local.py            # mail.json 전체 크롤링, 결과를 콘솔에 출력
    SAVE_TO_NOTION=1 python run_local.py   # 크롤링 후 Notion 에도 저장

mail.json 형식: { "text": "<메일 본문>", "index": <선택, 정수> }
index 가 있으면 해당 글 1건만, 없으면 전체를 크롤링한다.
"""

import json
import logging
import os

from auto_medium.pipeline import run

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main():
    with open("mail.json", "r", encoding="utf-8") as f:
        event = json.load(f)

    mail_text = event["text"]
    index = event.get("index")  # 특정 글만 테스트하려면 사용, 전체는 None
    save = os.environ.get("SAVE_TO_NOTION") == "1"

    results = run(mail_text, index=index, save_to_notion=save)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
