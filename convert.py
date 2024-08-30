import os
import json
import requests
import time
import re
import sys
from urllib.parse import quote
from concurrent.futures import ProcessPoolExecutor

BUF_SIZE = 1024 * 200
WORKERS = int(os.cpu_count() * 0.8)

API_SONG_DETAIL_CHUNK_SIZE = 100


def convert_uc(src: str, dest: str):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(src, 'rb') as fr:
        with open(dest, 'wb') as fw:
            while True:
                buf = fr.read(BUF_SIZE)
                if buf == b'':
                    break
                buf1 = bytearray()
                for b in buf:
                    buf1.append(b ^ 0xa3)
                fw.write(buf1)


def get_song_details(song_ids: list[int]) -> list[dict]:
    songs = []
    session = requests.Session()
    for chunk, i in [(song_ids[i:i+API_SONG_DETAIL_CHUNK_SIZE], i) for i in range(0, len(song_ids), API_SONG_DETAIL_CHUNK_SIZE)]:
        print(f'Getting song details: {i}/{len(song_ids)}', end='\r')
        r = session.get(f'http://music.163.com/api/song/detail/?ids={quote(json.dumps(chunk))}')
        for song in json.loads(r.text)['songs']:
            songs.append(song)
    print()
    return songs


def convert_file(src_file: str, out_dir: str, song_detail: dict = None):
    print(src_file)

    is_mobile = src_file.endswith('!')

    size_matched = True
    try:
        with open(os.path.splitext(src_file)[0] + ('.idx' if not is_mobile else '.idx!')) as f:
            idx = json.load(f)
            if os.path.getsize(src_file) != int(idx['size'] if not is_mobile else idx['filesize']):
                size_matched = False
                print('size not match')
    except:
        print('idx not found, not checking file size')

    ext = 'mp3'
    try:
        with open(os.path.splitext(src_file)[0] + ('.info' if not is_mobile else '.idac!')) as f:
            info = json.load(f)
            ext = info['format'] if not is_mobile else info['audioFormat']
    except:
        print(f'info not found, assuming format is {ext}')

    bitrate = int(os.path.basename(src_file).split('-')[1])
    if is_mobile:
        bitrate //= 1000

    out_file = f"{song_detail['name']} - {song_detail['artists'][0]['name']}" if song_detail and song_detail['name'] else os.path.basename(src_file)
    out_file = re.sub(r'[\\/:*?"<>|]', '_', out_file)
    out_file += f' ({bitrate}k)' if size_matched else f' ({bitrate}k uncompleted)'
    out_file += f'.{ext}'
    out_file = os.path.join(out_dir, out_file)

    convert_uc(src_file, out_file)


def convert_folder(src_dir: str, out_dir='output', workers=WORKERS):
    t0 = time.time()
    print(f'Workers: {workers}')

    conv_list = [file for file in os.listdir(src_dir) if file.endswith('.uc') or file.endswith('.uc!')]

    songs = {}
    for song in get_song_details([int(file.split('-')[0]) for file in conv_list]):
        songs[song['id']] = song

    with ProcessPoolExecutor(max_workers=workers) as exe:
        for file in conv_list:
            exe.submit(convert_file, os.path.join(src_dir, file), out_dir, songs.get(int(file.split('-')[0]), None))
        print('Task creation finished')

    t1 = time.time()
    print(f'Done {t1 - t0:.3f}s')


if __name__ == '__main__':

    conv_dir = ''

    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '-help', '--help']:
            print('Usage:\npython convert.py <path-to-cache-folder>\n\nIf cache folder is not specified, it will prompt you to pick a folder')
            exit()
        else:
            conv_dir = sys.argv[1]
    else:
        try:
            import tkinter
            from tkinter import filedialog
            tkinter.Tk().withdraw()
            conv_dir = filedialog.askdirectory()
        except:
            pass

    if not conv_dir:
        conv_dir = input('Enter path to cache folder: ')

    print('Converting files in:', conv_dir)
    convert_folder(conv_dir)

    input('\nPress enter to exit\n')
