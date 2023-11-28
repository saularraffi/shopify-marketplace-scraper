from bs4 import BeautifulSoup
from time import sleep
from sys import stdout
import requests
import json
import re

def printProgressBar(iteration, total, prefix='Progress:', suffix='Complete', decimals=1, length=50, fill='█', printEnd="\r"):
	"""
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	
	stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
	stdout.flush()
	sleep(0.1)

def flushProgressBar():
	print("\r" + " " * 100 + "\r", end='')
	stdout.flush()

def valueToInt(x):
	if type(x) == float or type(x) == int:
		return int(x)
	
	x = x.lower()

	if 'k' in x:
		if len(x) > 1:
			return int(float(x.replace('k', '')) * 1000)
		return 1000.0
	if 'm' in x:
		if len(x) > 1:
			return int(float(x.replace('m', '')) * 1000000)
		return 1000000.0
	return int(float(x))

class Options:
	def __init__(self, throttle, testModeOn, omitReviews, verbose):
		self.testModeOn = testModeOn
		self.throttleTime = throttle
		self.omitReviews = omitReviews
		self.verbose = verbose

class ShopifyApp:
	def __init__(self, url, throttle=3, testModeOn=False, omitReviews=False, verbose=False):
		self.options = Options(throttle, testModeOn, omitReviews, verbose)

		self.soup = None
		self.errors = []

		self.url = url
		self.title = ""
		self.imageUrl = ""
		self.rating = None
		self.reviewCount = None
		self.developerName = ""
		self.developerLink = ""
		self.dateLaunched = ""
		self.categories = []
		self.pricePlans = []
		self.reviews = {}
		self.numberOfReviewsScraped = 0

		self.scrape()

	def logError(self, message):
		self.errors.append(message)

	def scrape(self):
		self.fetchHtmlAndLoadSoup()
		
		if self.soup is None: return

		self.scrapeTitle()
		self.scrapeImgUrl()
		self.scrapeAppOverviewSection()
		self.scrapeAboutSection()
		self.scrapePricing()
		self.scrapeReviews()

	def getData(self):
		data = {
			'url': self.url,
			'title': self.title,
			'imageUrl': self.imageUrl,
			'rating': self.rating,
			'reviewCount': self.reviewCount,
			'developerName': self.developerName,
			'developerLink': self.developerLink,
			'dateLaunched': self.dateLaunched,
			'categories': self.categories,
			'pricePlans': self.pricePlans,
			'reviews': self.reviews
		}
		return data

	def getDataReadable(self):
		data = self.getData()
		data['reviews']['5-star']['content'] = "[...]"
		data['reviews']['4-star']['content'] = "[...]"
		data['reviews']['3-star']['content'] = "[...]"
		data['reviews']['2-star']['content'] = "[...]"
		data['reviews']['1-star']['content'] = "[...]"
		jsonStr = json.dumps(data, indent=4, ensure_ascii=False)
		return jsonStr

	def fetchHtmlAndLoadSoup(self):
		fetchError = False
		try:
			response = requests.get(self.url)
			if response.status_code == 200:
				html = response.content.decode()
				self.soup = BeautifulSoup(html, "html.parser")
			else:
				fetchError = True
		except Exception as e:
			if self.options.verbose: print("Failed to fetch HTML\n", e)
			fetchError = True
		finally:
			if fetchError:
				self.logError("Failed to fetch HTML")

	def scrapeTitle(self):
		try:
			self.title = self.soup.find("h1").text.strip()
		except Exception as e:
			errorMessage = "Failed to scrape title"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeImgUrl(self):
		try:
			self.imageUrl = self.soup.find("h1").parent.parent.parent.contents[1].find("div").find("img")['src']
		except Exception as e:
			errorMessage = "Failed to scrape image URL"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeRating(self, section):
		try:
			rating = section.find("span").text.split("(")[1].split(")")[0]
			self.rating = float(rating)
		except Exception as e:
			errorMessage = "Failed to scrape rating"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeReviewCount(self, section):
		try:
			reviewCountText = section.text.strip().replace(",", "")
			reviewCount = re.findall(r'[0-9]+', reviewCountText)[0]
			self.reviewCount = valueToInt(reviewCount)
		except Exception as e:
			errorMessage = "Failed to scrape review count"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeDeveloperName(self, section):
		try:
			self.developerName = section.find("a").text.strip()
		except Exception as e:
			errorMessage="Failed to scrape developer name"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeDeveloperLink(self, section):
		try:
			self.developerLink = "https://apps.shopify.com" + section.find("a", href=True)['href']
		except Exception as e:
			errorMessage = "Failed to scrape developer link"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeAppOverviewSection(self):
		try:
			appOverviewSection = self.soup.find("h1").parent.parent.parent.contents[3].contents[3]
			appOverviewSectionChildren = [i for i in appOverviewSection.contents if i != "\n"] 

			self.scrapeRating(appOverviewSectionChildren[0])
			self.scrapeReviewCount(appOverviewSectionChildren[1])
			self.scrapeDeveloperName(appOverviewSectionChildren[2])
			self.scrapeDeveloperLink(appOverviewSectionChildren[2])
		except Exception as e:
			errorMessage = "Failed to scrape app overview section"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeDateLaunched(self, section):
		try:
			self.dateLaunched = section.find_all("p")[1].text.strip()
		except Exception as e:
			errorMessage = "Failed to scrape date launched"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeCategories(self, section):
		try:
			categories = list(map(lambda link: link.text.strip(), section.find_all("a", href=True)))
			self.categories = categories
		except Exception as e:
			errorMessage = "Failed to scrape categories"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapeAboutSection(self):
		try:
			h2_tags = self.soup.find_all("h2")
			aboutSection = next(filter(lambda h2: h2.text.strip() == "About this app", h2_tags))
			aboutSections = aboutSection.parent.find("div")
			aboutSections = [i for i in aboutSections.contents if i != "\n"] 

			for section in aboutSections:
				sectionType = section.find("p").text.strip()

				match sectionType:
					case "Launched":
						self.scrapeDateLaunched(section)
					case "Categories":
						self.scrapeCategories(section)
		except Exception as e:
			errorMessage = "Failed to scrape about section"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def scrapePricing(self):
		try:
			priceOverview = self.soup.find("h1").parent.parent.parent.contents[3].find("div")
			isFree = "Price: Free" in str(priceOverview)

			if isFree:
				self.pricePlans = ["Free"]
			else:
				pricingPlanSection = self.soup.find(attrs={'id': 'adp-pricing'}).contents[3]
				pricingPlanChildren = [i for i in pricingPlanSection.contents[1].contents if i != "\n"]

				plans = []
				for planSection in pricingPlanChildren:
					plan = planSection.find("div", {"class": "app-details-pricing-plan-card"}).find("h3").text.strip()
					plans.append(plan)
				
				self.pricePlans = plans
		except Exception as e:
			errorMessage = "Failed to scrape pricing"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)

	def getReviewBlocks(self, reviewUrl):
		reviewBlocks = []
		for page in range(1,1000):
			url = "https://apps.shopify.com{}&page={}".format(reviewUrl, page)
			response = requests.get(url)
			html = response.content.decode()
			self.soup = BeautifulSoup(html, "html.parser")
			reviewTextBlocks = self.soup.find_all("p", {"class": "tw-break-words"})

			if (len(reviewTextBlocks) == 0): break

			lastBlock = None
			for idx, reviewTextBlock in enumerate(reviewTextBlocks):
				reviewBlock = reviewTextBlock.parent.parent.parent
				if reviewBlock != lastBlock:
					reviewBlocks.append(reviewBlock)
					lastBlock = reviewBlock

					self.numberOfReviewsScraped += 1
					printProgressBar(
						self.numberOfReviewsScraped,
						self.reviewCount,
						prefix="{}/{} reviews".format(self.numberOfReviewsScraped, self.reviewCount)
					)

			if (self.options.testModeOn and page > 2): break

			sleep(self.options.throttleTime)

		return reviewBlocks

	def getReviewContent(self, reviewUrl):
		reviewBlocks = self.getReviewBlocks(reviewUrl)

		reviews = []
		for reviewBlock in reviewBlocks:
			reviewTextParent = reviewBlock.find("p", {"class": "tw-break-words"}).parent
			paragraphBlocks = reviewTextParent.find_all("p")
			
			paragraphs = []
			for block in paragraphBlocks:
				paragraphs.append(block.text.strip() + "\n")

			reviews.append("".join(paragraphs))
		
		return reviews

	def scrapeReviews(self):
		if self.options.omitReviews: return

		try:
			appReviewMetricsSection = self.soup.find("div", {"class": "app-reviews-metrics"})
			ratingBlocks = appReviewMetricsSection.find_all("li")

			reviewData = {}
			for index, ratingBlock in enumerate(ratingBlocks):
				ratingBlockChildren = [i for i in ratingBlock.contents if i != "\n"]
				reviewCount = valueToInt(ratingBlockChildren[-1].find("span").text.strip())
				linkBlock = ratingBlockChildren[-1].find("a", href=True)

				key = "{}-star".format(5 - index)
				reviewData[key] = {}
				reviewData[key]['count'] = reviewCount
				reviewData[key]['content'] = self.getReviewContent(linkBlock['href']) if linkBlock is not None else []

			self.reviews = reviewData
			flushProgressBar()
		except Exception as e:
			errorMessage = "Failed to scrape reviews"
			if self.options.verbose: print(errorMessage, "\n", e)
			self.logError(errorMessage)