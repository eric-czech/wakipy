import os.path as osp
DEFAULT_DATA_DIR = '/home/pi/data/wakipy'


class Config(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir

    @property
    def music_data_dir(self):
        return osp.join(self.data_dir, 'music')

    @property
    def manifest_path(self):
        return osp.join(self.music_data_dir, 'manifest.json')


cfg = Config(DEFAULT_DATA_DIR)


def set_from_args(args):
    global cfg
    if args.data_dir:
        cfg = Config(args.data_dir)