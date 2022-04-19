import json
import telebot
import requests as req
from geopy import geocoders
import os

token = '5370477168:AAFsEPF-p4JIFa7NYsXXq_XnuTSixJTEnzE'
token_yandex = '02bb0d86-42ae-4854-983c-6e6051224a57'

dir_name = (os.path.abspath(os.path.dirname(__file__)))


def print_yandex_weather(dict_weather_yandex, message):
    day = {'night': 'ночью', 'morning': 'утром', 'day': 'днем', 'evening': 'вечером', 'fact': 'сейчас'}
    bot.send_message(message.from_user.id, f'Яндекс сказал:')
    bot.send_message(message.from_user.id, f' Подробнее по ссылке '
                                           f'{dict_weather_yandex["link"]}')
    for i in dict_weather_yandex.keys():
        if i != 'link':
            time_day = day[i]
            bot.send_message(message.from_user.id, f'Температура {time_day} {dict_weather_yandex[i]["temp"]} °C\n'
                                                   f'На небе {dict_weather_yandex[i]["condition"]}\n')


def geo_pos(city: str):
    geolocator = geocoders.Nominatim(user_agent="telebot")
    latitude = str(geolocator.geocode(city).latitude)
    longitude = str(geolocator.geocode(city).longitude)
    return latitude, longitude


def yandex_weather(latitude, longitude, token_yandex: str):
    url_yandex = f'https://api.weather.yandex.ru/v2/informers/?lat={latitude}&lon={longitude}&[lang=ru_RU]'
    #print('url_yandex', url_yandex)
    yandex_req = req.get(url_yandex, headers={'X-Yandex-API-Key': token_yandex}, verify=False)
    conditions = {'clear': 'ясно', 'partly-cloudy': 'малооблачно', 'cloudy': 'облачно с прояснениями',
                  'overcast': 'пасмурно', 'drizzle': 'морось', 'light-rain': 'небольшой дождь',
                  'rain': 'дождь', 'moderate-rain': 'умеренно сильный', 'heavy-rain': 'сильный дождь',
                  'continuous-heavy-rain': 'длительный сильный дождь', 'showers': 'ливень',
                  'wet-snow': 'дождь со снегом', 'light-snow': 'небольшой снег', 'snow': 'снег',
                  'snow-showers': 'снегопад', 'hail': 'град', 'thunderstorm': 'гроза',
                  'thunderstorm-with-rain': 'дождь с грозой', 'thunderstorm-with-hail': 'гроза с градом'
                  }
    wind_dir = {'nw': 'северо-западное', 'n': 'северное', 'ne': 'северо-восточное', 'e': 'восточное',
                'se': 'юго-восточное', 's': 'южное', 'sw': 'юго-западное', 'w': 'западное', 'с': 'штиль'}
    #print('yandex_req.text', yandex_req.text)
    yandex_json = json.loads(yandex_req.text)
    yandex_json['fact']['condition'] = conditions[yandex_json['fact']['condition']]
    yandex_json['fact']['wind_dir'] = wind_dir[yandex_json['fact']['wind_dir']]
    for parts in yandex_json['forecast']['parts']:
        parts['condition'] = conditions[parts['condition']]
        parts['wind_dir'] = wind_dir[parts['wind_dir']]

    weather = dict()
    params = ['condition', 'wind_dir', 'pressure_mm', 'humidity']
    for parts in yandex_json['forecast']['parts']:
        weather[parts['part_name']] = dict()
        weather[parts['part_name']]['temp'] = parts['temp_avg']
        for param in params:
            weather[parts['part_name']][param] = parts[param]

    weather['fact'] = dict()
    weather['fact']['temp'] = yandex_json['fact']['temp']
    for param in params:
        weather['fact'][param] = yandex_json['fact'][param]

    weather['link'] = yandex_json['info']['url']
    return weather


def add_city(message):
    try:
        latitude, longitude = geo_pos(message.text.lower().split('город ')[1])
        global cities
        cities[message.from_user.id] = message.text.lower().split('город ')[1]
        with open('cities.json', 'w') as f:
            f.write(json.dumps(cities))
        return cities, 0
    except Exception as err:
        return cities, 1


bot = telebot.TeleBot(token)

with open(dir_name + '/cities.json', encoding='utf-8') as f:
    cities = json.load(f)


@bot.message_handler(command=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, f'Weatherbot специально для разработка ПО-А, {message.from_user.first_name}')
    bot.send_message(message.from_user.id,
                     f'Weatherbot специально для разработка ПО-А {message.from_user.first_name}')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global cities
    if message.text.lower() == 'привет' or message.text.lower() == 'здравствуйте':
        bot.send_message(message.from_user.id,
                         f'Добрый день {message.from_user.first_name}! Чтобы получить '
                         f' информацию о погоде в городе по умолчанию напишите слово "погода"'
                         f' или напишите название города в котором Вы сейчас')
    elif message.text.lower() == '/start':
        bot.send_message(message.from_user.id,
                         f'Weatherbot специально для разработка ПО-А, USER - {message.from_user.first_name}')
    elif message.text.lower() == '/help':
        bot.send_message(message.from_user.id,
                         f'Введите:\n'
                         f'"погода" - отобразить погоду в городе по умолчанию\n'
                         f'"название_города" - чтобы отобразить погоду в городе\n'
                         f'"мой город название_города" чтобы установить город по умолчанию\n'
                         f'"привет" или "здравствуйте" чтобы отобразить приветствие\n'
                         f'"/start" информация о боте\n'
                         f'"/help" это сообщение')
    elif message.text.lower() == 'погода':
        if message.from_user.id in cities.keys():
            city = cities[message.from_user.id]
            bot.send_message(message.from_user.id, f'Пользователь {message.from_user.first_name}!'
                                                   f' ваш город - {city}')
            latitude, longitude = geo_pos(city)
            yandex_weather_x = yandex_weather(latitude, longitude, token_yandex)
            print_yandex_weather(yandex_weather_x, message)
        else:
            bot.send_message(message.from_user.id, f'Пользователь {message.from_user.first_name}'
                                                   f' Город не указан! Просто напишите:'
                                                   f'"Мой город *****" и я запомню ваш город по умолчанию!')
    elif message.text.lower()[:9] == 'мой город':
        cities, flag = add_city(message)
        if flag == 0:
            bot.send_message(message.from_user.id, f'Пользователь {message.from_user.first_name}!'
                                                   f' Ваш город установлен, это'
                                                   f' {cities[message.from_user.id]}')
        else:
            bot.send_message(message.from_user.id, f'Пользователь {message.from_user.first_name}!'
                                                   f' Произошло некоторое дерьмо :(')
    else:
        try:
            city = message.text
            bot.send_message(message.from_user.id, f'Добрый день {message.from_user.first_name}! Ваш город {city}')
            latitude, longitude = geo_pos(city)
            print('latitude, longitude, token_yandex is', latitude, longitude, token_yandex)
            yandex_weather_x = yandex_weather(latitude, longitude, token_yandex)
            print_yandex_weather(yandex_weather_x, message)
        except AttributeError as err:
            bot.send_message(message.from_user.id, f'{message.from_user.first_name}! внимание,'
                                                   f' город не найден!'
                                                   f'Код ошибки {err}, попробуйте другой город')


bot.polling(none_stop=True)

