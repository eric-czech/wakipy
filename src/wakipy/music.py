import vlc
import youtube_dl
import logging
import time
import json
import os
import config
import os.path as osp
logger = logging.getLogger(__name__)

STOP = False


def stop():
    global STOP
    STOP = True


def play_song(observer, path):
    global STOP
    STOP = False
    player = vlc.MediaPlayer(path)
    ct = 0
    observer('before', player, ct)
    player.play()
    while (player.get_state() not in [vlc.State.Ended, vlc.State.Error]) and not STOP:
        logger.info("Waiting for song to stop...")
        ct += 1
        time.sleep(10)
        logger.info("Current volume = %s", player.audio_get_volume())
        observer('during', player, ct)
    player.stop()
    observer('after', player, ct)
    logger.info("Song playback complete")


def play_all():
    logger.info("Playing music")
    manifest = get_manifest()

    # Sort by timestamp entry in manifest
    manifest = [(k, v) for k, v in manifest.items()]
    manifest = sorted(manifest, key=lambda x: -(x[1]['ts'] or 0))

    logging.info("Found order of songs: {}".format([s[1]['title'] for s in manifest]))

    def observer(event, player, ct):
        if event == 'before':
            player.audio_set_volume(10)
        if event == 'during':
            if ct % 4 == 0:
                player.audio_set_volume(min(player.audio_get_volume() + 5, 50))

    for k, v in manifest:
        logger.info("Playing song '%s' (%s)", v['title'], k)
        play_song(observer, v['path'])
        if STOP:
            break
    logger.info("Music playback complete")


def get_manifest():
    manifest = {}
    path = config.cfg.manifest_path
    if not osp.exists(path):
        return manifest
    with open(path, 'r') as fd:
        return json.load(fd)

def save_manifest(manifest):
    path = config.cfg.manifest_path
    with open(path, 'w') as fd:
        return json.dump(manifest, fd)
    return path

def _ts():
    return int(round(time.time() * 1000))

def rename(id, name):
    manifest = get_manifest()
    if id not in manifest:
        raise ValueError('Song "{}" not found'.format(id))
    manifest[id]['title'] = name
    save_manifest(manifest)
    return manifest

def prioritize(id):
    manifest = get_manifest()
    if id not in manifest:
        raise ValueError('Song "{}" not found'.format(id))
    manifest[id]['ts'] = _ts()
    save_manifest(manifest)
    return manifest

def download(id):
    url = 'https://www.youtube.com/watch?v={id}'.format(id=id)
    path = osp.join(config.cfg.music_data_dir, id + '.mp3')
    if not osp.exists(osp.dirname(path)):
        os.makedirs(osp.dirname(path))
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    manifest = get_manifest()
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video = {
            'id': id,
            'title': info.get('title', None),
            'url': info.get("url", None),
            'type': 'yt',
            'path': path,
            'ts': _ts()
        }
        manifest[id] = video
    save_manifest(manifest)
    logger.info("Downloaded video '%s'", video)
    return video


def sync():
    # Placeholder for potential playlist syncing
    logger.info("Running sync")
    logger.info("Sync complete")