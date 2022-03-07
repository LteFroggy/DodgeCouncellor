import datetime
import json
date = datetime.datetime.now().date()
filePath = 'app/static/data/searchResult.json'


def getCount() :
    # 날짜별 검색 횟수를 표시하는 함수 열기
    try :
        with open(filePath, 'r', encoding = 'utf-8') as file :
            countData = json.load(file)
        for i in range(len(countData)) :
            # 해당하는 날짜의 데이터가 이미 있다면 끝내기
            if countData[i]['date'] == str(date) :
                return countData[i]['count']
    except :
        countData = []
        countData.append( {
            "date" : str(date),
            "count" : 0
        })
        with open(filePath, 'w', encoding = 'utf-8') as outFile :
            json.dump(countData, outFile, ensure_ascii = False, indent = 4)
            outFile.close
        return 0

        


# 오늘 날짜의 검색된 횟수를 1 증가시키는 함수
def plusCount() :
        with open(filePath, 'r', encoding = 'utf-8') as file :
            countData = json.load(file)
        # 찾았다면 값을 1 증가시키고 종료
        for i in range(len(countData)) :
            if countData[i]['date'] == str(date) :
                countData[i]['count'] += 1
                with open(filePath, 'w', encoding = 'utf-8') as outFile :
                    json.dump(countData, outFile, ensure_ascii = False, indent = 4)
                    outFile.close
                break
        
        

            

