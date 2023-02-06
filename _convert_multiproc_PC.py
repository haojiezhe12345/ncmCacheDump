import os
import sys
import json
import requests
import multiprocessing
import time

uc_path = './'  # 缓存路径 例 D:/CloudMusic/Cache/
mp3_path = './output/'  # 导出歌曲路径
EXT_NAME = 'uc'  # 后缀uc结尾为PC端歌曲缓存, uc!结尾为手机端缓存
MAXCPUS = multiprocessing.cpu_count() - 1

def convert(file):
    global uc_path, mp3_path
    if file[1] == ':' or file[0] == '/':
        uc_path = ''
        mp3_path = ''
    print(' * Import: ' + file)

    uc_file = open(uc_path + file, mode='rb')
    uc_content = uc_file.read()
    mp3_content = bytearray()
    for byte in uc_content:
        byte ^= 0xa3
        mp3_content.append(byte)

    # 从.info文件读取缓存文件的格式(PC端)
    if (EXT_NAME == 'uc'):
        try:
            info_file = open(
                uc_path + file[0:-1 - len(EXT_NAME)] + '.info', 'r')
            info_json = json.loads(info_file.read())
            ext_export = info_json['format']
        except:
            print(f' ! Info file not found, assuming it is MP3')
            ext_export = 'mp3'
    else:
        ext_export = 'mp3'

    # 根据文件名中的歌曲id匹配歌名
    try:
        song_id = os.path.basename(file[0:file.find('-')])
        song_data = requests.get(
            f'http://music.163.com/api/song/detail/?id={song_id}&ids=%5B{song_id}%5D').text
        song_data = json.loads(song_data)
        song_name = song_data['songs'][0]['name']
        song_artist = song_data['songs'][0]['artists'][0]['name']
        mp3_file_name = f'{mp3_path}{song_artist} - {song_name}.{ext_export}'
    except:
        print(' ! Unable to get song metadata, the song will remain unrenamed')
        mp3_file_name = mp3_path + file[0:0 - len(EXT_NAME)] + ext_export

    try:
        mp3_file = open(mp3_file_name, 'wb')
        mp3_file.write(mp3_content)
        uc_file.close()
        mp3_file.close()
        print(f'-> Success {mp3_file_name}')
    except:
        print(f' X Failed to write file {mp3_file_name}')

if __name__ == '__main__':
    
    print(f'Device cpu count: {multiprocessing.cpu_count()}, will use {MAXCPUS}')
    if not os.path.exists(mp3_path):
        os.mkdir(mp3_path)

    #print(sys.argv)
    if len(sys.argv) == 1:
        files = os.listdir(uc_path)
    else:
        files = sys.argv

    for file in files:
        if file[0 - len(EXT_NAME):] == EXT_NAME:
            while (True):
                if (len(multiprocessing.active_children()) < MAXCPUS):
                    multiprocessing.Process(target=convert, args=(file,)).start()
                    break
                else:
                    time.sleep(0.1)

    while (True):
        if (len(multiprocessing.active_children()) == 0):
            input("\nPress Enter to continue...")
            break
        else:
            time.sleep(1)

