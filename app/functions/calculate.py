from requests.models import REDIRECT_STATI, HTTPError
from riotwatcher import LolWatcher
from riotwatcher._apis.league_of_legends.SummonerApiV4 import SummonerApiV4
from riotwatcher._apis.league_of_legends.MatchApiV5 import MatchApiV5
import app.functions.functions as fun
import time as t

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

    fun.getTier(summonerDTO, resultSet) #티어와 디비전 먼저 세팅

    for i in range(len(matchInfos)) :

        # 이번 판의 길이를 알아내기 위한 부분
        # 나누는 부분이 if, else로 나눠져있는 이유는 11.21패치 이전에 실행된 게임들에 대해서는 시간 단위가 ms, 이후에는 s이기 때문.
        gameDuration = matchInfos[i]['info']['gameDuration']
        if (gameDuration > 100000) :
            gameDuration /= 60000
        else :
            gameDuration /= 60

        # 게임 길이를 구했다면 반올림 후 적용한다.
        gameDuration = round(gameDuration, 1)
        resultSet['gameDuration'].append(gameDuration)        

        # 이번 판의 트롤력 계산을 위한 0점짜리 추가
        resultSet['trollScore'].append(0)

        userLoc = fun.getUserLoc(matchInfos[i], summonerDTO['name'])
        resultSet['win'].append(matchInfos[i]['info']['participants'][userLoc]['win'])

        #사용한 챔피언명 구하는 부분
        resultSet['championName'].append(matchInfos[i]['info']['participants'][userLoc]['championName'])

        #게임에서의 영문 포지션명 구하는 부분
        resultSet['teamPosition'].append(matchInfos[i]['info']['participants'][userLoc]['teamPosition'])

        #영문 포지션명을 한글로 변환
        resultSet['teamPositionKR'].append(fun.getPositionKR(resultSet['teamPosition'][i]))

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
                    raise Exception
        except Exception :
            continue

        # 처음 보는 챔피언이면 새로운 목록 추가
        resultSet['trollScorePerChampion'].append( {
            "championName" : resultSet['championName'][i],
            "trollScore" : resultSet['trollScore'][i]
        })

    resultSet['totalScore'] = round(resultSet['totalScore'], 1)


    # 매 판 승리했는지의 여부를 토대로 winCount값 설정
    for i in range(len(resultSet['win'])) :
        if resultSet['win'][i] :
            resultSet['winCount'] += 1

    # 제일 트롤력이 높은 챔피언 3개 정도만 우선 출력하기 위해 trollScorePerChampion을 정렬
    resultSet['trollScorePerChampion'] = sorted(resultSet['trollScorePerChampion'], key = (lambda x : x['trollScore']), reverse = True)

    target.append(resultSet)