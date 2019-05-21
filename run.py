import os
import time
import pprint
import feedparser


def main():
    ARXIV_BASE_URL = os.environ['ARXIV_BASE_URL']
    ARXIV_SUBJECT = os.environ['ARXIV_SUBJECT']

    while True:
        ARXIV_URL = ARXIV_BASE_URL + ARXIV_SUBJECT
        feed = feedparser.parse(ARXIV_URL)
        pprint.pprint(feed)
        time.sleep(5)


if __name__ == '__main__':
    main()
