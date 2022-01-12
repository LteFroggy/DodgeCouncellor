from requests.models import REDIRECT_STATI, HTTPError
from riotwatcher import LolWatcher
from riotwatcher._apis.league_of_legends.SummonerApiV4 import SummonerApiV4
from riotwatcher._apis.league_of_legends.MatchApiV5 import MatchApiV5
from werkzeug.datastructures import Range
import app.functions.functions as fun
import time
import json
import os

DeathKingScore = 20
NoItemScore = 10
BadSpellScore = 10
DamageDiffWeight = 1
GoldDiffWeight = 1
visionScoreWeight = 1

def calculateScorePerUser(userName, target) :
    summonerDTO = fun.getSummonerInfo(userName)
    matchList = fun.getMatchBySummonerDTO(summonerDTO, 20)
    matchInfos = fun.getMatchInfoByMatchID(matchList)

    resultSet = {
        "gameCount" : 0,
        "userName" : userName,
        "tier" : "",
        "division" : "",
        "championName" : [],
        "gameDuration" : [],
        "teamPosition" : [],
        "teamPositionKR" : [],
        "deathKingScore" : 0,
        "badItemScore" : 0,
        "badSpellScore" : 0,
        "weakDamageScore" : 0,
        "lackGoldScore" : 0,
        "visionLowScore" : 0,
        "win" : [],
        "winCount" : 0,
        "trollScorePerChampion" : [],
        "trollScore" : [],
        "totalScore" : 0
    }

    # 티어와 디비전 먼저 세팅
    fun.getTier(summonerDTO, resultSet) 

    # 구해온 게임 횟수를 gameCount에 저장
    resultSet['gameCount'] = len(matchInfos)

    # 필요한 파일이 존재하는지 확인한다.
    filePath = "../static/data" + resultSet['tier'] + " " + resultSet['division'] + "result.json"
    try :
        with open(filePath, 'r', encoding = 'utf-8') as file :
            data = json.dump(file)
    except :
        data = False

    for i in range(len(matchInfos)) :
        # 게임 길이를 먼저 입력한다
        resultSet['gameDuration'].append(fun.getGameLength(matchInfos[i]))

        # 이번 판의 트롤력 계산을 위한 0점짜리 추가
        resultSet['trollScore'].append(0)
        
        # 유저의 게임 내에서의 위치 구하기
        userLoc = fun.getUserLoc(matchInfos[i], summonerDTO['name'])

        # 승리 여부 넣기
        resultSet['win'].append(matchInfos[i]['info']['participants'][userLoc]['win'])        

        #사용한 챔피언명 구하는 부분
        resultSet['championName'].append(matchInfos[i]['info']['participants'][userLoc]['championName'])

        #게임에서의 영문 포지션명 구하는 부분
        resultSet['teamPosition'].append(matchInfos[i]['info']['participants'][userLoc]['teamPosition'])

        #영문 포지션명을 한글로 변환
        resultSet['teamPositionKR'].append(fun.getPositionKR(resultSet['teamPosition'][i]))

        ememyLoc = fun.getEnemyLocation(matchInfos[i], userLoc)
        enemyChampion = matchInfos[i]['info']['participants'][ememyLoc]['championName']

        # 트롤력 계산 시 data가 존재하는지 먼저 확인
        try :
            # data가 없다면 KeyError 발생시키기
            if not(data) :
                raise KeyError

            # 사용할 데이터 찾기
            positionName = resultSet['teamPosition'][i]
            for number in range(len(data[positionName])) :
                if data[positionName][number]['championName'] == resultSet['championName'][i] and data[positionName][number]['enemyChampionName'] == enemyChampion :
                    data = data['positionName'][number]
                    break
            
            # 사용할 데이터의 크기 확인 후 5 이하면 사용하지 않음(객관성을 위해)
            if data['gameCount'] <= 5 :
                raise KeyError


            ''' 데이터를 이용하여 트롤력을 측정하는 부분 '''

            #DeathKing 구하는 부분
            if (fun.DeathKing(matchInfos[i], userLoc)) :
                resultSet['trollScore'][i] += DeathKingScore
                resultSet['deathKingScore'] += DeathKingScore

            #noItem 구하는 부분
            if (fun.buySameItems(matchInfos[i], userLoc)) :
                resultSet['trollScore'][i] += NoItemScore
                resultSet['badItemScore'] += NoItemScore

            #badSpell 구하는 부분
            if (not(fun.UseCorrectSpell(matchInfos[i], userLoc))) :
                resultSet['trollScore'][i] += BadSpellScore
                resultSet['badSpellScore'] += BadSpellScore
            
            #딜량 차이 구하는 부분
            damageDiff = fun.damageDiffWithData(matchInfos[i], userLoc, data)
            if (damageDiff != 0) :
                resultSet['trollScore'][i] += (damageDiff * DamageDiffWeight)
                resultSet['weakDamageScore'] += (damageDiff * DamageDiffWeight)

            #골드 차이 구하는 부분
            goldDiff = fun.goldDiffWithData(matchInfos[i], userLoc, data)
            if (goldDiff != 0) :
                resultSet['trollScore'][i] += (goldDiff * GoldDiffWeight)
                resultSet['lackGoldScore'] += (goldDiff * GoldDiffWeight)

            #시야점수 차이 구하는 부분
            visionDiff = fun.vScoreDiffWithData(matchInfos[i], userLoc, data)
            if (visionDiff != 0) :
                resultSet['trollScore'][i] += (visionDiff * visionScoreWeight)
                resultSet['visionLowScore'] += (visionDiff * visionScoreWeight)

            resultSet['trollScore'][i] = round(resultSet['trollScore'][i], 1)

            resultSet['totalScore'] += resultSet['trollScore'][i]


        except KeyError :     

            ''' 상대 플레이어와의 격차를 이용해서 트롤력을 측정하는 부분 '''  

            #DeathKing 구하는 부분
            if (fun.DeathKing(matchInfos[i], userLoc)) :
                resultSet['trollScore'][i] += DeathKingScore
                resultSet['deathKingScore'] += DeathKingScore

            #noItem 구하는 부분
            if (fun.buySameItems(matchInfos[i], userLoc)) :
                resultSet['trollScore'][i] += NoItemScore
                resultSet['badItemScore'] += NoItemScore

            #badSpell 구하는 부분
            if (not(fun.UseCorrectSpell(matchInfos[i], userLoc))) :
                resultSet['trollScore'][i] += BadSpellScore
                resultSet['badSpellScore'] += BadSpellScore
            
            #딜량 차이 구하는 부분
            damageDiff = fun.damageDiffByPosition(matchInfos[i], userLoc)
            if (damageDiff != 0) :
                resultSet['trollScore'][i] += (damageDiff * DamageDiffWeight)
                resultSet['weakDamageScore'] += (damageDiff * DamageDiffWeight)

            #골드 차이 구하는 부분
            goldDiff = fun.goldDiffByPostion(matchInfos[i], userLoc)
            if (goldDiff != 0) :
                resultSet['trollScore'][i] += (goldDiff * GoldDiffWeight)
                resultSet['lackGoldScore'] += (goldDiff * GoldDiffWeight)

            #시야점수 차이 구하는 부분
            visionDiff = fun.visionScoreDiffByPosition(matchInfos[i], userLoc)
            if (visionDiff != 0) :
                resultSet['trollScore'][i] += (visionDiff * visionScoreWeight)
                resultSet['visionLowScore'] += (visionDiff * visionScoreWeight)

            resultSet['trollScore'][i] = round(resultSet['trollScore'][i], 1)

            resultSet['totalScore'] += resultSet['trollScore'][i]

        # 매 루프마다 챔피언별 트롤력 측정을 위한 계산 추가
        try :
            for k in range(len(resultSet['trollScorePerChampion'])) :
                # 이미 목록에 있는 챔피언이면 챔피언에 값만 추가
                if resultSet['championName'][i] == resultSet['trollScorePerChampion'][k]['championName'] :
                    resultSet['trollScorePerChampion'][k]['trollScore'] += resultSet['trollScore'][i]
                    resultSet['trollScorePerChampion'][k]['gameCount'] += 1
                    raise Exception
        except Exception :
            continue

        # 처음 보는 챔피언이면 새로운 목록 추가
        resultSet['trollScorePerChampion'].append( {
            "championName" : resultSet['championName'][i],
            "trollScore" : resultSet['trollScore'][i],
            "gameCount" : 1
        })

    resultSet['totalScore'] = round(resultSet['totalScore'], 1)


    # 매 판 승리했는지의 여부를 토대로 winCount값 설정
    for i in range(len(resultSet['win'])) :
        if resultSet['win'][i] :
            resultSet['winCount'] += 1

    # 판수를 적용해서 챔프별 트롤력 재정리
    for k in range(len(resultSet['trollScorePerChampion'])) :
        resultSet['trollScorePerChampion'][k]['trollScore'] /= resultSet['trollScorePerChampion'][k]['gameCount']
        resultSet['trollScorePerChampion'][k]['trollScore'] = round(resultSet['trollScorePerChampion'][k]['trollScore'], 1)
    # 제일 트롤력이 높은 챔피언 3개 정도만 우선 출력하기 위해 trollScorePerChampion을 정렬
    resultSet['trollScorePerChampion'] = sorted(resultSet['trollScorePerChampion'], key = (lambda x : x['trollScore']), reverse = True)

    target.append(resultSet)