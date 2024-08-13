# Бот для ClydeTapBot
## Запуск в Docker
```
$ git clone https://github.com/IgorKonstantinov/ClydeTapBot.git
$ cd ClydeTapBot
$ cp .env-example .env
$ nano .env # укажите ваши API_ID и API_HASH, остальное можно оставить по умолчанию
```
### Docker Compose (рекомендуется)
```
$ docker-compose run clydetapot -a 2 # первый запуск для авторизации (переопределяем аргументы)
$ docker-compose start # запуск в фоновом режиме (аргументы по умолчанию: -a 1)
```
### Docker
```
$ docker build -t clydetapot .
$ docker run --name ClydeTapBot -v .:/app -it clydetapot -a 2 # первый запуск для авторизации
$ docker rm ClydeTapBot # удаляем контейнер для пересоздания с аргументами по умолчанию
$ docker run -d --restart unless-stopped --name ClydeTapBot -v .:/app clydetapot # запуск в фоновом режиме (аргументы по умолчанию: -a 2)
```

## Ручная установка

```
# Linux
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
$ cp .env-example .env
$ nano .env # укажите ваши API_ID и API_HASH, остальное можно оставить по умолчанию
$ python3 main.py

# Windows (сначала установите Python 3.10 или более позднюю версию)
> python -m venv venv
> venv\Scripts\activate
> pip install -r requirements.txt
> copy .env-example .env
> # укажите ваши API_ID и API_HASH, остальное можно оставить по умолчанию
> python main.py
```

Также для быстрого запуска вы можете использовать аргументы:
```
$ python3 main.py --action (1/2)
# или
$ python3 main.py -a (1/2)

# 1 - запустить бот
# 2 - создать сессию
```
