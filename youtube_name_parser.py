from googleapiclient.discovery import build

# Ваш API-ключ
channel_id = 'UCocemgp-kMkgdECI1yAhbTA'
api_key = ''
# Подключение к YouTube API
youtube = build('youtube', 'v3', developerKey=api_key)

# Получение загрузочного плейлиста канала
channel_response = youtube.channels().list(
    part='contentDetails',
    id=channel_id
).execute()

uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

# Открываем файл для записи
with open(f'video_titles{channel_id}.txt', 'w', encoding='utf-8') as file:
    next_page_token = None
    while True:
        playlist_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in playlist_response['items']:
            title = item['snippet']['title']
            print(title)
            file.write(title + '\n')

        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break

print(f"Список видео сохранен в 'video_titles{channel_id}.txt'")
