# Это наш телеграмм бот!!! [@animamix_bot](https://t.me/animamix_bot)
Бот берет обложки аниме с аниме библиотеки [шикимори](https://shikimori.one/) и соединяет их с названиями видео с каналов [ItsMamix](https://www.youtube.com/@ItsMamix), [Дюшес](https://www.youtube.com/@OffDuchess) и [Экспериментаторы](https://www.youtube.com/@Exprmnts/videos).

![image](https://github.com/user-attachments/assets/00550eee-e52a-4f25-9251-6d29a500302d)

### Config
- **token** - токен телеграмм бота
- **api_url** - get запрос `https://shikimori.one/api/animes?page={page}&season=2005_2025&score=6&kind=ova,tv,movie,ona` 
	- page - номер аниме(берется рандомный)
	- season - года выпуска аниме
	- score - оценка > n 
	- kind - тип аниме
	подробнее с shikimori api можно ознакомиться [тут](https://shikimori.one/api/doc/1.0/animes/index)
- **max_retries** - количество повторных запросов при получении пустых ответов или картинки заглушки
- **video_titles_file** - .txt файл с названиями роликов. Программа для их генерации ***youtube_name_parcer.py***
- **debug**- включение/выключение отладки в консоль
### Работа бота 
Бот работает по адресу @animamix_bot или [тут](https://t.me/animamix_bot), можете добавлять в свои чаты доступ к нему не ограничен.
Для запуска бота используется команда - /start 
И основная команда генерирующая контент - /anime
