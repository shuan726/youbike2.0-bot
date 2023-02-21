from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

import pandas as pd
import random
from haversine import haversine, Unit
# Create your views here.

from linebot import LineBotApi, WebhookHandler, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, TextMessage, LocationSendMessage, LocationMessage


line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parse = WebhookParser(settings.LINE_CHANNEL_SECRET)


def index(requests):
    return HttpResponse('<h1>LINEBOT APP</h1>')


@csrf_exempt
def callback(request):
    keywords = {'words': ['哪條街或周邊景點呢？', '再請您輸入地址or景點！！',
                          '越詳細地址越好唷，前面不用加台北市唷～', '快給我其他資訊!要不然怎麼幫你找???', '今天想要減肥嗎，給我更我多資訊幫你找哪裡有ubike唷！！'],
                '台北市': [
                    '中山區，中正區，信義區，內湖區，\n北投區，南港區，士林區，大同區，\n大安區，文山區，松山區，臺大公館校區，\n臺大專區，萬華區', '想要找哪個區域呢？？'],
                '新北市': [
                    '瑞芳區，三芝區，金山區，深坑區，\n三峽區，鶯歌區，淡水區，永和區，\n泰山區，板橋區，中和區，樹林區，\n萬里區，五股區，八里區，汐止區，\n石門區，石碇區，土城區，新莊區，\n三重區，坪林區，新店區，蘆洲區，\n林口區，猴雙公共自行車專區', '想要找哪個區域呢？？']
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
                            '歡迎使用ubike bot！\n查找規則:\n可輸入附近，並傳送個人位置訊息\n目前只能用拖曳的方式定位(打字在line map無法使用)\n欲查找站點請先輸入區域(如：台北 或 新北)\n可查看詳細行政區， \n再輸入欲查找行政區即可查詢，\n感謝您的使用！！', event)
                    elif text == '台北市' or text == '臺北市' or text == '臺北' or text == '台北':
                        messages = [TextSendMessage(text)
                                    for text in keywords['台北市']]
                        line_bot_api.reply_message(event.reply_token, messages)
                    elif text == '新北市' or text == '新北':
                        messages = [TextSendMessage(text)
                                    for text in keywords['新北市']]
                        line_bot_api.reply_message(event.reply_token, messages)
                    elif text in keywords['新北市'][0].replace(
                            '\n', '').replace('，', ','):
                        send_data = get_area(text, new_taipei=True)
                        message = random.choice(keywords['words'])
                        sendText(
                            f'{text}共有 {len(send_data)} 個站點 \n如不確定是在哪裡，可輸入附近，傳送個人位置 或 輸入 "街" or "路"查詢 \n{message}', event)

                    elif text in keywords['台北市'][0].replace(
                            '\n', '').replace('，', ','):
                        if '臺大公館校區' in text or '公館校區' in text:
                            send_data = get_area(text)
                            messages = LocationSendMessage(
                                send_data[0][0], send_data[0][1], send_data[0][2], send_data[0][3]), TextSendMessage(f'更新時間：{send_data[0][6]} 目前車輛數量：{send_data[0][4]} 空位數量：{send_data[0][5]}')
                            line_bot_api.reply_message(
                                event.reply_token, messages)
                        else:
                            send_data = get_area(text)
                            message = random.choice(keywords['words'])
                            sendText(
                                f'{text}共有 {len(send_data)} 個站點 \n如不確定是在哪裡，可輸入附近，傳送個人位置 或 輸入 "街" or "路"查詢 \n{message}', event)
                    elif '附近' in text:
                        message = '請先發送個人位置訊息'
                        sendText(message, event)

                    else:
                        ai(text, event, line_bot_api)
                elif isinstance(event.message, LocationMessage):
                    address = event.message.address
                    lat = event.message.latitude
                    lng = event.message.longitude
                    send_data = get_location(
                        address, lat, lng, event, line_bot_api)

                else:
                    sendText('無法辨識！', event)

        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def sendText(message, event):
    message = TextSendMessage(text=message)
    line_bot_api.reply_message(event.reply_token, message)


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


def analyze_area_data(new_taipei_area=False):
    if new_taipei_area:
        api_url = 'https://data.ntpc.gov.tw/api/datasets/010E5B15-3823-4B20-B401-B1CF000550C5/json?page=0&size=1000'
    else:
        api_url = 'https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json'
    df = pd.read_json(api_url)
    df1 = df[df['act'] == 1]
    columns = 'sarea sna ar lat lng tot sbi bemp mday'.split()
    ubike_data = df1[columns]
    ubike_data = ubike_data.rename(columns={
                                   'sarea': '區域', 'tot': '總車位數', 'sbi': '目前車輛數量', 'bemp': '空位數量', 'mday': '更新時間'})
    if new_taipei_area:
        ubike_data['更新時間'] = ubike_data['更新時間'].apply(lambda x: (str(x)))
        ubike_data['更新時間'] = ubike_data['更新時間'].astype(
            'datetime64[ns]').astype(str)
    ubike_data = ubike_data.sort_values('目前車輛數量', ascending=False)
    datas = ubike_data.values.tolist()
    return datas


