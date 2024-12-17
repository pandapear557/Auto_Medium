import json
import requests
import re
import urllib
from utils import Utils 
from bs4 import BeautifulSoup

#람다 함수를 실행을 위한 핸들러 함수    
def lambda_handler(event, context): 
    result = Mail_Crawler(event, context).medium_crawler()
    return {
            'statusCode' : 200,
            "headers": {
                "Content-Type": "application/json"
            },
		    'body' : json.dumps(result)
            }


class Mail_Crawler:
    def __init__(self, data, context):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.origin_url = data
        self.title = []
        self.txt = []
    
    def medium_crawler_single_instance(self, index):
        """
        요청마다 하나의 URL을 처리하고 결과 반환
        """
        except_list = ["·Member", "Edit who you follow", "Control your recommendations", "·Terms of service"]

        # 유효한 인덱스인지 확인
        if index < 0 or index >= len(self.origin_url):
            return {
                'statusCode': 400,
                'body': f"Invalid index {index}. Must be between 0 and {len(self.origin_url) - 1}."
            }

        # URL 생성
        url = Utils().make_url(self.origin_url, index)

        # 예외 처리 목록 확인
        if url[0] in except_list:
            return {
                'statusCode': 204,
                'body': f"Skipped URL {url[1]} (in except list)."
            }

        try:
            # 요청 및 HTML 파싱
            req = urllib.request.Request(url[1], headers=self.headers)
            soup = BeautifulSoup(urllib.request.urlopen(req).read(), "html.parser")

            # 제목 및 본문 추출
            title = soup.select_one("h1").get_text() if soup.select_one("h1") else "No Title Found"
            paragraphs = soup.select(".pw-post-body-paragraph")
            text = "\n".join([paragraph.get_text() for paragraph in paragraphs]) if paragraphs else "No Paragraph Found"

            # 결과 반환
            return {
                'statusCode': 200,
                'body': {
                    'url': url[1],
                    'title': title,
                    'text': text
                }
            }

        except Exception as e:
            # 오류 처리
            return {
                'statusCode': 500,
                'body': f"Failed to parse URL {url[1]}: {str(e)}"
            }
  

def main():
    # 로컬 실행을 위한 테스트 이벤트
    with open("mail.txt", "r", encoding="utf-8") as file:
        data = file.read()  
    context = None

    result = Mail_Crawler(data, context).medium_crawler_single_instance(3)
    print(json.dumps(result, indent=4))
    
if __name__ == "__main__":
    main()