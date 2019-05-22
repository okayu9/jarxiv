import os
import sys
import re
import time
import json
import requests
import feedparser
import googletrans


def get_arxiv_url_from_envvar():
    if 'ARXIV_BASE_URL' not in os.environ:
        print('ERROR: ARXIV_BASE_URL is not set in env.', file=sys.stderr)
        sys.exit(-1)
    if 'ARXIV_SUBJECT' not in os.environ:
        print('ERROR: ARXIV_SUBJECT is not set in env.', file=sys.stderr)
        sys.exit(-1)

    return os.environ['ARXIV_BASE_URL'] + os.environ['ARXIV_SUBJECT']


def get_dest_lang_from_envvar():
    if 'DEST_LANG' not in os.environ:
        print('ERROR: DEST_LANG is not set in env.', file=sys.stderr)
        sys.exit(-1)
    DEST_LANG = os.environ['DEST_LANG']
    if DEST_LANG not in googletrans.LANGUAGES.keys():
        print(f'ERROR: DEST_LANG: {DEST_LANG} is not supported.', file=sys.stderr)
        sys.exit(-1)

    return DEST_LANG


def get_arxiv_vanity_base_url_from_envvar():
    if 'ARXIV_VANITY_BASE_URL' not in os.environ:
        return None
    return os.environ['ARXIV_VANITY_BASE_URL']


def get_slack_webhook_url_from_envvar():
    if 'SLACK_WEBHOOK_URL' not in os.environ:
        print('ERROR: SLACK_WEBHOOK_URL is not set in env.', file=sys.stderr)
        sys.exit(-1)
    return os.environ['SLACK_WEBHOOK_URL']


def get_slack_user_info_from_envvar():
    SLACK_USERNAME = os.environ['SLACK_USERNAME'] if 'SLACK_USERNAME' in os.environ else None
    SLACK_ICON_EMOJI = os.environ['SLACK_ICON_EMOJI'] if 'SLACK_ICON_EMOJI' in os.environ else None
    SLACK_CHANNEL = os.environ['SLACK_CHANNEL'] if 'SLACK_CHANNEL' in os.environ else None

    slack_user_info = {}
    if SLACK_USERNAME:
        slack_user_info['username'] = SLACK_USERNAME
    if SLACK_ICON_EMOJI:
        slack_user_info['icon_emoji'] = SLACK_ICON_EMOJI
    if SLACK_CHANNEL:
        slack_user_info['channel'] = SLACK_CHANNEL

    return slack_user_info


def handling_feed_error(feed):
    if feed.bozo == 0:
        # success
        return
    elif 'status' not in feed.keys():
        print('unreachable to the server', file=sys.stderr)
    elif feed['status'] != 200:
        print('reachable but not OK(200)', file=sys.stderr)
    else:
        print('OK(200) but not rss', file=sys.stderr)
    print(feed.bozo_exception, file=sys.stderr)
    sys.exit(-1)


def get_paper_info_from_entry(entry, translator, DEST_LANG, ARXIV_VANITY_BASE_URL):
    url = entry['link']
    uid = re.sub(r'^.*\/', '', url)
    if entry['title'].endswith('] UPDATED)'):
        return False
    title = re.sub(r' \(arXiv:.*? \[.*?\]\)$', '', entry['title'])
    abstract = entry['summary'][3:-4].replace('\n', ' ').strip()
    title_dest = translator.translate(title, src='en', dest=DEST_LANG).text
    abstract_dest = translator.translate(abstract, src='en', dest=DEST_LANG).text
    if ARXIV_VANITY_BASE_URL:
        arxiv_vanity_url = ARXIV_VANITY_BASE_URL + uid + '/'
    else:
        arxiv_vanity_url = None
    return {
        'url': url,
        'title': title,
        'title_dest': title_dest,
        'abstract': abstract,
        'abstract_dest': abstract_dest,
        'arxiv_vanity_url': arxiv_vanity_url
    }


def combine_paper_info_to_text(paper_info):
    title = paper_info['title']
    title_dest = paper_info['title_dest']
    abstract_dest = paper_info['abstract_dest']
    url = paper_info['url']
    arxiv_vanity_url = paper_info['arxiv_vanity_url']

    text = f'*{title_dest} | {title}*\n'
    text += f'{abstract_dest}\n'
    text += f'[<{url}|arXiv>]'
    if arxiv_vanity_url:
        text += f' [<{arxiv_vanity_url}|arXiv Vanity>]'

    return text


def main():
    ARXIV_URL = get_arxiv_url_from_envvar()
    DEST_LANG = get_dest_lang_from_envvar()
    ARXIV_VANITY_BASE_URL = get_arxiv_vanity_base_url_from_envvar()
    SLACK_WEBHOOK_URL = get_slack_webhook_url_from_envvar()
    slack_user_info = get_slack_user_info_from_envvar()

    translator = googletrans.Translator()

    updated = ''

    while True:
        feed = feedparser.parse(ARXIV_URL)
        handling_feed_error(feed)
        if feed['updated'] == updated:
            time.sleep(10 * 60)
            continue
        updated = feed['updated']
        print(f'updated at {updated}')

        datas_to_send_to_slack = []
        for entry in feed['entries']:
            paper_info = get_paper_info_from_entry(entry, translator, DEST_LANG, ARXIV_VANITY_BASE_URL)
            if paper_info == False:
                continue
            paper_info_text = combine_paper_info_to_text(paper_info)
            data_to_send_to_slack = {'text': paper_info_text, **slack_user_info}
            datas_to_send_to_slack.append(json.dumps(data_to_send_to_slack))

        for data_to_send_to_slack in datas_to_send_to_slack:
            requests.post(SLACK_WEBHOOK_URL, data=data_to_send_to_slack)

        time.sleep(10 * 60)


if __name__ == '__main__':
    main()
