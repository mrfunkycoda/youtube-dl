# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
)


class LibraryOfCongressIE(InfoExtractor):
    IE_NAME = 'loc'
    IE_DESC = 'Library of Congress'
    _VALID_URL = r'https?://(?:www\.)?loc\.gov/(?:item/|today/cyberlc/feature_wdesc\.php\?.*\brec=)(?P<id>[0-9]+)'
    _TESTS = [{
        # embedded via <div class="media-player"
        'url': 'http://loc.gov/item/90716351/',
        'md5': '353917ff7f0255aa6d4b80a034833de8',
        'info_dict': {
            'id': '90716351',
            'ext': 'mp4',
            'title': "Pa's trip to Mars",
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 0,
            'view_count': int,
        },
    }, {
        # webcast embedded via mediaObjectId
        'url': 'https://www.loc.gov/today/cyberlc/feature_wdesc.php?rec=5578',
        'info_dict': {
            'id': '5578',
            'ext': 'mp4',
            'title': 'Help! Preservation Training Needs Here, There & Everywhere',
            'duration': 3765,
            'view_count': int,
            'subtitles': 'mincount:1',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        media_id = self._search_regex(
            (r'id=(["\'])media-player-(?P<id>.+?)\1',
             r'<video[^>]+id=(["\'])uuid-(?P<id>.+?)\1',
             r'<video[^>]+data-uuid=(["\'])(?P<id>.+?)\1',
             r'mediaObjectId\s*:\s*(["\'])(?P<id>.+?)\1'),
            webpage, 'media id', group='id')

        data = self._download_json(
            'https://media.loc.gov/services/v1/media?id=%s&context=json' % media_id,
            video_id)['mediaObject']

        derivative = data['derivatives'][0]
        media_url = derivative['derivativeUrl']

        # Following algorithm was extracted from setAVSource js function
        # found in webpage
        media_url = media_url.replace('rtmp', 'https')

        is_video = data.get('mediaType', 'v').lower() == 'v'
        ext = determine_ext(media_url)
        if ext not in ('mp4', 'mp3'):
            media_url += '.mp4' if is_video else '.mp3'

        if 'vod/mp4:' in media_url:
            formats = [{
                'url': media_url.replace('vod/mp4:', 'hls-vod/media/') + '.m3u8',
                'format_id': 'hls',
                'ext': 'mp4',
                'protocol': 'm3u8_native',
            }]
        elif 'vod/mp3:' in media_url:
            formats = [{
                'url': media_url.replace('vod/mp3:', ''),
                'vcodec': 'none',
            }]

        self._sort_formats(formats)

        title = derivative.get('shortName') or data.get('shortName') or self._og_search_title(webpage)
        duration = float_or_none(data.get('duration'))
        view_count = int_or_none(data.get('viewCount'))

        subtitles = {}
        cc_url = data.get('ccUrl')
        if cc_url:
            subtitles.setdefault('en', []).append({
                'url': cc_url,
                'ext': 'ttml',
            })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
            'subtitles': subtitles,
        }