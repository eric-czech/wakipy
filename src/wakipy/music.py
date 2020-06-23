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


def play_song(observer, path, idx, ct):
    global STOP
    STOP = False
    player = vlc.MediaPlayer(path)
    observer('before', player, idx, ct)
    player.play()
    while (player.get_state() not in [vlc.State.Ended, vlc.State.Error]) and not STOP:
        logger.info("Waiting for song to stop...")
        logger.info("Current music player state: %s", player.get_state())
        ct += 1
        time.sleep(10)
        logger.info("Current volume = %s", player.audio_get_volume())
        observer('during', player, idx, ct)
    player.stop()
    observer('after', player, idx, ct)
    logger.info("Song playback complete")
    return ct


def play_all():
    logger.info("Playing music")
    manifest = get_manifest()

    # Sort by timestamp entry in manifest
    manifest = [(k, v) for k, v in manifest.items()]
    manifest = sorted(manifest, key=lambda x: -(x[1]['ts'] or 0))

    logging.info("Found order of songs: {}".format([s[1]['title'] for s in manifest]))

    def observer(event, player, _, ct):
        if ct == 0 and event == 'before':
            player.audio_set_volume(10)
        if event == 'during':
            if ct % 4 == 0:
                player.audio_set_volume(min(player.audio_get_volume() + 5, 50))

    ct = 0
    for i, (k, v) in enumerate(manifest):
        logger.info("Playing song '%s' (%s)", v['title'], k)
        ct = play_song(observer, v['path'], i, ct)
        if STOP:
            break
    logger.info("Music playback complete")


def get_manifest():
    manifest = {}
    path = config.cfg.manifest_path
    if not osp.exists(path):
        return manifest
    with open(path, 'r') as fd:
        for l in fd.readlines():
            if l:
                obj = json.loads(l)
                manifest[obj['_id']] = obj
    return manifest


def save_manifest(manifest):
    path = config.cfg.manifest_path
    with open(path, 'w') as fd:
        for vid in sorted(manifest.keys()):
            obj = manifest[vid]
            obj['_id'] = vid
            fd.write(json.dumps(obj) + '\n')
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
    # It seems it's actually necessary to use the string format fields and not
    # hard-code the template for the path (this was also seen in
    # https://stackoverflow.com/questions/47685506/pygame-playing-mp3-files-downloaded-by-youtube-dl-is-not-working)
    path = osp.join(config.cfg.music_data_dir, '%(id)s.%(ext)s')
    if not osp.exists(osp.dirname(path)):
        os.makedirs(osp.dirname(path))
    ydl_opts = {
        'format': 'bestaudio/best',
        # Convert to avoid: WARNING: Parameter outtmpl is bytes, but should be a unicode string.
        'outtmpl': unicode(path, 'utf-8'),
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
            'path': osp.join(config.cfg.music_data_dir, id + '.mp3'),
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