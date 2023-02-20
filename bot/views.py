from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

import pandas as pd
import random
# Create your views here.

from linebot import LineBotApi, WebhookHandler, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, TextMessage, ImageSendMessage, StickerSendMessage, LocationSendMessage


line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parse = WebhookParser(settings.LINE_CHANNEL_SECRET)


def index(requests):
    return HttpResponse('<h1>LINEBOT APP</h1>')


@csrf_exempt
def callback(request):
    keywords = {'words': ['哪條街或周邊景點呢？', '再請您輸入地址or景點！！',
                          '越詳細地址越好唷，前面不用加台北市唷～', '快給我其他資訊!要不然怎麼幫你找？？？', '今天想要減肥嗎，給我更我多資訊幫你找哪裡有ubike唷！！'],
                'area': [
                    '中山區，中正區，信義區，內湖區，\n北投區，南港區，士林區，大同區，\n大安區，文山區，松山區，臺大公館校區，\n臺大專區，萬華區', '想要找哪個區域呢？？']
                }

    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parse.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        for event in events:
            if isinstance(event, MessageEvent):
                if isinstance(event.message, TextMessage):
                    text = event.message.text
                    if '使用' in text or '說明' in text:
                        sendText(
                            '歡迎使用ubike bot！\n查找規則:\n欲查找站點請先輸入區域(輸入區域即可查看)，不需要打"台北市" ，再輸入欲查找站點即可查詢\n如不確定是在哪裡，可以在輸入完區域後再輸入 "街" or "路" \n完感謝您的使用！！', event)
                    elif '區域' in text:
                        messages = [TextSendMessage(text)
                                    for text in keywords['area']]
                        line_bot_api.reply_message(event.reply_token, messages)
                    elif text == '中山區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        zhongshan()
                    elif text == '中正區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        zhongzheng()
                    elif text == '信義區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        xinyi()
                    elif text == '內湖區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        neihu()
                    elif text == '北投區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        beitou()
                    elif text == '南港區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        nangang()
                    elif text == '士林區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        shilin()
                    elif text == '大同區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        datong()
                    elif text == '大安區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        daan()
                    elif text == '文山區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        wenshan()
                    elif text == '松山區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        songshan()
                    elif '臺大專區' in text or '台大專區' in text or text == '臺大專區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        ntu()
                    elif '臺大公館校區' in text or '公館校區' in text:
                        send_data = ntu_gongguan()
                        messages = LocationSendMessage(
                            send_data[0][0], send_data[0][1], send_data[0][2], send_data[0][3]), TextSendMessage(f'更新時間：{send_data[0][6]} 目前車輛數量：{send_data[0][4]} 空位數量：{send_data[0][5]}')
                        line_bot_api.reply_message(event.reply_token, messages)
                    elif text == '萬華區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        wanhua()
                    else:
                        ai(text, event, line_bot_api)

                else:
                    sendText('無法辨識！', event)

        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def sendText(message, event):
    message = TextSendMessage(text=message)
    line_bot_api.reply_message(event.reply_token, message)


def sendImage(img_url, event):
    try:
        message = ImageSendMessage(original_content_url=img_url,
                                   preview_image_url=img_url)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='傳送失敗!'))


def sendSticker(p_id, s_id, event):
    try:
        message = StickerSendMessage(package_id=p_id,
                                     sticker_id=s_id)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='傳送失敗!'))


def sendLocation(sna, ar, lat, lng, event):
    try:
        message = LocationSendMessage(title=sna,
                                      address=ar,
                                      latitude=lat,
                                      longitude=lng)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='傳送失敗!'))


def analyze_area_data():
    api_url = 'https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json'
    df = pd.read_json(api_url)
    df1 = df[df['act'] == 1]
    columns = 'sarea sna ar lat lng tot sbi bemp mday'.split()
    ubike_data = df1[columns]
    ubike_data = ubike_data.rename(columns={
                                   'sarea': '區域', 'tot': '總車位數', 'sbi': '目前車輛數量', 'bemp': '空位數量', 'mday': '更新時間'})

    ubike_data = ubike_data.sort_values('目前車輛數量', ascending=False)
    datas = ubike_data.values.tolist()
    return datas


