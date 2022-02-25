import math
import random
import requests
import speech_recognition
from vosk import Model, KaldiRecognizer
import wave
import json
import os
import pyttsx3
import webbrowser
import ipinfo
import wikipediaapi
import traceback
from googlesearch import search
from dotenv import load_dotenv


class User:
    """
    Описание текущего пользователя
    """

    name = ''
    sex = ''
    home_sity = ''


class VoiceAssistant:
    """
    Найстройки голосового ассистента
    """

    def __init__(self, name='Джарвис', sex='male', speech_language='ru'):

        self.name = name
        self.sex = sex
        self.speech_language = speech_language

    def setup_assistant_voice(self):
        voices = ttsEngine.getProperty("voices")
        if self.sex == 'female':
            ttsEngine.setProperty('voice', voices[0].id)
        else:
            ttsEngine.setProperty('voice', voices[3].id)


def play_voice_assistant_speech(text_to_speech: str):
    """
    Проигрывание речи ответов голосового ассистента (без сохранения аудио)
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    ttsEngine.say(str(text_to_speech))
    ttsEngine.runAndWait()


def record_and_recognize_audio():
    """
    Запись и распознавание аудио
    """
    with microphone:
        recognized_data = ''

        # регулирование уровня внешнего шума
        recognizer.adjust_for_ambient_noise(microphone, duration=1)

        try:
            print("Listening...")
            audio = recognizer.listen(microphone, 2)

            with open("microphone-results.wav", 'wb') as file:
                file.write(audio.get_wav_data())

        except speech_recognition.WaitTimeoutError:
            print("Can you check if your microphone is on, please?")
            return

        try:
            print("Started recognition...")
            recognized_data = recognizer.recognize_google(audio, language='ru').lower()
        except speech_recognition.UnknownValueError:
            pass
        except speech_recognition.RequestError:
            recognized_data = use_offline_recognition()

        return recognized_data


def use_offline_recognition():
    """
    Переключение на оффлайн-распознавание речи
    :return: распознанная фраза
    """
    recognized_data = ""
    try:
        # проверка наличия модели на нужном языке в каталоге приложения
        if not os.path.exists("vosk-model-small-ru-0.22"):
            print("Please download the model from:\n"
                  "https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
            exit(1)

        # анализ записанного в микрофон аудио (чтобы избежать повторов фразы)
        wave_audio_file = wave.open("microphone-results.wav", "rb")
        model = Model("vosk-model-small-ru-0.22")
        offline_recognizer = KaldiRecognizer(model, wave_audio_file.getframerate())

        data = wave_audio_file.readframes(wave_audio_file.getnframes())
        if len(data) > 0:
            if offline_recognizer.AcceptWaveform(data):
                recognized_data = offline_recognizer.Result()

                # получение данных распознанного текста из JSON-строки
                # (чтобы можно было выдать по ней ответ)
                recognized_data = json.loads(recognized_data)
                recognized_data = recognized_data["text"]
    except:
        print("Sorry, speech service is unavailable. Try again later")

    return recognized_data


def execute_commands(commands_name: str, *args):
    for key in commands.keys():
        if commands_name in key:
            commands[key](*args)
            return
    play_voice_assistant_speech('Простите, но я пока не могу разобрать вашу команду')


def greetings():
    play_voice_assistant_speech(f'Здравстувуйте, повелитель! мое имя - {assistant.name}. Как мне вас называть?')

    name = record_and_recognize_audio()
    play_voice_assistant_speech(
        f'{random_phrases_to_greetings[random.randint(0, len(random_phrases_to_greetings) - 1)]} - {name}')

    return name


def get_location():
    """
    С помощью текущего ip и ключа ipinfo получаем текущее расположение
    :return: город
    """
    handler = ipinfo.getHandler(os.getenv("access_token_ipinfo"))
    details = handler.getDetails()
    return details.city


def get_weather_forecast(*args):
    """
    Получение и озвучивание прогнза погоды
    :param args: город, по которому должен выполняться запос
    """
    tips_for_weather = {
        'Clear': 'На улице ясно',
        'Clouds': 'Облачно, поэтому советую накинуть на себя куртку',
        'Rain': 'На улице возможен дождь, посмотрите в окно. В случае выходы на улицу не забудьте зонтик',
        'Drizzle': 'На улице возможен дождь, посмотрите в окно. В случае выходы на улицу не забудьте зонтик',
        'Thunderstorm': 'Возможно появление грозы, советую сидеть дома',
        'Snow': 'В интернете сказанно о возможном появление снега сегодня',
        'Mist': 'Возможен туман',
    }
    city_name = args[0][0]
    try:
        city_name = get_location()
    except Exception as ex:
        print(ex)
        city_name = user.home_sity
        play_voice_assistant_speech(f'{user.name} я не смог получить ваше расположение. Смотрите логи')
        play_voice_assistant_speech(f'Для получения погоды я буду использовать город по умолчанию - {city_name}')
        play_voice_assistant_speech('Желаете изменить город?')
        input_voice = record_and_recognize_audio()
        if input_voice in ('да', 'конечно', ',безусловно'):
            play_voice_assistant_speech('Хорошо, тогда назовите город, для которого хотите получить прогноз погоды')
            input_voice = record_and_recognize_audio()
            play_voice_assistant_speech(f'Я вас понял. Ищу прогноз погоды для города - {input_voice}')
            city_name = input_voice
        else:
            play_voice_assistant_speech(f'Хорошо, тогда ищу прогноз погоды для города - {city_name}')
    try:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/find?q={city_name}&appid={os.getenv('token_openweather')}&units=metric")
        data = response.json()
        city_id = data['list'][0]['id']
        cur_temp = math.ceil(data['list'][0]['main']['temp'])
        weather_description = data['list'][0]['weather'][0]['main']
        if weather_description in tips_for_weather:
            weather_description = tips_for_weather[weather_description]
        else:
            weather_description = 'Посмотри в окно, не пойму что там за погода!'
        play_voice_assistant_speech(f'В городе {city_name} сейчас {cur_temp} градусов. {weather_description}!')
        play_voice_assistant_speech('Открыть полный прогноз погоды?')
        input_voice = record_and_recognize_audio()
        print(input_voice)
        if input_voice in ('да', 'конечно', 'безусловно', 'открой', 'покажи'):
            webbrowser.open(f'https://openweathermap.org/city/{city_id}')
        else:
            play_voice_assistant_speech(f'Понял, хорошего дня {user.name}')
    except Exception as ex:
        play_voice_assistant_speech(f'Простите {user.name}, но я пока не смогу сказать вам погоду. Смотрите логи')
        print(ex)


def get_random_number(*args):
    info = args[0]
    if not info:
        return
    numbers = []
    for i in info:
        if i.isdigit():
            numbers.append(int(i))
    play_voice_assistant_speech(random.randint(numbers[0], numbers[1]))


def search_in_youtube(*args):
    if len(args[0]) == 0:
        return
    search_item = ' '.join(args[0])
    url = f"https://www.youtube.com/results?search_query={search_item}"
    webbrowser.get().open(url)

    play_voice_assistant_speech(f"Вот что я нашел для {search_item} в ютубе")


def data_search_in_google(*args):
    if not args[0]:
        return

    search_phrase = ' '.join(args[0])
    try:
        for item in search(search_phrase,  # Строка для поиска
                           tld='com',  # Верхнеуровневый домен
                           lang=assistant.speech_language,  # Язык ассистента
                           num=1,  # количество результатов на странице
                           start=0,  # Индекс первого извлекаемоего элемента
                           stop=1,  # Индекс последннего извлекаемоего элемента
                           pause=1.0  # Задержка между HTTP запросами
                           ):
            webbrowser.get().open(item)
            play_voice_assistant_speech('Вот что мне удалось найти по вашему запросу в гугл')
    except Exception as ex:
        play_voice_assistant_speech('Возникли некторое проблемы, посмотри логи')
        print(ex)


def search_definition_in_wiki(*args):
    if not args[0]:
        return

    search_term = ' '.join(args[0])

    wiki = wikipediaapi.Wikipedia('ru')

    page_wiki = wiki.page(search_term)

    try:
        if page_wiki.exists():
            page_summary = page_wiki.summary
            page_url = page_wiki.fullurl

            webbrowser.get().open(page_url)
            play_voice_assistant_speech(page_summary[:200])
    except:
        traceback.print_exc()
        play_voice_assistant_speech(
            'При запросе к апи википедии произошла не совсем понятная для меня ошибка, посмотри логи')


commands = {
    # ('Привет'): greetings,
    # ('Пока'): farewell,
    ('определение', 'описание'): search_definition_in_wiki,
    ('информацию'): data_search_in_google,
    ('видео', 'ролик', 'видос'): search_in_youtube,
    ('число','рандомное'): get_random_number,
    ('погоду', 'прогноз'): get_weather_forecast,
}


random_phrases_to_greetings = ('очень приятно', 'рад знакомству', 'очень красивое имя')

if __name__ == "__main__":

    # инициализация инструментов распознавания и ввода речи
    recognizer = speech_recognition.Recognizer()
    microphone = speech_recognition.Microphone()

    # инициализация инструмента синтеза речи
    ttsEngine = pyttsx3.init()

    # настройка данных голосового помощника
    assistant = VoiceAssistant(name="Джарвис", sex='male', speech_language='ru')

    # установка голоса по умолчанию
    assistant.setup_assistant_voice()

    # Приветсвие и получение данных о пользователе
    user = User()
    name_user = greetings()
    user.name = name_user
    user.sex = 'male'
    user.home_sity = 'Курган'

    # загрузка ключей из .env-файла
    load_dotenv()

    while True:
        # старт записи речи с последующим выводом распознанной речи
        # и удалением записанного в микрофон аудио
        voice_input = record_and_recognize_audio()
        if os.path.exists('microphone-results.wav'):
            os.remove("microphone-results.wav")

        if voice_input is None:
            continue

        # отделение комманд от дополнительной информации (аргументов)
        voice_input = voice_input.split(" ")

        if voice_input[0] == 'стоп':
            exit()
        if voice_input[0] == 'найди':
            command_name = voice_input[1]
            command_args = [str(input_part) for input_part in voice_input[2:]]
            execute_commands(command_name, command_args)

