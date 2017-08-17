# To run tests, execute
#   python test_crawler.py
# on the command line. If tests pass, exit using ctrl-C, and ignore
# the stack trace this generates.

import unittest
from crawler import crawler
from bottle import get, post, request, run, route, static_file
from multiprocessing import Process
import os
import urllib2


# Manually verified results which depend on a number of key
# requirements for the crawler.
test_case_result = {
    'world': set([
        'http://localhost:8080/test_files/test3/test.html',
        'http://localhost:8080/test_files/test.html']),
    'test2': set([
        'http://localhost:8080/test_files/test3/test.html']),
    'hello': set([
        'http://localhost:8080/test_files/test3/test.html',
        'http://localhost:8080/test_files/test3/test2.html',
        'http://localhost:8080/test_files/test.html',
        'http://localhost:8080/test_files/test2.html']),
    'marvin': set([
        'http://localhost:8080/test_files/test3/test2.html',
        'http://localhost:8080/test_files/test2.html'])}

class TestCrawler(unittest.TestCase):
    def test_crawler(self):
        """
        Tests the crawler by comparing its results to manually verified results.
        """
        global test_case_result

        # Run the crawler and store the results.
        bot = crawler(None, "test.txt")
        bot.crawl(depth=1)
        inverted_index = bot.get_inverted_index()
        resolved_inverted_index = bot.get_resolved_inverted_index()
        
        # Check that the result contains the correct number of words.
        self.assertTrue(len(resolved_inverted_index) == len(test_case_result), "incorrect number of words found.")

        for key in resolved_inverted_index:
            # Check that each word is in the precomputed results.
            self.assertTrue(key in test_case_result, "unexpected word: {key}.".format(key = key))
            
            # Check that each word maps to the correct number of urls.
            self.assertTrue(
                len(resolved_inverted_index[key]) == len(test_case_result[key]),
                "incorrect number of urls for word: {key}.".format(key = key))

               
            for url in resolved_inverted_index[key]:
                # Check that each url is correct.
                self.assertTrue(url in test_case_result[key], "unexpected url: <{url}>.".format(url = url))
            

@get('/test_files/<filename:path>')
def fetch(filename):
    return static_file(filename, root=os.path.join(os.getcwd(), 'test_files'))
        
if __name__ == "__main__":
    # Start test_file server.
    p = Process(target=run, kwargs=dict(host='localhost', port=8080))
    p.start()

    # Wait for test_file server to become available.
    while True:
        socket = None
        try:
            socket = urllib2.urlopen('http://localhost:8080/test_files/test.html', timeout=3)
            break
        except Exception as e:
            continue
        finally:
            if socket:
                socket.close()

    # Execute tests.
    unittest.main()

    # Terminate server.
    p.terminate()
