import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
import configparser
from time import sleep
import os

ENDPOINT = "https://apps.shopify.com/search"
params = {
	"q": ""
}
headers = {
	"Turbo-Frame": "search_page",
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
	"Postman-Token": "160ece74-2bfe-4f27-9155-fd0e366f29a9",
	"Host": "apps.shopify.com",
	"Cookie": "_s=20c5f02e-0c5f-4f99-b725-ac6ab9ea9d3e; _shopify_s=20c5f02e-0c5f-4f99-b725-ac6ab9ea9d3e; _shopify_y=285cf33d-9626-485a-bdb7-e68fecc04d02; _y=285cf33d-9626-485a-bdb7-e68fecc04d02; _shopify-app_store_session5=ba9d52c11364f984e999640261d7e43a"
}

OUTPUT_DIR = "output"
LOG_DIR = "log"
CONFIG_DIR = "config"

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "shopify_app_links.txt")
SEARCH_TERMS_FILE = os.path.join(OUTPUT_DIR, "shopify_search_terms.txt")
LOG_FILE = os.path.join(LOG_DIR, "shopify_market_scraper.log")
CONFIG_FILE = os.path.join(CONFIG_DIR, "shopify_market_scraper.ini")

config = configparser.ConfigParser()
searchTerms = []
linksTable = set()
currentUrl = ""

def initializePropertyFile():
	config['DEFAULT'] = {'LastIndex': '0'}
	with open(CONFIG_FILE, 'w') as configfile:
		config.write(configfile)

def getLastIndexProperty():
	if not os.path.isfile(CONFIG_FILE):
		initializePropertyFile()
	config.read(CONFIG_FILE)
	return int(config.get("DEFAULT", "lastIndex"))

def setLastIndexProperty(index):
	if not os.path.isfile(CONFIG_FILE):
		initializePropertyFile()
	config.read(CONFIG_FILE)
	config.sections()
	config.set("DEFAULT", "lastIndex", str(index))
	with open(CONFIG_FILE, 'w') as configfile:
	  	config.write(configfile)

def loadSearchTerms():
	global searchTerms
	termsFile = open(SEARCH_TERMS_FILE, 'r')
	searchTerms = termsFile.read().splitlines()
	termsFile.close()

def buildLinksTable():
	global linksTable
	if os.path.isfile(OUTPUT_FILE):
		with open(OUTPUT_FILE, 'r') as linksFile:
			links = linksFile.read().splitlines()
			for link in links:
				linksTable.add(link.split("?")[0])

def log(errorMessage):
	with open(LOG_FILE, 'a') as logFile:
	  	logFile.write(errorMessage + "\n")

def extractLinksFromSoup(soup):
	links = []
	try:
		for linkBlock in soup.find_all("a"):
			link = linkBlock["href"]
			if "search_id" in link and link.count("/") == 3:
				links.append(link)
	except:
	  	log("Scraper Error - " + currentUrl)
	finally:
		return links

def getHtml(searchQuery):
	global currentUrl
	html = ""
	try:
		params["q"] = quote(searchQuery)
		currentUrl = ENDPOINT + "?q=" + params["q"]
		response = requests.get(ENDPOINT, params=params, headers=headers)
		if response.status_code == 200:
			html = response.content.decode()
	except:
		log("HTTP Error - " + currentUrl)
	finally:
		return html

def getAppLinksFromPage(searchQuery):
	html = getHtml(searchQuery)
	soup = BeautifulSoup(html, "html.parser")
	return extractLinksFromSoup(soup)

def saveLinks(links):
	global linksTable
	savedLinks = []

	with open(OUTPUT_FILE, 'a') as outputFile:
		for link in links:
			link = link.split("?")[0]
			if link not in linksTable:
				outputFile.write(link + "\n")
				savedLinks.append(link)
				linksTable.add(link)
	return savedLinks

def throttle(index):
	if (index+1) % 500 == 0:
		sleep(60 * 5)
	elif (index+1) % 100 == 0:
		sleep(60)
	else:
		sleep(3)

def main():
	global searchTerms
	loadSearchTerms()
	buildLinksTable()

	lastSearchedIdx = getLastIndexProperty()
	searchTerms = searchTerms[lastSearchedIdx:]

	for index, term in enumerate(searchTerms):
		links = getAppLinksFromPage(term)
		linksSaved = saveLinks(links)
		print("[{}/{}] Scraped {} app links from {}".format(index + 1, len(searchTerms), len(linksSaved), currentUrl))

		lastSearchedIdx += 1
		setLastIndexProperty(lastSearchedIdx)
		throttle(index)

if __name__ == "__main__":
	main()