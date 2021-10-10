import config
import requests
import shutil
import json
import time
import asyncio

from aiogram import Bot, Dispatcher, executor
from datetime import datetime
from bs4 import BeautifulSoup
from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *

link = 'https://coinmarketcap.com'
altLink = 'https://www.blockchaincenter.net/altcoin-season-index'
fgImage = 'https://alternative.me/crypto/fear-and-greed-index.png'
whiteListLink = 'whiteListChats.json'
noneUsersLink = 'noneUsers.json'


bot = Bot(token=config.tgAPI)
dp = Dispatcher(bot)

with open(whiteListLink) as json_file:
    whiteListFile = json.load(json_file)

whiteList = whiteListFile

noneUsers = {}

result = os.stat(noneUsersLink)

if result.st_size == 1:
    with open(noneUsersLink) as json_file:
        noneUsers = json.load(json_file)

mainPath = os.path.abspath(__file__).split("\\")
mainPath.remove(mainPath[-1])

request_client = RequestClient(api_key=config.binanceAPI.fromkeys('api_key'), secret_key=config.binanceAPI.fromkeys('secret_key'))

async def delMsg(botMsg, userMsg, timeF=20):
    if userMsg.chat.id == -1001578263497 or userMsg.chat.id == -1001532493523:
        timeF = 60 * 60
    await asyncio.sleep(timeF)
    await bot.delete_message(userMsg.chat.id, botMsg.message_id)
    await bot.delete_message(userMsg.chat.id, userMsg.message_id)

def checkUser(message):
    return message.chat.id in whiteList.values() or message.chat.id > 0

def addToBlackList(dict):
    file = open(noneUsersLink, "w")
    json.dump(dict, file)
    file.close()
    return dict

def getDominance():
    return BeautifulSoup(requests.get(link).text, 'lxml').find('a', attrs={'href':'/charts/#dominance-percentage'}).text

def getAltSeason():
    re = requests.get(altLink).text
    soupAlt = BeautifulSoup(re, 'lxml')
    altcoinSeasonIndex = soupAlt.find_all('div', attrs={'style':'margin-top:-74px;padding: 0px 10px;'})[1].find_next('div').text
    month = soupAlt.find_all('div', attrs={'style':'margin-top:-74px;padding: 0px 10px;'})[0].find_next('div').text
    year = soupAlt.find_all('div', attrs={'style':'margin-top:-74px;padding: 0px 10px;'})[2].find_next('div').text
    return f'⚡️ Altcoin Month Index {month}\n⚡️ Altcoin Season Index: {altcoinSeasonIndex}\n⚡️ Altcoin Year Index: {year}'

def getIndex():
    path = 'fear-and-greed-index.png'
    r = requests.get(fgImage, stream=True)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    else:
        path = 'Фото не найдено, обратитесь к администратору @kopasxa'
    return path

def getAllCoin(limit):
    dataMarket = {}
    for index in zip(range(limit)):
        response = requests.get(f'{link}/?page={index[0] + 1}').text
        soup = BeautifulSoup(response, 'lxml')

        for name in soup.tbody.find_all('tr'):
            if name.find('p', class_ = 'coin-item-symbol') == None:
                symbol = name.find('span', class_ = 'crypto-symbol').text.lower()
            else:
                symbol = name.find('p', class_ = 'coin-item-symbol').text.lower()
            if not symbol in dataMarket:
                dataMarket[symbol] = name.find('a', class_ = 'cmc-link', href=True)['href']
    return dataMarket

dataMarket = getAllCoin(63)

def getData(soup):
    name = soup.find('small', class_ = 'nameSymbol').text
    price = soup.find('div', class_ = 'priceValue').text
    marketCap = soup.find('div', class_ = 'statsValue').text
    percent = soup.find('span', class_='sc-15yy2pl-0').getText()
    percentsUD = soup.find('span', class_='sc-15yy2pl-0').findChildren('span')
    sign = ''
    color = ''
    statistics = ''

    result = request_client.get_top_long_short_positions(symbol=name + 'USDT', period='1h', limit=1)

    symbol = ''
    LSRatio = ''
    longs = ''
    shorts = ''

    dominance = ''

    #dom = 'https://api.coingecko.com/api/v3/global'
    #r = requests.get(dom).json()

    #if name.lower() in r["data"]["market_cap_percentage"]:
        #dominance = '📊 Dominance: ' + str(r["data"]["market_cap_percentage"][name.lower()])[:5] + '%\n'

    for idx, row in enumerate(result):
        members = [attr for attr in dir(row) if not callable(attr) and not attr.startswith("__")]
        for member_def in members:
            val_str = str(getattr(row, member_def))
            if member_def == 'longAccount': longs = val_str
            elif member_def == 'shortAccount': shorts = val_str
            elif member_def == 'longShortRatio': LSRatio = val_str
            elif member_def == 'symbol': symbol = val_str

    if result != []:
        statistics += f'{symbol}\n🕐 Time frame: 1h\n🟩️ Long: {str(float(longs) * 100)[:4]}% 🟥️ Short: {str(float(shorts) * 100)[:4]}%\n☁️ Volumes (long/short): {LSRatio}\n'

    if percentsUD[0]['class'][0] == 'icon-Caret-up':
        sign = '+'
        color = '🟢'
    elif percentsUD[0]['class'][0] == 'icon-Caret-down':
        sign = '-'
        color = '🔴'
    
    return f'\n\n{color} #{name} - {price} ({sign}{percent})\nVolume (24h) - {marketCap}\n{statistics}{dominance}'

