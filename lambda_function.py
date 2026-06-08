"""AWS Lambda 진입점.

기대 입력 (event 또는 event["body"]):
    { "text": "<메일 본문>", "index": <선택, 정수>, "save_to_notion": <선택, bool> }

index 가 있으면 해당 글 1건, 없으면 전체를 크롤링한다.
save_to_notion 이 true 면 Notion 에도 저장한다 (NOTION_* 환경변수 필요).
"""

import json
import logging

from auto_medium.pipeline import run

logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    # API Gateway 는 본문을 event["body"] 문자열로 전달한다.
    body = event
    if isinstance(event, dict) and isinstance(event.get("body"), str):
        body = json.loads(event["body"])

    mail_text = body["text"]
    index = body.get("index")
    save_to_notion = bool(body.get("save_to_notion", False))

    results = run(
        mail_text,
        index=int(index) if index is not None else None,
        save_to_notion=save_to_notion,
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(results, ensure_ascii=False),
    }
