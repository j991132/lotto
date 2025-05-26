import requests
from bs4 import BeautifulSoup
import csv

def get_lotto_numbers(draw_no):
    api_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()
        print(f"{draw_no}회 결과추출")
        # Request 데이터 출력
        return {
            'drwNo' : data['drwNo'],
            'date': data['drwNoDate'], 
            'lottoNumb': [str(data[f"drwtNo{i}"]) for i in range(1, 7)], 
            'bonusNumb': data['bnusNo']
        }
        
        
    except requests.exceptions.RequestException as e:
        print(f"오류가 발생했습니다: {e}")
        
def maxRound():
    url = "https://dhlottery.co.kr/common.do?method=main"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "lxml")
    max_numb = soup.find(name="strong", attrs={"id": "lottoDrwNo"}).text
    return int(max_numb)

        
# 최신 회차 가져오기
maxCount = maxRound()
draw_no  = 1

# CSV 파일 쓰기
with open('lottoRes.csv', 'w', newline='') as csvfile:
    # CSV 파일 쓰기
    writer = csv.writer(csvfile, delimiter=',')
    
    # 1화부터 최신화까지 크롤링
    for draw_no in range(1, maxCount+1):
        res = get_lotto_numbers(draw_no)
        # 순서 : 회차, 날짜, 로또번호1, 로또번호2, 로또번호3, 로또번호4, 로또번호5, 로또번호6, 보너스번호
        writer.writerow([res.get('drwNo'), res.get('date')] + res.get('lottoNumb') + [res.get('bonusNumb')])
출처: https://dalseobi.tistory.com/159 [달에 앉아있는 서비:티스토리]
