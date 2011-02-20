#!/usr/bin/python
"""
Tomatwo - The Mean Twitting Machine
(c) 2011 - Emmanuel Goossaert 
Under BSD License
"""


import random
import time
import sqlite3

# TODO: need to make an object with all that, to have conn and cursor encapsulated and avoid to have them as parameters and/or globals

def exists_url( cursor, url ):
    query = 'select * from article where url_article="%s"' % (url)
    #print query
    cursor.execute(query) 
    for row in cursor:
        return True
    return False


def exists_table( cursor, name ):
    cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='%s';""" % name)
    for row in cursor:
        return True
    return False


def delete_articles( conn, cursor, date ):
    cursor.execute( 'delete from article where date_crawled <= %d' % (date) )
    conn.commit()


def get_random_non_tweeted_article( cursor ):
    # TODO: just do a count and then select one article with LIMIT
    date_limit = int( time.time() ) - 86400 * 3
    query = 'select * from article where date_tweeted=0 and date_crawled >= %d' % (date_limit)
    #print query
    cursor.execute(query) 

    rows = []
    for row in cursor:
        #print row
        rows.append( row )

    #num = random.randint(0, len(rows) - 1)
    row_article = random.sample( rows, 1 )[ 0 ]
    article = {}
    fields = [ 'id', 'date_updated', 'date_crawled', 'date_tweeted', 'url_source', 'url_feed', 'url_article', 'url_short', 'title', 'author' ]
    for index, field in enumerate( fields ):
        article[ field ] = row_article[ index ]

    #article['id']           = row_article[ 0 ]
    #article['date_updated'] = row_article[ 1 ]
    #article['date_crawled'] = row_article[ 2 ]
    #article['date_tweeted'] = row_article[ 3 ]
    #article['url_source']   = row_article[ 4 ]
    #article['url_feed']     = row_article[ 5 ]
    #article['url_article']  = row_article[ 6 ]
    #article['url_short']    = row_article[ 7 ]
    #article['title']        = row_article[ 8 ]
    #article['author']       = row_article[ 9 ]
    return article


def get_latest_date( conn, cursor ):
    cursor.execute('select * from article order by id')
    for row in cursor:
        print row
    #print exists_url( cursor, "http://test.com" )
    #sql.commit()


def delete_date( conn, cursor, id ):
    cursor.execute('delete from tweet_date where id=%d' % id)
    conn.commit()


def create_table( conn, cursor ):
    if not exists_table(cursor, 'article'):
        cursor.execute('''CREATE TABLE article (id integer primary key,
                                                date_updated integer,
                                                date_crawled integer,
                                                date_tweeted integer,
                                                url_source text,
                                                url_feed text,
                                                url_article text,
                                                url_short text,
                                                title text,
                                                author text)''')

        cursor.execute('''CREATE TABLE tweet_date (id integer primary key,
                                                   date integer)''')

        cursor.execute('''CREATE TABLE tweet_date (id integer primary key,
                                                   date integer)''')

        conn.commit()


def escape_title( title ):
    return title.replace('"', ' ')


def insert_url( conn, cursor, date_updated, url_source, url_feed, url_article, title, author ):
    #date_crawled = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
    date_crawled = int( time.time() )
    if not exists_url( cursor, url_article ):
        query = """insert into article
                   (date_updated, date_crawled, date_tweeted, url_source, url_feed, url_article, url_short, title, author)
                   values (%d, %d, 0, "%s", "%s", "%s", "None", "%s", "%s")""" % (date_updated, date_crawled, url_source, url_feed, url_article, escape_title(title), author)
        cursor.execute(query)
        conn.commit()
        return True
    else:
        return False


def insert_date( conn, cursor, date ):
    query = """insert into tweet_date
               (date)
               values (%d)""" % (date)
    cursor.execute(query)
    conn.commit()


def update_article( conn, cursor, article, exclude=None ):
    if exclude == None: exclude = [] 
    string_set = ", ".join( "%s='%s'" % (k, v) for k, v in article.iteritems() if k not in ["id"] )
    cursor.execute("""update article
                      set %s
                      where id=%d""" % ( string_set, article['id'] ))
    conn.commit()


def select_next_date( conn, cursor ):
    date_current = int( time.time() )
    cursor.execute('select * from tweet_date order by date limit 1')
    for row in cursor:
        if row[ 1 ] <= date_current:
            return row[ 0 ]
    return -1
    #
    

def update_date_and_url( conn, cursor, article ):
    cursor.execute("""update article
                      set url_short='%s', date_tweeted=%d
                      where id=%d""" % ( article[5], article[2], article[0] ))
    conn.commit()


def connect():
    return sqlite3.connect('rss.db')


if __name__=="__main__":

    conn = connect()
    cursor = conn.cursor()

    import sys
    if( len(sys.argv) == 2 ):
        if( sys.argv[1] == 'create' ):
            print 'creating...'
            create_table( conn, cursor )
            conn.commit()
        elif( sys.argv[1] == 'drop' ):
            print 'droping...'
            cursor.execute('drop table article')
            cursor.execute('drop table tweet_date')
            conn.commit()
        elif( sys.argv[1] == 'delete' ):
            print 'deleting...'
            cursor.execute('delete from article')
            cursor.execute('delete from tweet_date')
            conn.commit()
    else:
        cursor.execute('select * from article order by id')
        for row in cursor:
            print row

        cursor.execute('select * from tweet_date order by id')
        for row in cursor:
            print row

    cursor.close()
