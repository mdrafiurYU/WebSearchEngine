import math
import sys
import string
import urllib
import urlparse
from functools import wraps
from operator import itemgetter, and_
from time import sleep

from bottle import get, post, error, request, run, route, static_file, template, redirect, app, hook, response
import beaker.middleware

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import OAuth2WebServerFlow, httplib2 

from database import DBHandler

# Set session perameters
session_opts = {
    'session.type': 'file',
    'session.data_dir': './session/',
    'session.auto': True,
}

# Start the session
app = beaker.middleware.SessionMiddleware(app(), session_opts)

# Global dictionary to hold the search history of users. Keys are user's emails
user_top_20_database = {}

# Whether to hang the server
hang = False

math_chars = string.digits + string.whitespace + ".+-*^/\%()[]"


def check_hang(func):
	@wraps(func)
	def inner(*args, **kwargs):
		while hang:
			sleep(60)
		return func(*args, **kwargs)
	return inner

# This route provides access to the homepage logo.
@route('/ollerus.gif', method='GET')
@check_hang
def get_logo():
    return static_file('ollerus.gif', '.')

@route('/kill', method='GET')
@check_hang
def kill():
    global hang
    hang = True

# This route provides access to the square logo.
@route('/style.css', method='GET')
@check_hang
def get_style():
    return static_file('style.css', '.')

# This route will define the home page.
# There is a form query that is a text box, and captures the user's search in a
# variable called "keywords". If this variable is provided to the route, it will
# instead provide the results of the request.
@route('/')
@check_hang
def homepage_search():
	
	# Provide access to the search history dictionary
	global user_top_20_database

	keywords = request.query.get('keywords')
	if keywords != None and keywords != "":
		return do_search(keywords)

	# Fetch the current session
	request_session = request.environ['beaker.session']

	# Fetch the users email for their session
	user_email = request_session.get("user_email", "Anonymous")

	# If the user email does not yet exist in the database
	if user_top_20_database.get(user_email) == None:
		# Add it and set their search history to an empty list
		user_top_20_database[user_email] = []
	
	# Initialize the users history
	user_top_20 = []

	# If the user is not in Anonymous mode
	if user_email != 'Anonymous':
		# Fetch the top 20 list for that users email
		user_top_20 = user_top_20_database.get(user_email)


	return template('''
		<head>
			<link rel="stylesheet" type="text/css" href="/style.css" />
		</head>
			<body>
				<br>
				%if user_email == 'Anonymous':
					<form action="/login" class="inline" align ="right">
						<button class="float-left submit-button" >Sign In</button>
					</form>
				%else:
					<form action="/signout" class="inline" align="right">
						<button class="float-left submit-button" >Sign Out</button>
					</form>
				%end

				<center>
				    <img src="ollerus.gif" alt="ollerus" style="width:300px;height:106px;">
					<br><br>
					<div class = "nowrapcontainer">
						<form action="/" method="GET">
						    <input name="keywords" type="text" size = "45" /><!--
						    --><input value = "Search" type="submit" />
						</form>
					</div>

				</center>
				%if user_email != 'Anonymous':
					<p align="right"> Logged in as: {{user_email}} </p>
					<p align="right"> <a href='/history'>History</a> </p>
				%else:
					<p align="right"> Browsing Anonymously </p>
				%end
			</body>

            ''', user_top_20 = user_top_20, user_email = user_email)

# This function pulls the users query and analyzes it. It takes the user's input string and
# partitions it into separate elements. Calls table creation is managed if the query length
# is greater than 1 word.
def do_search(keywords):

	global user_top_20_database
	
	# Fetch the current session
	request_session = request.environ['beaker.session']
	# Fetch the users email for their session
	user_email = request_session.get('user_email', 'Anonymous')
   
   	if reduce(and_, map(lambda c: c in math_chars, keywords)):
		result = None
		try:
			result = eval(keywords.replace('^', '**').replace('[', '(').replace(']', ')'))
			return result_template(user_email, keywords, template('''
				<p> {{keywords}} = {{result}} </p>
				''', keywords=keywords, result=result))
		except Exception as e:
			pass
	

	# A list of all keywords from the search query.
	keyword_list = map(str.lower, keywords.split())
	keywords = keyword_list
