#!/usr/bin/env python3

import os
import shlex
import subprocess
import argparse
import sys
import random
import pprint
import json
from pathlib import Path
from natsort import natsorted
from lib import local_data

with open(local_data, 'r+') as _f:
    data = json.load(_f)
    assert 'library_dir' in data

    LIB = {_k: data[_k] for _k in data if 'Path' in data[_k]}

    to_del = [
        _k for _k in LIB if
        not os.path.exists(os.path.join(data['library_dir'], data[_k]['Path']))
    ]
    l0 = len(LIB)
    l1 = len(to_del)
    print(f"{l0} entries detected.")

    if l1 > 0:
        if l1 / l0 <= 0.05:
            print(f"Deleted: {to_del}")
            confirm = True
        else:
            confirm = input(f"Delete {len(to_del)} entries (Y/N)")
            if "n" in confirm.lower():
                confirm = False
            else:
                confirm = True

        if confirm:
            for _k in to_del:
                del data[_k]

    _f.seek(0)
    json.dump(data, _f, indent=4, ensure_ascii=False)
    _f.truncate()
    LIB = {_k: data[_k] for _k in data if 'Path' in data[_k]}

if len(sys.argv) > 1 and '-n' not in sys.argv and '--number' not in sys.argv:
    sys.argv.insert(1, '-k')

pp = pprint.PrettyPrinter(indent=4)


def parse_cli():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-k",
            "--keywords",
            nargs='+',
        )
        parser.add_argument(
            "-n",
            '--number',
            type=int,
            choices=range(1, 13),
        )
        parser.set_defaults(number=5)
        return parser.parse_args()
    except argparse.ArgumentError as err:
        print(str(err))
        sys.exit(2)


def find_audio_files(_dir=os.getcwd(), exts=None):
    if exts is None:
        exts = ['.mp3', '.mp4', '.webm', '.flac']
    return natsorted([
        '"' + os.path.join(root, file) + '"' for ext in exts
        for root, dirs, files in os.walk(_dir) for file in files
        if file.lower().endswith(ext)
    ])


def find_cover(_dir=os.getcwd(), exts=None):
    if exts is None:
        exts = ['.jpg', '.webp', '.png']
    l = [
        os.path.join(root, file) for ext in exts
        for root, dirs, files in os.walk(_dir) for file in files
        if file.lower().endswith(ext)
    ]
    if not l:
        return 'no'
    return "'" + sorted([(os.path.getsize(file), file) for file in l],
                        key=lambda s: s[0])[-1][1] + "'"


def get_rjcode_with(keywords):
    _res = LIB.keys()
    for keyword in keywords:
        _res = [
            rjcode for rjcode in _res for value in data[rjcode].values()
            if (keyword in value) or (keyword in rjcode)
        ]
    return _res


def print_rjcode(_rjcode):
    print()
    print('========')
    print(_rjcode)
    print('========')
    # _path = data[_rjcode]['Path']
    _path = os.path.join(data['library_dir'], data[_rjcode]['Path'])
    for k in data[_rjcode].keys():
        if k not in ['img', 'Path', 'ファイル容量', 'ファイル形式']:
            print(f'  {k}:  \t{data[_rjcode][k]}')
    print(Path(_path).as_uri())
    cover = find_cover(_path)
    if cover[1:-1]:
        print(Path(cover[1:-1]).as_uri())
    print()


args = parse_cli()

if not args.keywords:
    size = min(len(LIB), args.number)
    rjcodes_to_play = random.sample(list(LIB.keys()), size)
else:
    temp = get_rjcode_with(args.keywords)
    print(f"{len(temp)} found:", temp)
    size = min(len(temp), args.number)
    rjcodes_to_play = random.sample(temp, size)

for rjcode in set(rjcodes_to_play):
    print_rjcode(rjcode)
    path = os.path.join(data['library_dir'], data[rjcode]['Path'])
    playlist = ' '.join(find_audio_files(path))
    mpv = f'mpv --loop-playlist=no --no-video {playlist}'
    subprocess.call(shlex.split(mpv))
