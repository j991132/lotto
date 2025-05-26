import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def crawl_lotto_data_to_csv():
    """
    동행복권 웹사이트에서 로또 1회차부터 최신 회차까지의 당첨번호를 크롤링하여
    'lotto_winning_numbers.csv' 파일로 저장합니다.
    """
    
    base_url = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
    all_data = []

    # 최신 회차 번호를 가져오는 로직
    try:
        print("최신 회차 번호를 가져오는 중...")
        response = requests.get(base_url + "1", timeout=10) # 임의의 회차로 최신 회차 번호 파싱
        response.raise_for_status() # HTTP 오류가 발생하면 예외 발생
        soup = BeautifulSoup(response.text, 'html.parser')
        latest_drw_no_str = soup.find('strong', class_='drwNo').text
        latest_drw_no = int(latest_drw_no_str)
        print(f"최신 회차 번호: {latest_drw_no}")
    except requests.exceptions.RequestException as e:
        print(f"최신 회차 번호를 가져오는 데 실패했습니다: {e}")
        print("기본값 1122회차까지 크롤링을 시도합니다. (실패 시 수동 업데이트 필요)")
        latest_drw_no = 1122 # 실패 시 임의의 최신 회차

    print(f"1회차부터 {latest_drw_no}회차까지 로또 당첨 번호를 크롤링합니다...")

    for drw_no in range(1, latest_drw_no + 1):
        url = base_url + str(drw_no)
        try:
            response = requests.get(url, timeout=5) # 5초 타임아웃
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            numbers = []
            for i in range(1, 7):
                num_tag = soup.find('span', class_=f'drw no{i}')
                if num_tag:
                    numbers.append(int(num_tag.text))
                else:
                    raise ValueError(f"{drw_no}회차 번호{i} 태그를 찾을 수 없습니다.")
            
            bonus_num_tag = soup.find('span', class_='drwBonus no7')
            if bonus_num_tag:
                bonus_num = int(bonus_num_tag.text)
            else:
                raise ValueError(f"{drw_no}회차 보너스 번호 태그를 찾을 수 없습니다.")

            date_str_tag = soup.find('p', class_='desc')
            if date_str_tag:
                date_str = date_str_tag.text.split('(')[0].strip()
            else:
                raise ValueError(f"{drw_no}회차 날짜 태그를 찾을 수 없습니다.")
            
            all_data.append({
                '회차': drw_no,
                '날짜': date_str,
                '번호1': numbers[0],
                '번호2': numbers[1],
                '번호3': numbers[2],
                '번호4': numbers[3],
                '번호5': numbers[4],
                '번호6': numbers[5],
                '보너스번호': bonus_num,
                '당첨번호_리스트': sorted(numbers) # 분석을 위해 정렬된 리스트로 저장
            })
            
            if drw_no % 100 == 0: # 100회차마다 진행 상황 출력
                print(f"{drw_no}회차까지 크롤링 완료...")

        except requests.exceptions.RequestException as req_err:
            print(f"경고: {drw_no}회차 데이터 요청 중 오류 발생 (네트워크 또는 서버): {req_err}")
            # 이 경우 해당 회차 데이터는 스킵하고 다음 회차로 진행
        except (AttributeError, ValueError) as parse_err:
            print(f"경고: {drw_no}회차 데이터 파싱 중 오류 발생 (사이트 구조 변경?): {parse_err}")
            # 이 경우 해당 회차 데이터는 스킵하고 다음 회차로 진행
        except Exception as e:
            print(f"경고: {drw_no}회차 데이터를 가져오는 중 알 수 없는 오류 발생: {e}")
            # 이 경우 해당 회차 데이터는 스킵하고 다음 회차로 진행
        
        time.sleep(0.1) # 서버 과부하 방지를 위해 짧은 지연 시간 추가

    if all_data:
        df = pd.DataFrame(all_data)
        df['날짜'] = pd.to_datetime(df['날짜'])
        # '당첨번호_리스트' 컬럼은 CSV 저장 시 문자열로 변환됩니다.
        # 추후 불러올 때 ast.literal_eval 등으로 다시 리스트로 변환 필요할 수 있음
        df.to_csv('lotto_winning_numbers.csv', index=False, encoding='utf-8-sig')
        print(f"\n✅ 로또 당첨 번호 데이터를 'lotto_winning_numbers.csv' 파일로 성공적으로 저장했습니다.")
        print(f"총 {len(df)}개의 회차 데이터가 저장되었습니다.")
    else:
        print("\n❌ 크롤링된 데이터가 없습니다. CSV 파일을 생성할 수 없습니다.")

if __name__ == "__main__":
    crawl_lotto_data_to_csv()
