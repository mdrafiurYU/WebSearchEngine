import sqlite3
from operator import itemgetter

class DBHandler:
    def __init__(self):
        self.conn = sqlite3.connect('crawler.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS lexicon (word_id integer, word text)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS inverted_index (word_id integer, doc_id integer)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS pagerank (doc_id integer, rank real)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS doc_index (doc_id integer, url text)''')
        self.conn.commit()

    def get_word_id(self, word):
        self.cursor.execute('''
            SELECT word_id 
            FROM   lexicon 
            WHERE  word=?''', (word,))
        return self.cursor.fetchone()

    def get_doc_ids(self, word_id):
        self.cursor.execute('''
            SELECT doc_id
            FROM   inverted_index
            WHERE  word_id=?''', word_id)

        return self.cursor.fetchall()
                            

    def get_pageranks(self, doc_ids):
        def get_pagerank(doc_id):
            self.cursor.execute('''
                SELECT rank
                FROM   pagerank
                WHERE  doc_id=?''', doc_id)
            return self.cursor.fetchone()

        return map(get_pagerank, doc_ids)

    def get_urls(self, doc_ids):
        def get_url(doc_id):
            self.cursor.execute('''
                SELECT url
                FROM   doc_index
                WHERE  doc_id=?''', doc_id)
            return self.cursor.fetchone()

        return map(get_url, doc_ids)

    def put_lexicon(self, lexicon):
        self.cursor.executemany('''
            INSERT INTO lexicon
            VALUES (?, ?)''', lexicon.iteritems())
        self.conn.commit()

    def put_inverted_index(self, inverted_index):
        print inverted_index
        entries = [(key, value)
            for key in inverted_index.keys()
                for value in inverted_index[key]]

        self.cursor.executemany('''
            INSERT INTO inverted_index
            VALUES (?, ?)''', entries)
        self.conn.commit()

    def put_pageranks(self, pageranks):
        self.cursor.executemany('''
            INSERT INTO pagerank
            VALUES (?, ?)''', pageranks.items())
        self.conn.commit()

    def put_doc_index(self, doc_index):
        self.cursor.executemany('''
            INSERT INTO doc_index
            VALUES (?, ?)''', doc_index.items())
        self.conn.commit()

    def close(self):
        self.conn.close()
