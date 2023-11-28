import requests
import itertools
import json
import configparser
from time import sleep
import os

OUTPUT_DIR = "output"
LOG_DIR = "log"
CONFIG_DIR = "config"

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)

API_ENDPOINT = "https://apps.shopify.com/search/autocomplete"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "shopify_search_terms.txt")
CONFIG_FILE = os.path.join(CONFIG_DIR, "shopify_market_autocompleter.ini")
LOG_FILE = os.path.join(LOG_DIR, "shopify_market_autocompleter.log")

params = {
	"v": "3",
	"q": "",
	"st_source": "autocomplete"
}

config = configparser.ConfigParser()

def initializePropertyFile():
	config['DEFAULT'] = {'LastIndex': '0'}
	with open(CONFIG_FILE, 'w') as configfile:
		config.write(configfile)

def getLastIndexProperty():
	config.read(CONFIG_FILE)
	return int(config.get("DEFAULT", "lastIndex"))

def setLastIndexProperty(index):
	config.read(CONFIG_FILE)
	config.sections()
	config.set("DEFAULT", "lastIndex", str(index))
	with open(CONFIG_FILE, 'w') as configfile:
		config.write(configfile)

def generateThreeLetterKeywords():
	alphabets = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
	keywords = itertools.product(alphabets, repeat = 3)
	return [''.join(i) for i in itertools.product(alphabets, repeat = 3)]

def getSearchTermsFromAutoComplete(keyword):
	params["q"] = keyword
	response = requests.get(API_ENDPOINT, params=params)

	searchTerms = []
	if response.status_code == 200:
		try:
			body = response.content.decode('utf8').replace("'", '"')
			jsonObj = json.loads(body)
			
			if 'searches' in jsonObj:
				searches = jsonObj['searches']
				for searchObj in searches:
					searchTerms.append(searchObj['name'])
		except:
			with open(LOG_FILE, 'a') as logFile:
	  			logFile.write("Failed to get search terms for keyword '" + keyword + "'\n")

	return searchTerms

def saveTerms(terms):
	with open(OUTPUT_FILE, 'a') as outputFile:
		for term in terms:
			outputFile.write(term + "\n")

def throttle(index):
	if (index+1) % 500 == 0:
		sleep(60 * 5)
	elif (index+1) % 100 == 0:
		sleep(60)
	else:
		sleep(3)

def main():
	lastSearchedIdx = getLastIndexProperty()
	keywords = generateThreeLetterKeywords()
	keywords = keywords[lastSearchedIdx:]

	for index, word in enumerate(keywords):
		searchTerms = getSearchTermsFromAutoComplete(word)
		print("[{}/{}] Got {} terms from.....{}".format(index + 1, len(keywords), len(searchTerms), word))
		saveTerms(searchTerms)
		
		lastSearchedIdx += 1
		setLastIndexProperty(lastSearchedIdx)
		throttle(index)

if __name__ == "__main__":
	# initializePropertyFile()
    main()