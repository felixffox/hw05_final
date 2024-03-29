# hw05_final

Социальная сеть YaTube для публикации постов и картинок (Яндекс.Практикум)
=====

Описание проекта
----------
Проект создан в рамках учебного курса Яндекс.Практикум.

Социальная сеть для авторов и подписчиков. Пользователи могут подписываться на избранных авторов, оставлять и удалять комментари к постам, оставлять новые посты на главной странице и в тематических группах, прикреплять изображения к публикуемым постам. 

Реализована система регистрации новых пользователей, система тестирования проекта на unittest, пагинация постов и кэширование страниц. Проект имеет верстку с адаптацией под размер экрана устройства пользователя.

Стек технологий
----------
* Python 3.8
* Django 2.2 
* Unittest
* Pytest
* SQLite3
* CSS
* HTML

Установка проекта из репозитория (Linux и macOS)
----------

1. Клонировать репозиторий и перейти в него в командной строке:
```bash
git clone git@github.com:NikitaChalykh/YaTube.git

cd YaTube
```
2. Cоздать и активировать виртуальное окружение:
```bash
python3 -m venv env

source env/bin/activate
```
3. Установить зависимости из файла ```requirements.txt```:
```bash
python3 -m pip install --upgrade pip

pip install -r requirements.txt
```
4. Выполнить миграции:
```bash
cd hw05_final

python3 manage.py migrate
```
5. Запустить проект (в режиме сервера Django):
```bash
python3 manage.py runserver
```