#-----------------------------------------------------------------------
	counted_keyword_list = [(keyword_list.count(x),x) for x in set(keyword_list)]
	# Sort the list in descending order of frequency.
	counted_keyword_list.sort(key=wordCount, reverse = 1)
	
	page = request.query.get('page')
	if user_email <> 'anonymous' and page == None:
		# Fetch the top 20 list for that users email
		user_top_20 = user_top_20_database.get(user_email)

		if user_top_20 != None:
			# Add to the top 20 list and update totals.
			# Iterate through the counted keyword list.
			for keywords1 in counted_keyword_list:
				# If any keywords are already in the top 20 list, merge them into the top 20 list.
				if any(keywords1[1] in element for element in user_top_20):
					# Iterator to keep track of which keyword in the top 20 list we are at.
					i = 0
					# Iterate through the keyword pairs and add the values from the counted_keyword_list into the top20 list.
					for keywords2 in user_top_20:
						# If the keywords match.
						if keywords2[1] == keywords1[1]:
							# Save the count value of the user_top_20 version.
							keyword_count = keywords2[0]
							# Delete the old user_top_20 keyword and count.
							del user_top_20[i]
							# Add the keyword with updated count to the front of the top_20 list.
							user_top_20.insert(0,((keywords1[0] + keyword_count),keywords1[1]))
						# Iterate
						i = i+1

				# If the word isn't already in the top 20 list add it.
				else:
					user_top_20.append(keywords1)

			# Organize the top 20 list in decending order by the frequency of a keyword.
			user_top_20.sort(key=wordCount, reverse = 1)

			# Update the database of user search history
			user_top_20_database["user_email"] = user_top_20

			# If the user_top_20 list is longer than 20 keywords, trim it.
			# while len(user_top_20) > 20:
			#	del user_top_20[-1]

		
		

#------------------------------------------------------------------------
	
	# Grab the first keyword that was inputted by the user
	if keyword_list == []:
		results_list = []
		return generate_page_results(1, results_list, [], user_email)

	if page == None:
		page = 1
	else:
		page = int(page)

	db = DBHandler()

	# Get the word_ids through a getter in the database
	word_ids = []
	ignored_words = set([
		'', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
		'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
		'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
		'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
	])

	for keyword in keyword_list:
		if keyword in ignored_words:
			continue
		word_ids.append(db.get_word_id(keyword))


	# Get the doc_ids from the word_ids in the database
	list_of_doc_id_lists = []
	for word_id in word_ids:
		if word_id == None:
			list_of_doc_id_lists.append([])
		else:
			list_of_doc_id_lists.append(db.get_doc_ids(word_id))

	# Find lists of doc_ids that intersect with each other, this will give us doc ids that contain both keywords
	intersecting_doc_ids = find_intersections(list_of_doc_id_lists)

	# Get the url_ranks from pagerank in the database
	ranks = db.get_pageranks(intersecting_doc_ids)

	# Zip the doc_ids with the corresponding url_ranks to make ranked_doc_ids
	ranked_doc_ids = zip(ranks, intersecting_doc_ids)

	# Sort the ranked_doc_ids to make sorted_doc_ids and get the sorted_urls from the database
	ranked_sorted_doc_ids = sorted(ranked_doc_ids, key = itemgetter(0))
	results_list = map(itemgetter(0), db.get_urls(map(itemgetter(1), ranked_sorted_doc_ids)))
	return generate_page_results(page, results_list, keyword_list, user_email)

def result_template(user_email, keywords, html_results):
	return template('''
			<html>
				<head>
					<link rel="stylesheet" type="text/css" href="/style.css" />
					<style>
						div.demo {
							display: table;
							width: 100%;
							table-layout: fixed;    /* For cells of equal size */
						}
						div.demo span {
							vertical-align: top;
							display: table-cell;
							text-align: center;
						}
						div.demo span:first-child {
							text-align: left;
						}
						div.demo span:last-child {
							text-align: right;
						}
						.searchBar {
							overflow-x: visible;
							white-space: nowrap;
						}
					</style>
				</head>
				<body>
				<br><br>
					<div class="demo">
						<span>
							<a href="/">
							<img src="ollerus.gif" alt="olleruslogo" style="width:135px;height:48px;">
							</a>
						</span>
						<span>
							<div class = "searchBar">
								<form style = action="/" method="GET">
									<input name="keywords" type="text", value="{{keywords}}" size="35"/><!--
									--><input value = "Search" type="submit" />
								</form>
							</div>
						</span>
						<span>
							%if user_email == 'Anonymous':
								<form action="/login">
									<button class="float-left submit-button" >Sign In</button>
								</form>
							%else:
								<form action="/signout">
									<button class="float-left submit-button" >Sign Out</button>
								</form>
							%end
						</span>
					</div>
					<hr>
			''', user_email=user_email, keywords=keywords) + html_results + template('''
				%if user_email != 'Anonymous':
					<p align="right"> Logged in as: {{user_email}} </p>
				%else:
					<p align="right"> Browsing Anonymously </p>
				%end
				</body>
			</html>
			''', user_email=user_email)

	
