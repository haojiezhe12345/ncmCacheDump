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
    mtime = os.path.getmtime(src)
    os.utime(dest, (mtime, mtime))


def convert_file(src_file: str, out_dir: str, song_detail: dict = None):
    print(src_file)

    src_ext = os.path.splitext(src_file)[1]
    src_name = {
        '.uc': os.path.splitext(src_file)[0],
        '.uc!': os.path.splitext(src_file)[0],
        '.nmsf': os.path.splitext(src_file)[0].removesuffix('_0'),
    }[src_ext]

    size_matched = True
    try:
        with open(src_name + {
            '.uc': '.idx',
            '.uc!': '.idx!',
            '.nmsf': '.nmsfi',
        }[src_ext]) as f:
            idx = json.load(f)
            if os.path.getsize(src_file) != int(idx[{
                '.uc': 'size',
                '.uc!': 'filesize',
                '.nmsf': 'file_size',
            }[src_ext]]):
                size_matched = False
                print('Size not match')
    except:
        print('Unable to check file size')

    ext = 'mp3'
    try:
        with open(src_name + {
            '.uc': '.info',
            '.uc!': '.idac!',
            '.nmsf': '.config',
        }[src_ext]) as f:
            info = json.load(f)
            ext = info[{
                '.uc': 'format',
                '.uc!': 'audioFormat',
                '.nmsf': 'audioFormat',
            }[src_ext]]
    except:
        print(f'Unable to determine file format, assuming it is .{ext}')

    bitrate = SongFilename(src_file).bitrate

    out_file = f"{song_detail['name']} - {song_detail['artists'][0]['name']}" if song_detail and song_detail['name'] else os.path.basename(src_file)
    out_file = re.sub(r'[\\/:*?"<>|]', '_', out_file)
    out_file += f' ({bitrate}k)' if size_matched else f' ({bitrate}k UNCOMPLETED)'
    out_file += f'.{ext}'
    out_file = os.path.join(out_dir, out_file)

    convert_uc(src_file, out_file)


class SongFilename:
    def __init__(self, filename: str):
        self.name = os.path.basename(os.path.splitext(filename)[0])
        self.ext = os.path.splitext(filename)[1]
        self.name_spilt = self.name.split({
            '.uc': '-',
            '.uc!': '-',
            '.nmsf': '_',
        }[self.ext])

    @property
    def id(self):
        return int(self.name_spilt[0])

    @property
    def bitrate(self):
        return round(int(self.name_spilt[1]) / {
            '.uc': 1,
            '.uc!': 1000,
            '.nmsf': 1000,
        }[self.ext])


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


def convert_folder(src_dir: str, out_dir='output', workers=WORKERS):
    t0 = time.time()
    print(f'Workers: {workers}')

    conv_list: list[str] = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if os.path.splitext(file)[1] in ['.uc', '.uc!', '.nmsf']:
                conv_list.append(filepath)
                print(f'Added {len(conv_list)} songs', end='\r')
    print()

    songs = {}
    for song in get_song_details([SongFilename(file).id for file in conv_list]):
        songs[song['id']] = song

    with ProcessPoolExecutor(max_workers=workers) as exe:
        for file in conv_list:
            exe.submit(convert_file, file, out_dir, songs.get(SongFilename(file).id, None))
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
