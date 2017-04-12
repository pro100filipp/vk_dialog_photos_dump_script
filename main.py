# coding=utf-8


import os
import re
import sys

import requests

CWD = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FOLDER = 'photos'
ERRORS = [
    'remixsid',
    'dialog_id'
]


class Loader:
    """
    Class for loading image data
    """
    links = []
    url = 'https://vk.com/wkview.php'

    def __init__(self, remixsid, dialog_id, folder_name=DEFAULT_FOLDER):
        self._cookies = {
            'remixsid': remixsid
        }
        self._count = 10000
        self._offset = 0
        self.data = {
            'act': 'show',
            'al': 1,
            'loc': 'im',
            'w': 'history%s_photo' % dialog_id,
            'offset': self._offset,
            'part': 1

        }
        self.folder = os.path.join(CWD, folder_name)

    def _fetch_urls(self, save=True):
        """
        Fetch image urls and optionally save them to a file
        """
        count_pattern = r'(?<=\"count\":)\d+'
        offset_pattern = r'(?<=\"offset\":)\d+'
        link_pattern = r'(?<=\()https?://(cs|pp).+?(?=\))'

        while self._count > self._offset:
            r = requests.post(self.url, cookies=self._cookies, data=self.data)
            count_match = re.search(count_pattern, r.text)
            offset_match = re.search(offset_pattern, r.text)
            if count_match and offset_match:
                self._count = int(count_match[0])
                self._offset = int(offset_match[0])
                for link in re.finditer(link_pattern, r.text):
                    self.links.append(link[0])
            else:
                break
            self.data['offset'] = self._offset
            print('Fetched %d links' % len(self.links), end='\r')

        if save:
            with open(os.path.join(self.folder, 'links.txt'), 'w') as f:
                for l in self.links:
                    f.write(l + '\n')

    def get_images(self, save_links=False):
        """
        Download images from urls fetched
        """
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        self._fetch_urls(save_links)

        for i, l in enumerate(self.links):
            print('Loading image %d from %d' %
                  (i + 1, len(self.links)), end='\r')
            r = requests.get(l, stream=True)
            with open(os.path.join(self.folder, '%d.jpg' % i), 'wb') as f:
                for chunk in r.iter_content(chunk_size=128):
                    f.write(chunk)
        print('Done! %d images downloaded.' % len(self.links))


def print_help():
    """
    Prints usage information
    """
    print('''
    Usage: python main.py <remixsid> <dialog_id> <name_of_folder>
        <remixsid> is a cookie set by vk.com
        <dialog_id> is a string parameter "sel" in address line which you see when open a dialog
        <name_of_folder> is a folder name, where to store data
    ''')
    sys.exit()


def print_err(number):
    """
    Prints arguments error
    """
    print('''
        Invalid number of arguments. {err} {verb} missing.
        Please check and run again.
        '''.format(err=', '.join(ERRORS[number - 1:]),
                   verb='are' if number < 2 else 'is'))
    sys.exit()


if __name__ == '__main__':
    args_number = len(sys.argv)
    if args_number == 1 or sys.argv[1] == 'help':
        print_help()

    elif args_number < 3:
        print_err(args_number)

    remixsid = sys.argv[1]
    dialog_id = sys.argv[2]
    folder_name = sys.argv[3] if args_number >= 4 else DEFAULT_FOLDER

    loader = Loader(remixsid, dialog_id, folder_name)
    loader.get_images()