def generate_page_results(page, results_list, keyword_list, user_email):
	if results_list != []:
		keywords = ' '.join(keyword_list)
		return result_template(user_email, keywords, template('''
			%if page == 1:
				%for result in results_list[:5]:
					<p> <a href={{result}}>{{result}}</a> </p>
				%end
	
			%elif len(results_list[(page-1)*5:]) < 5:
				%for result in results_list[((page-1)*5):]:
					<p> <a href={{result}}>{{result}}</a> </p>
				%end

			%else:
				%for result in results_list[(page-1)*5:((page-1)*5)+5]:
					<p> <a href={{result}}>{{result}}</a> </p>
				%end
			%end
			<center>
				%if len(results_list) > 5:
					Go to Page:
					<form action="/" method="GET">
						<input name="keywords" value="{{keywords}}" type="hidden" />
						<div id="buttons">
							%if page != 1:
								<input type="submit" class="f" name="page" value="{{page-1}}">
							%end
							%if len(results_list[(page-1)*5:]) > 5:
								<input type="submit" class="f" name="page" value="{{page+1}}">
							%end
							<div style="clear:both"></div>
						</div>
					</form>
				%end
			</center>
			''', results_list=results_list, keywords=keywords, page=page))

	else:
		return template('''
			<head>
				<link rel="stylesheet" type="text/css" href="/style.css" />
			</head>
			<body>				
				<center>
					<b>OH NO!</b> 
					<p>This is a travesty.</p>
					<p>We couldn't find what you were looking for.</p>
					<p>Why don't you try another search?</p>
			
					<form action="/" method="GET">
						<input name="keywords" type="text" /><!--
						--><input value = "Try Again" type="submit" />
					</form>
				</center>
			<body>
			''')

def wordCount(word):
     return word[0]

def find_intersections(list_of_lists):
	if len(list_of_lists) == 0:
		return []
	
	prev_seen = set(list_of_lists[0])
	curr_seen = set()
	for l in list_of_lists[1:]:
		for item in l:
			if item in prev_seen:
				curr_seen.add(item)
		prev_seen, curr_seen = curr_seen, set()

	return list(prev_seen)

@route('/history', 'GET')
@check_hang
def show_history():
	# Fetch the current session
	request_session = request.environ['beaker.session']
	# Fetch the users email for their session
	user_email = request_session.get('user_email', 'Anonymous')
	
	# Fetch the top 20 list for that users email
	user_top_20 = user_top_20_database.get(user_email)
	
	return template('''
		<right>		
			<a align href="/">
				<img src="ollerus.gif" alt="olleruslogo" style="width:135px;height:48px;">
			</a>
		</right>
		<center>
			<table border = "1" id = "history">
				<th colspan="2">HISTORY</th>
				</thead>
				%for count, word in user_top_20:
					<tr>
					    <td>{{word}}</td>
					    <td>{{count}}</td>
					</tr>
				%end
			</table>
		<center>
		''', user_top_20 = user_top_20, user_email = user_email)

# This route will define the signout page.
# It will terminate and delete the users session and redirect to the home page
@route('/signout', 'GET')
@check_hang
def signout():
	request_session = request.environ['beaker.session']
	request_session.delete()
	redirect('/')

# This route will define the login page.
# This page starts the authentication process with Google's API
@route('/login', 'GET')
@check_hang
def login():
	flow = flow_from_clientsecrets("client_secrets.json",
					scope=['https://www.googleapis.com/auth/plus.me','https://www.googleapis.com/auth/userinfo.email'],
					redirect_uri="http://localhost:8080/redirect")
	uri = flow.step1_get_authorize_url()
	redirect(str(uri))

# This route will define the login redirect page
# After initial steps of authentication, this page will finish the process
# It captures all user data obtained from Google's API and stores it in the current session
@route('/redirect', 'GET')
@check_hang
def redirect_page():
	code = request.query.get('code', '')
	CLIENT_ID = "1089760586264-m3m2g136v6a8c1po80qq8f8jfalgqegs.apps.googleusercontent.com"
	CLIENT_SECRET = "y5R1bemcTK8Sv_iY9EaAeBuw"
	SCOPE = ['https://www.googleapis.com/auth/plus.me','https://www.googleapis.com/auth/userinfo.email']
	REDIRECT_URI = 'http://localhost:8080/redirect'
	flow = OAuth2WebServerFlow( client_id=CLIENT_ID,
					client_secret=CLIENT_SECRET,
					scope=SCOPE,
					redirect_uri=REDIRECT_URI)

	credentials = flow.step2_exchange(code)

	token = credentials.id_token['sub']

	http = httplib2.Http()
	http = credentials.authorize(http)

	# Get user email
	users_service = build('oauth2', 'v2', http=http)
	user_document = users_service.userinfo().get().execute()
	user_email = user_document['email']

	# Store all user credentials in the beaker session
	request_session = request.environ['beaker.session']
	request_session['users_service'] = users_service
	request_session['user_document'] = user_document
	request_session['user_email'] = user_email
	request_session['is_logged_in'] = True
	request_session['user_top_20'] = []
	# Return to homepage
	redirect('/')

@error(404)
@check_hang
def error404(error):
    return template('''
		<center>
			<p> Looks like what you want doesn't exist... </p>
			<p> How unfortunate. </p>
			<p> Why don't you go try our <a href='/'>homepage</a>? </p>
		</center>
		''')

if __name__ == '__main__':
    run(app)

