from shopify import ShopifyApp
from tinydb import TinyDB, Query
from time import sleep
import configparser
import argparse
import os

parser = argparse.ArgumentParser(description='Shopify app marketplace scraper')
parser.add_argument("-t", "--throttle", type=int, default=2, help="Throttle time (in seconds) bettween HTTP requests")
parser.add_argument("-v", "--verbose", default=False, action=argparse.BooleanOptionalAction, help="Verbose error output")
parser.add_argument("-tm", "--test-mode-on", default=False, action=argparse.BooleanOptionalAction, help="Only scrape maximum 2 pages per star review")
parser.add_argument("-or", "--omit-reviews", default=False, action=argparse.BooleanOptionalAction, help="Don't scrape app reviews")
parser.add_argument("-r", "--reset", default=False, action=argparse.BooleanOptionalAction, help="Reset scraper...delete log, config, and db files")
args = parser.parse_args()

OUTPUT_DIR = "output"
LOG_DIR = "log"
CONFIG_DIR = "config"

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)

APP_URLS_FILE = os.path.join(OUTPUT_DIR, "shopify_app_links.txt")
LOG_FILE = os.path.join(LOG_DIR, "shopify_app_scraper.log")
CONFIG_FILE = os.path.join(CONFIG_DIR, "shopify_app_scraper.ini")
DB_FILE = os.path.join(OUTPUT_DIR, "shopify_apps.json")
appUrls = []

config = configparser.ConfigParser()
db = TinyDB(DB_FILE)

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

def loadAppUrls():
	global appUrls
	with open(APP_URLS_FILE, 'r') as file:
		 appUrls = file.read().splitlines()

def log(appUrl, errors):
	with open(LOG_FILE, 'a') as logFile:
		logFile.write("Failed to scrape " + appUrl + "\n")
		for err in errors:
			logFile.write("\t" + err + "\n")

def throttle(index):
	if (index+1) % 500 == 0:
		sleep(args.throttle * 60 * 5)
	elif (index+1) % 100 == 0:
		sleep(args.throttle * 30)
	else:
		sleep(args.throttle)

def printReport(totalAppUrls, numberOfAppsWithErrors, numberOfTotalErrors):
	print("\n\n[+] Scraper Reports:")
	print("-------------------------------------")
	print("[+] {} apps scraped".format(totalAppUrls))
	if numberOfTotalErrors == 0:
		print("[+] 0 Errors")
	else:
		print("[-] {} apps with errors".format(numberOfAppsWithErrors))
		print("[-] {} total errors".format(numberOfTotalErrors))

	print("\n[+] Done!\n")

def reInitialize():
	if os.path.exists(LOG_FILE):
		os.remove(LOG_FILE)
		print("deleted " + LOG_FILE)
	if os.path.exists(CONFIG_FILE):
		os.remove(CONFIG_FILE)
		print("deleted " + CONFIG_FILE)
	if os.path.exists(DB_FILE):
		db.close()
		os.remove(DB_FILE)
		print("deleted " + DB_FILE)

def main():
	loadAppUrls()
	totalAppUrlCount = len(appUrls)
	lastSearchedIdx = getLastIndexProperty()
	remainingAppUrls = appUrls[lastSearchedIdx:]

	numberOfAppsWithErrors = 0
	numberOfTotalErrors = 0

	for index, appUrl in enumerate(remainingAppUrls):
		app = ShopifyApp(appUrl,
			throttle=args.throttle,
			verbose=args.verbose,
			testModeOn=args.test_mode_on,
			omitReviews=args.omit_reviews
		)
		db.insert(app.getData())
		print("[{}/{}] Scraped {}"
			.format(index + (totalAppUrlCount - len(remainingAppUrls)) + 1, totalAppUrlCount, appUrl))
		
		if len(app.errors) > 0:
			log(appUrl, app.errors)
			numberOfAppsWithErrors += 1
			numberOfTotalErrors += len(app.errors)

		lastSearchedIdx += 1
		setLastIndexProperty(lastSearchedIdx)
		throttle(index)

	initializePropertyFile()
	printReport(totalAppUrlCount, numberOfAppsWithErrors, numberOfTotalErrors)

if __name__ == "__main__":
	if args.reset:
		reInitialize()
	else:
		main()