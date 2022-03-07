from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask import current_app as app
from flask import request
from flask import Flask
import app.functions.calculate as cal
import app.functions.functions as fun
import app.functions.countCheck as dateFun
import time
import threading
import jinja2
from requests.models import HTTPError
# 추가할 모듈이 있다면 추가

app = Flask(__name__)
app.secret_key = 'myKey'
main= Blueprint('main', __name__, url_prefix='/')

'''
입력 예시입니다
미미또또님이 로비에 참가하셨습니다.
흑백화님이 로비에 참가하셨습니다.
보라돌이 앙앙님이 로비에 참가하셨습니다.
우물쭈물대지마라님이 로비에 참가하셨습니다.
Darius ever only님이 로비에 참가하셨습니다.
'''

'''
fun.calcualteScorePerUser함수가 반환하는 결과입니다!
    resultSet = {
        "gameCount" : 0,
        "userName" : userName,
        "tier" : "",
        "division" : "",
        "championName" : [],
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
        "trollScorePerChampion" : [{
            "championName" : "",
            "trollScore" : 0
        }],
        "trollScore" : [],
        "totalScore" : 0
    }
'''

@main.route('/', methods = ['GET'])
def mainPage() :
    count = dateFun.getCount()
    print("검색 횟수 :", count)
    return render_template('mainPage.html', searchCount = count)


@main.route('/guide', methods = ['GET'])
def guidePage() :
    return render_template('guide.html')


@main.route('/solo', methods = ['POST'])
def soloUserInfo() :
    userName = request.form["userName"]
    info = []

    try :
        cal.calculateScorePerUser(userName, info)

        dateFun.plusCount()
        return render_template('/result.html', result = info, length = 1)
    except HTTPError as e:
        if (str(e)[0:3] == "404") :
            flash("소환사 이름을 제대로 입력해주세요")
            return render_template('/mainPage.html')

        elif (str(e)[0:3] == "403") :
            flash("Riot 서버 오류입니다")
            return render_template('/mainPage.html')

        else :
            flash("HTTPError 발생 : " + str(e))
            return render_template('/mainPage.html')

    except IndexError as e:
        flash("충분한 횟수의 랭크 게임을 플레이하지 않은 유저가 존재합니다.")
        return render_template('/mainPage.html')


@main.route('/search', methods = ['POST'])
def homePage():
    inputData = request.form["identification"]
    userNames = fun.nameSlice(inputData)

    try :
        infoList = []
        threads = []
        averageScore = 0
        for id in userNames :
            t = threading.Thread(target = cal.calculateScorePerUser, args = (id, infoList))
            t.start()
            threads.append(t)

        for t in threads :
            t.join()

        for i in range(len(infoList)) :
            averageScore += infoList[i]['totalScore']
        
        averageScore /= len(infoList)
        averageScore = round(averageScore, 1)


        dateFun.plusCount()
        return render_template('/result.html', result = infoList, averageScore = averageScore, length = 5)

    except HTTPError as e:
        if (str(e)[0:3] == "404") :
            flash("유저명이 잘못 입력되었습니다. 채팅창 입장 대화를 다시 입력해주세요")
            return render_template('/mainPage.html') 

        elif (str(e)[0:3] == "403") :
            flash("Riot 서버 오류입니다")
            return render_template('/mainPage.html')

        else :
            flash("HTTPError 발생 : " + str(e))
            return render_template('/mainPage.html')

    except jinja2.exceptions.UndefinedError as e :
        flash("충분한 횟수의 랭크 게임을 플레이하지 않은 유저가 존재합니다.")
        return render_template('/mainPage.html')