def get_data(datas, name, area_dict):
    global send_data
    for i in datas:
        if name in i[0]:
            area_dict[i[1]] = i[2:]
    send_data = []
    for i in area_dict.items():
        title = i[0]
        ar = i[1][0]
        lat = i[1][1]
        lng = i[1][2]
        have_ubike = str(i[1][-3])
        empty = str(i[1][-2])
        updatetime = i[1][-1]
        # print(title,ar,lat,lng)
        send_data.append([title, ar, lat, lng, have_ubike, empty, updatetime])
    return send_data


def zhongshan():
    datas = analyze_area_data()
    area_dict = {}
    name = '中山'
    send_data = get_data(datas, name, area_dict)
    return send_data


def zhongzheng():
    datas = analyze_area_data()
    area_dict = {}
    name = '中正'
    send_data = get_data(datas, name, area_dict)
    return send_data


def xinyi():
    datas = analyze_area_data()
    area_dict = {}
    name = '信義'
    send_data = get_data(datas, name, area_dict)
    return send_data


def neihu():
    datas = analyze_area_data()
    area_dict = {}
    name = '內湖'
    send_data = get_data(datas, name, area_dict)
    return send_data


def beitou():
    datas = analyze_area_data()
    area_dict = {}
    name = '北投'
    send_data = get_data(datas, name, area_dict)
    return send_data


def nangang():
    datas = analyze_area_data()
    area_dict = {}
    name = '南港'
    send_data = get_data(datas, name, area_dict)
    return send_data


def shilin():
    datas = analyze_area_data()
    area_dict = {}
    name = '士林'
    send_data = get_data(datas, name, area_dict)
    return send_data


def datong():
    datas = analyze_area_data()
    area_dict = {}
    name = '大同'
    send_data = get_data(datas, name, area_dict)
    return send_data


def daan():
    datas = analyze_area_data()
    area_dict = {}
    name = '大安'
    send_data = get_data(datas, name, area_dict)
    return send_data


def wenshan():
    datas = analyze_area_data()
    area_dict = {}
    name = '文山'
    send_data = get_data(datas, name, area_dict)
    return send_data


def songshan():
    datas = analyze_area_data()
    area_dict = {}
    name = '松山'
    send_data = get_data(datas, name, area_dict)
    return send_data


def ntu_gongguan():
    datas = analyze_area_data()
    area_dict = {}
    name = '臺大公館'
    send_data = get_data(datas, name, area_dict)
    return send_data


def ntu():
    datas = analyze_area_data()
    area_dict = {}
    name = '臺大專區'
    send_data = get_data(datas, name, area_dict)
    return send_data


def wanhua():
    datas = analyze_area_data()
    area_dict = {}
    name = '萬華'
    send_data = get_data(datas, name, area_dict)
    return send_data


def ai(text, event, line_bot_api):
    try:
        if send_data is not None or send_data != []:
            # print(text)
            data2 = [data for data in send_data if text in data[0]
                     or text in data[1]]
            if len(data2) == 0:
                messages = (TextSendMessage('您所找的地方/景點未搜尋到此站點名稱，請確認後再重新輸入！'))
            elif len(data2) == 1:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'{data2[0][0]}\n 更新時間：{data2[0][6]} \n目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}')
            elif len(data2) == 2:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'{data2[0][0]}\n 更新時間：{data2[0][6]} \n目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}'), LocationSendMessage(
                    data2[1][0], data2[1][1], data2[1][2], data2[1][3]), TextSendMessage(f'{data2[1][0]}\n 更新時間：{data2[1][6]} \n目前車輛數量：{data2[1][4]} 空位數量：{data2[1][5]}')
            else:
                data3 = [
                    f'*您所查詢的: {text} 共有{len(data2)}個站點', f'*欲想查詢地圖位置，可輸入該站點名稱(如:{data2[0][0][11:]}，{data2[1][0][11:]}...)！！']
                for i in data2:
                    data3.append(i[0] + '\n' + ' 目前車輛數量為 :' +
                                 str(i[-3]) + ' 空位數量為 : ' + str(i[-2]))
                messages = TextSendMessage('\n\n'.join(data3))
            line_bot_api.reply_message(event.reply_token, messages)
            return
    except:
        message = TextSendMessage(
            text='請注意地址/景點是否正確唷，例如: "臺"跟"台"的差別，也請您從區域開始查找，再請您試一次，拜託～～～～')
        line_bot_api.reply_message(event.reply_token, message)
