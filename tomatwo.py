#!/usr/bin/python
"""
Tomatwo - The Mean Twitting Machine
(c) 2011 - Emmanuel Goossaert 
Under BSD License
"""

import urllib2
import time
import random
import ConfigParser

import tweepy
import bitly
import feedparser

import rssdb


# Loading settings from file
config = ConfigParser.RawConfigParser()
config.read('settings.cfg')

CONSUMER_KEY        = config.get("twitter", "consumer_key")
CONSUMER_SECRET     = config.get("twitter", "consumer_secret")
ACCESS_TOKEN        = config.get("twitter", "access_token")
ACCESS_TOKEN_SECRET = config.get("twitter", "access_token_secret")
LEN_MAX_TWEET       = int(config.get("twitter", "len_max_tweet"))

BITLY_LOGIN         = config.get("bitly", "login")
BITLY_KEY           = config.get("bitly", "key")


def send_tweet( tweet ):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    bot = tweepy.API(auth, secure=True, retry_count=10)
    bot.update_status( tweet )


def shorten_url( url ):
    bitly_api = bitly.Api( login=BITLY_LOGIN, apikey=BITLY_KEY )
    return bitly_api.shorten( url )

def is_internet_available():
    import urllib2
    urls = ['http://www.google.com',
            'http://www.bing.com',
            'http://www.yahoo.com',
            'http://www.microsoft.com',
            'http://www.facebook.com',
            'http://www.twitter.com' ]

    random.shuffle( urls )
    for url in urls:
        try:
            urllib2.urlopen( url )
        except:
            continue
        return True

    return False



def plan_current_day( conn, cursor ):
    # TODO: modify to have tweet type (link or message) and to have
    # the distribution as a parameter, along with starting and ending times
    seconds_start = int( time.time() ) + 3600 * 10 # no tweets before 10am
    seconds_end   = int( time.time() ) + 86400

    #nb_tweets = random.randint(2, 4)
    nb_tweets = abs(int( random.gauss( 2, 1 ) ))

    interval = int( (seconds_end - seconds_start) / ( nb_tweets + 1 ) )

    for index in range(nb_tweets):
        randomness = 3600 * 2 
        seconds = seconds_start + interval * index + random.randint( - randomness, randomness )
        rssdb.insert_date( conn, cursor, seconds )


def make_tweet( article ):
    tweet = article['title'][0: LEN_MAX_TWEET - len(article['url_short']) - 1] + ' ' + article['url_short']
    return tweet


def handle_tweet( conn, cursor ):
    article = rssdb.get_random_non_tweeted_article( cursor )
    article[ 'date_tweeted' ] = int( time.time() )
    article[ 'url_short' ] = shorten_url( article['url_article'] )
    rssdb.update_article( conn, cursor, article, ['content'] )
    tweet = make_tweet( article )
    send_tweet( tweet )


def filter_feed_url( url ):
    url_return = url
    if url.startswith("http://feedproxy"):
        data = urllib2.urlopen( url )
        url_return = data.geturl()
        data.close()
        pos = url_return.find('?utm_source')
        url_return = url_return[:pos]
    #print 'filter', url, 'to', url_return
    return url_return


def get_content_url( url ):
    content = ""
    try:
        fd = urllib2.urlopen( url )
        content = fd.read()
        fd.close()
    except:
        pass
    return content


def parse_feed( conn, cursor, url ):

    d = feedparser.parse( url )
    print "Parsing:", d.feed.title
    #print d.channel.title
    print d.feed.link
    #print d.feed.subtitle
    for entry in d.entries:
        updated_parsed = 0
        if 'updated_parsed' in entry:
            updated_parsed = time.mktime( entry.updated_parsed )
            #updated_parsed = time.mktime( time.strftime(entry.updated_parsed, "%Y-%m-%d %H:%M") )

            #seconds_date_start = time.mktime( time.strptime(date_start, "%Y-%m-%d %H:%M") )

        author = "None"
        if 'author' in entry:
            author = entry.author

        url_feed = entry.link
        url_article = filter_feed_url( entry.link )

        #content = get_content_url( url_article )
        #if content == "":
        #    print "Cannot retrieve:", url_article
        #    continue

        ret = rssdb.insert_url( conn=conn,
                                cursor=cursor,
                                date_updated=updated_parsed,
                                url_source=d.feed.link,
                                url_feed=url_feed,
                                url_article=url_article,
                                title=entry.title,
                                author=author )
        #if ret:
        #    print "Added:", entry.link


def cleanup_db( conn, cursor ):
    date = int( time.time() ) - 86400 * 15  # delete articles more than 15 days old
    rssdb.delete_articles( conn, cursor, date )


if __name__=="__main__":
    import sys
    if not is_internet_available():
        exit()
    random.seed( time.time() )
    conn = rssdb.connect()
    cursor = conn.cursor()

    if( len( sys.argv ) == 2 ):
        if( sys.argv[ 1 ] == 'crawl' ):
            f = open( 'rss.txt', 'r' )
            for line in f.readlines():
                line = line.strip()
                if( line and not line.strip().startswith('#') ):
                    parse_feed( conn, cursor, line ) 
            f.close()
            cleanup_db( conn, cursor )
        elif( sys.argv[ 1 ] == 'plan' ):
            plan_current_day( conn, cursor )
        elif( sys.argv[ 1 ] == 'check' ):
            id = rssdb.select_next_date( conn, cursor )
            if id > 0:
                handle_tweet( conn, cursor )
                rssdb.delete_date( conn, cursor, id )
        

    cursor.close()