def get_location(address, lat, lng, event, line_bot_api):
    if '新北市' in address:
        datas = analyze_area_data(new_taipei_area=True)
    else:
        datas = analyze_area_data(new_taipei_area=False)
    send_data = []
    for data in datas:
        point1 = (lat, lng)
        point2 = (data[3], data[4])
        result = haversine(point1, point2, unit=Unit.METERS)
        if result <= 500:
            send_data.append([data[1], data[2], data[3],
                             data[4], data[5], data[7], data[8], round(result, 1)])
    data2 = [data for data in send_data]
    if len(data2) == 0:
        messages = (TextSendMessage('您所定位的位置周圍500公尺都沒有站點唷，麻煩你用走路的，謝謝！'))
    elif len(data2) == 1:
        messages = LocationSendMessage(
            data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'{data2[0][0]}\n更新時間：{data2[0][6]} \n目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}\n距離您的定位：{data2[0][-1]}公尺')
    elif len(data2) == 2:
        messages = LocationSendMessage(
            data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'{data2[0][0]}\n更新時間：{data2[0][6]} \n目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}\n距離您的定位：{data2[0][-1]}公尺'), LocationSendMessage(
            data2[1][0], data2[1][1], data2[1][2], data2[1][3]), TextSendMessage(f'{data2[1][0]}\n更新時間：{data2[1][6]} \n目前車輛數量：{data2[1][4]} 空位數量：{data2[1][5]}\n距離您的定位：{data2[1][-1]}公尺')
    else:
        data3 = [
            f'*您附近 共有{len(data2)}個站點', f'*欲想查詢地圖位置，可輸入該站點名稱(如:{data2[0][0][11:]}，{data2[1][0][11:]}...)！！']
        for i in data2:
            data3.append(i[0] + '\n' + '目前車輛數量為 :' +
                         str(i[-4]) + ' 空位數量為 : ' + str(i[-3]) + '\n' + '距離您的定位：' + str(round(i[-1], 1))+'公尺')
        messages = TextSendMessage('\n\n'.join(data3))
    line_bot_api.reply_message(event.reply_token, messages)
    return


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


def get_area(text, new_taipei=False):
    if new_taipei:
        datas = analyze_area_data(new_taipei_area=True)
    else:
        datas = analyze_area_data()
    area_dict = {}
    name = text
    send_data = get_data(datas, name, area_dict)
    return send_data


def ai(text, event, line_bot_api):
    try:
        if send_data is not None or send_data != []:
            data2 = [data for data in send_data if text in data[0]
                     or text in data[1]]
            if len(data2) == 0:
                messages = (TextSendMessage('您所找的地方/景點未搜尋到此站點名稱，請確認後再重新輸入！'))
            elif len(data2) == 1:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'{data2[0][0]}\n更新時間：{data2[0][6]} \n目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}')
            elif len(data2) == 2:
                messages = LocationSendMessage(
                    data2[0][0], data2[0][1], data2[0][2], data2[0][3]), TextSendMessage(f'{data2[0][0]}\n更新時間：{data2[0][6]} \n目前車輛數量：{data2[0][4]} 空位數量：{data2[0][5]}'), LocationSendMessage(
                    data2[1][0], data2[1][1], data2[1][2], data2[1][3]), TextSendMessage(f'{data2[1][0]}\n更新時間：{data2[1][6]} \n目前車輛數量：{data2[1][4]} 空位數量：{data2[1][5]}')
            else:
                data3 = [
                    f'*您所查詢的: {text} 共有{len(data2)}個站點', f'*欲想查詢地圖位置，可輸入該站點名稱(如:{data2[0][0][11:]}，{data2[1][0][11:]}...)！！']
                for i in data2:
                    data3.append(i[0] + '\n' + '目前車輛數量為 :' +
                                 str(i[-3]) + ' 空位數量為 : ' + str(i[-2]))
                messages = TextSendMessage('\n\n'.join(data3))
            line_bot_api.reply_message(event.reply_token, messages)
            return
    except:
        message = TextSendMessage(
            text='請注意地址/景點是否正確唷，例如: "臺"跟"台"的差別\n也請您從區域開始查找(不確定區域有哪些的話可以輸入區域查找\n再請您試一次，拜託～～～～')
        line_bot_api.reply_message(event.reply_token, message)
