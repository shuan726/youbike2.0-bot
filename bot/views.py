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
    global send_data
    keywords = {'words': ['哪條路或周邊景點呢？', '請您輸入地址or景點！！',
                          '越詳細地址越好唷(我只能找前五個QQ)，前面不用加台北市唷～', '快給我地址!要不然怎麼幫你找？？？', '地址的英文是address，但我看不懂英文地址唷～'],
                'area': [
                    '中山區，中正區，信義區，內湖區，北投區，南港區，士林區，大同區，大安區，文山區，松山區，臺大公館校區，臺大專區，萬華區', '想要找什麼區域呢？？']
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
                    if '區域' in text:
                        messages = [TextSendMessage(text)
                                    for text in keywords['area']]
                        line_bot_api.reply_message(event.reply_token, messages)
                    elif text == '中山區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = zhongshan()
                    elif text == '中正區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = zhongzheng()
                    elif text == '信義區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = xinyi()
                    elif text == '北投區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = beitou()
                    elif text == '南港區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = nangang()
                    elif text == '士林區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = shilin()
                    elif text == '大同區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = datong()
                    elif text == '大安區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = daan()
                    elif text == '文山區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = wenshan()
                    elif text == '松山區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = songshan()
                    elif '臺大' in text or '台大' in text:
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = ntu()
                        if '公館' in text:
                            message = random.choice(keywords['words'])
                            sendText(message, event)
                            send_data = ntu_gongguan()
                    elif text == '萬華區':
                        message = random.choice(keywords['words'])
                        sendText(message, event)
                        send_data = wanhua()
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
    columns = 'mday sarea sna ar lat lng tot sbi bemp'.split()
    ubike_data = df1[columns]
    ubike_data = ubike_data.rename(columns={
                                   'mday': '更新時間', 'sarea': '區域', 'tot': '總車位數', 'sbi': '目前車輛數量', 'bemp': '空位數量'})

    ubike_data = ubike_data.sort_values('目前車輛數量', ascending=False)
    datas = ubike_data.values.tolist()
    return datas


def get_data(datas, name, area_dict):
    for i in datas:
        if name in i[1]:
            area_dict[i[2]] = i[3:]
    send_data = []
    for i in area_dict.items():
        title = i[0]
        ar = i[1][0]
        lat = i[1][1]
        lng = i[1][2]
        have_ubike = str(i[1][-2])
        empty = str(i[1][-1])
        # print(title,ar,lat,lng)
        send_data.append([title, ar, lat, lng, have_ubike, empty])
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
            print(text)
            data2 = [data for data in send_data if text in data[0]
                     or text in data[1]]
            if len(data2) == 1:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}')
            elif len(data2) == 2:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}'), LocationSendMessage(
                    data2[1][0], data2[1][1], data2[1][2], data2[1][3]), TextSendMessage(f'目前車輛數量：{data2[1][4]} 空位數量：{data2[1][5]}')
            elif len(data2) == 3:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}'), LocationSendMessage(
                    data2[1][0], data2[1][1], data2[1][2], data2[1][3]), TextSendMessage(f'目前車輛數量：{data2[1][4]} 空位數量：{data2[1][5]}'), LocationSendMessage(
                    data2[2][0], data2[2][1], data2[2][2], data2[2][3])
            elif len(data2) == 4:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}'), LocationSendMessage(
                    data2[1][0], data2[1][1], data2[1][2], data2[1][3]), LocationSendMessage(
                    data2[2][0], data2[2][1], data2[2][2], data2[2][3]), LocationSendMessage(
                    data2[3][0], data2[3][1], data2[3][2], data2[3][3])
            elif len(data2) >= 5:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), LocationSendMessage(
                    data2[1][0], data2[1][1], data2[1][2], data2[1][3]), LocationSendMessage(
                    data2[2][0], data2[2][1], data2[2][2], data2[2][3]), LocationSendMessage(
                    data2[3][0], data2[3][1], data2[3][2], data2[3][3]), LocationSendMessage(
                    data2[4][0], data2[4][1], data2[4][2], data2[4][3])
            line_bot_api.reply_message(event.reply_token, messages)
            return
    except:
        message = TextSendMessage(
            text='請注意地址是否正確唷，例如: "臺"跟"台"的差別，再請您試一次，拜託～～～～')
        line_bot_api.reply_message(event.reply_token, message)