def get50(lim):
    returns = ''
    dataMarket2 = getAllCoin(1)

    for index, item in zip(range(lim), dataMarket2):
        newLink = link + dataMarket2[item]

        response2 = requests.get(newLink).text
        soup = BeautifulSoup(response2, 'lxml')
        returns += getData(soup)

    return returns

def getcoin(coin):
    newLink = link + dataMarket[coin]

    response3 = requests.get(newLink).text
    soup = BeautifulSoup(response3, 'lxml')

    return getData(soup)

async def buy(message):
    botMsg = await bot.send_message(message.chat.id, 'Оплатите подписку. Поддержка: @kopasxa')
    await delMsg(message, botMsg)


# Бот создан при поддежке команды, @crypto_djedis\n

@dp.message_handler(commands=['start'])
async def start_message(message):
    await bot.send_message(message.chat.id, '👀 Привет, ' + str(message.chat.first_name) + ' !')
    await bot.send_message(message.chat.id, 'Выбери цену каких монет хочешь посмотреть, напиши \n/символ монеты')

""" @dp.message_handler(commands=['top50'])
def start_message(message):
    bot.send_message(message.chat.id, get50(50)) """

@dp.message_handler(commands=['top10'])
async def start_message(message):
    if checkUser(message):
        botMsg = await bot.send_message(message.chat.id, get50(10))
        await delMsg(message, botMsg)
    else:
        await buy(message)

@dp.message_handler(commands=['fgindex'])
async def start_message(message):
    if checkUser(message):
        botMsg = await bot.send_photo(message.chat.id, photo=open(getIndex(), 'rb'), caption="Crypto Fear & Greed Index")
        await delMsg(message, botMsg)
    else:
        await buy(message)

@dp.message_handler(commands=['dominance'])
async def start_message(message):
    if checkUser(message):
        botMsg = await bot.send_message(message.chat.id, f'📊 Dominance: {getDominance()}')
        await delMsg(message, botMsg)
    else:
        await buy(message)


@dp.message_handler(commands=['altseason'])
async def start_message(message):
    if checkUser(message):
        botMsg = await bot.send_message(message.chat.id, getAltSeason())
        await delMsg(message, botMsg)
    else:
        await buy(message)

@dp.message_handler(commands=dataMarket.keys())
async def start_message(message):
    if checkUser(message):
        botMsg = await bot.send_message(message.chat.id, getcoin(message.text.split('/')[1]))
        await delMsg(message, botMsg)
    else:
        await buy(message)

@dp.message_handler(commands=['adminPanel'])
async def start_message(message):
    if message.chat.id == 810636815:
        text = ''
        for item in noneUsers.keys():
            print(item)
            text += await bot.get_chat(item).username + ':' + bot.get_chat(item).title + ':' + bot.get_chat(item).invite_link + '\n'
            await bot.send_message(message.chat.id, text)
    else:
        await bot.send_message(message.chat.id, 'Ты не админ (')

@dp.message_handler(content_types=['text'])
async def send_text(message):
    print(message.chat.id in whiteList.values(), message.chat.id)
    if (message.chat.id in whiteList.values()) == False and message.chat.id < 0:
        print(message.chat.id, bot.get_chat(message.chat.id))
        global noneUsers
        noneUsers[int(message.chat.id)] = str(await bot.get_chat(message.chat.id).invite_link)
        noneUsers = addToBlackList(noneUsers)
    if message.text.lower() == 'топ 50 монет':
        if checkUser(message):
            await bot.send_message(message.chat.id, get50(50))
        else:
            await bot.send_message(message.chat.id, 'Оплатите подписку. Поддержка: @kopasxa')
            
    elif message.text.lower() == 'топ 10 монет':
        if checkUser(message):
            await bot.send_message(message.chat.id, get50(10))
        else:
            await bot.send_message(message.chat.id, 'Оплатите подписку. Поддержка: @kopasxa')

if __name__ == '__main__':
    executor.start_polling(dp)