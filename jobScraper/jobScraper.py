from selenium import webdriver #Webdriver de Selenium qui permet de contrôler un navigateur
from selenium.webdriver.common.by import By #Permet d'accéder aux différents élements de la page web
#from selenium.webdriver.remote.webelement
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager #Assure la gestion du webdriver de Chrome

from datetime import datetime, timedelta
import math
import time
import requests

import warnings
warnings.filterwarnings("ignore")
import os
import json
from definitions import ROOT_DIR, COUNTRY_CODES_MAP, JOB_SEARCH_LOCATIONS, CONTRACT_TYPES_BY_COUNTRY_CODE
import re

from routers.models.job import Job
from routers.models.job import JobUpdate
from urllib.parse import quote_plus as urlEncode

from playwright.sync_api import sync_playwright
from fake_useragent import UserAgent
import random

import logging as log
log.basicConfig(filename=os.path.join(ROOT_DIR,"logs","scraper.log"), encoding='utf-8', filemode='w', format='%(asctime)s-%(levelname)s:%(message)s', level=log.DEBUG)

# Optional: Use your own proxy
PROXY = None  # e.g., "http://username:password@proxyhost:port"

class JobScraper:
    def __init__(self) -> None:
        self.debug = False
        self.dalJob = self.DataAccessLayer(resourceName="job")#, apiUrl="http://192.168.1.100:8000")
        self.today = datetime.now()
        self.targetDay = self.today
        self.year = str(self.targetDay.year)
        self.month = str(self.targetDay.month)
        self.day = "0" + str(self.targetDay.day) if len(str(self.targetDay.day)) < 2 else str(self.targetDay.day) #on ajoute 0 devant le jour s'il est compris entre 1 et 9
        
        # self.chromeDriverPath = "/snap/bin/chromium.chromedriver"#"/snap/chromium/2873/usr/lib/chromium-browser/chromedriver"
        # self.chromeOptions = webdriver.ChromeOptions()
        # self.chromeOptions.add_argument('--headless')
        # self.chromeOptions.add_argument('--no-sandbox')
        # self.chromeOptions.add_argument('--disable-dev-shm-usage')
        # self.chromeOptions.add_argument('--window-size=1920,1080')
        # #self.chromeOptions.add_argument('--ignore-certificate-errors')
        # #self.chromeOptions.add_argument('--allow-running-insecure-content')
        # user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        # self.chromeOptions.add_argument(f'user-agent={user_agent}')

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.commonViewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1280, "height": 800},
            {"width": 1536, "height": 864},
            {"width": 1600, "height": 900},
            {"width": 1280, "height": 720},
        ]

        # self.currentCountryCode = None #Code du pays actuel, par défaut France
        self.countryCode = ""
        self.localeByCountry = {
            "US": "en-US",
            "GB": "en-GB",
            "CA": "en-CA",
            "AU": "en-AU",
            "IE": "en-IE",
            "NZ": "en-NZ",
            "IN": "en-IN",

            "FR": "fr-FR",
            "BE": "fr-BE",
            "CH": "fr-CH",

            "DE": "de-DE",
            "AT": "de-AT",
            "CH_DE": "de-CH",  # German-speaking part of Switzerland

            "IT": "it-IT",
            "ES": "es-ES",
            "MX": "es-MX",
            "AR": "es-AR",
            "CL": "es-CL",
            "CO": "es-CO",
            "PE": "es-PE",

            "PT": "pt-PT",
            "BR": "pt-BR",

            "NL": "nl-NL",
            "BE_NL": "nl-BE",  # Dutch-speaking part of Belgium

            "PL": "pl-PL",
            "CZ": "cs-CZ",
            "SK": "sk-SK",
            "HU": "hu-HU",

            "RU": "ru-RU",
            "UA": "uk-UA",

            "JP": "ja-JP",
            "KR": "ko-KR",
            "CN": "zh-CN",
            "TW": "zh-TW",
            "HK": "zh-HK",

            "TR": "tr-TR",
            "IL": "he-IL",
            "SA": "ar-SA",
            "IR": "fa-IR",

            "SE": "sv-SE",
            "NO": "nb-NO",
            "DK": "da-DK",
            "FI": "fi-FI",

            "RO": "ro-RO",
            "BG": "bg-BG",
            "GR": "el-GR",
            "TH": "th-TH",
            "VN": "vi-VN",

            "ID": "id-ID",
            "MY": "ms-MY",

            "ZA": "en-ZA",
            "NG": "en-NG",
            "EG": "ar-EG",

            "HK_EN": "en-HK",
            "SG": "en-SG",
        }

        self.userAgentNominalFetchedPages = 100 #Nombre nominal de pages à scrapper avant de changer d'user agent
        self.userAgentMaxFetchedPages = 0 #Nombre de pages à scrapper avant de changer d'user agent
        self.userAgentFetchedPages = 0 #Nombre de pages scrappées avec l'user agent actuel
        
        self.sessionDirPath = ""
        self.sessionPlatformFilesPath = ""
        self.fsTimestamp = ""
        self.dbTimestamp = ""
        
        self.antibotFlagPauseSeconds = 5 #2.5


        # user_agent = self.get_random_user_agent()
        self.setSearchContractTypes(
            fullTime=True,
            temporary=True,
            partTime=False,
            internship=False,
            apprenticeship=True,
            freelance=True
        )
    
    def get_random_user_agent():
        ua = UserAgent()
        return ua.random

    def start(self, countryCode: str):
        browser_args = []
        if PROXY:
            browser_args.append(f'--proxy-server={PROXY}')

        user_agent = self.get_random_user_agent()
        self.userAgentFetchedPages = 0
        multiplier = random.randrange(0,100) / 100
        multiplier = 1 if multiplier >= 0.5 else -1
        self.userAgentMaxFetchedPages = self.userAgentNominalFetchedPages + multiplier * random.randint(0, math.ceil(self.userAgentNominalFetchedPages * 0.3)) #On ajoute ou retranche un nombre aléatoire de pages à scrapper entre 0 et 30% du nombre nominal de pages
        log.debug(f"ScraperLog - New user agent max fetched pages: {self.userAgentMaxFetchedPages}")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, args=browser_args)

        viewport = random.choice(self.commonViewports)
        locale = self.localeByCountry.get(countryCode, "en-US")
        self.context = self.browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale=locale,
        )
        self.page = self.context.new_page()

    def stop(self):
        log.debug("ScraperLog - Stopping Playwright browser context")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.browser = self.playwright = self.context = self.page = None

    def visit_page(self, url):
        if self.page is None:
            log.debug("ScraperLog - Starting Playwright browser context")
            self.start(countryCode=self.countryCode)
        
        if self.userAgentFetchedPages >= self.userAgentMaxFetchedPages:
            log.debug(f"ScraperLog - User agent fetched pages limit reached: {self.userAgentFetchedPages} >= {self.userAgentMaxFetchedPages}")
            self.stop() # Close the browser context and stop Playwright
            return self.visit_page(url) # Restart the process with a new user agent

        log.debug(f"ScraperLog - Fetching page content from url: {url}")
        self.page.goto(url) # self.page.goto(url, timeout=60000)
        # Optional: wait for page to render fully
        self.page.wait_for_load_state('networkidle')
        self.currentUrl = self.page.url
        log.debug(f"Final resolved URL: {self.currentUrl}")
        self.userAgentFetchedPages += 1
        log.debug(f"ScraperLog - User agent fetched pages: {self.userAgentFetchedPages} / {self.userAgentMaxFetchedPages}")

    def sleep(self, seconds):
        time.sleep(seconds)

    def random_sleep(self, min_seconds=4, max_seconds=12, deepSleep=True):
        random_seconds = random.uniform(min_seconds, max_seconds)
        log.debug(f"ScraperLog - Sleeping for {random_seconds:.2f} seconds")
        time.sleep(random_seconds)
        if deepSleep:
            random_seconds = random.uniform(min_seconds, max_seconds)
            log.debug(f"ScraperLog - Deep Sleeping (2nd sleep) for {random_seconds:.2f} seconds")
            time.sleep(random_seconds)

    def search(self, query):
        self.page.fill("input[name='q']", query)
        self.page.press("input[name='q']", "Enter")

    def get_title(self):
        return self.page.title()

    def getPageContent(self):
        """
        Returns the HTML content of the current page.
        """
        return self.page.content()

    class DataAccessLayer:
        def __init__(self, resourceName:str, apiUrl: str = "http://127.0.0.1:8000") -> None:
            self.apiUrl = f"{apiUrl}/{resourceName}s"
            self.resourceName = resourceName
            self.scrapedUrlsInDb = self.getScrapedUrlsInDb()
        
        def getScrapedUrlsInDb(self) -> dict:
             log.info(f"{self.resourceName}Dal--getScrapedUrlsInDb-Start")
             res = requests.get(url=f"{self.apiUrl}/scraped-urls")
             log.info(f"{self.resourceName}Dal--getScrapedUrlsInDb-End")
             return json.loads(res.text)
        
        def getAll(self):
            log.info(f"{self.resourceName}Dal--getAll-Start")
            res = requests.get(f"{self.apiUrl}/")
            log.info(f"{self.resourceName}Dal--getAll-End")
            return res
        
        def getAllSumList(self) -> list[dict]:
            log.info(f"{self.resourceName}Dal--getAllSumList-Start")
            res =  requests.get(
                url=f"{self.apiUrl}/list"
                ).json()
            log.debug(f"Json converted list :\n{res}")
            log.info(f"{self.resourceName}Dal--getAllSumList-End")
            return res
        
        def postOne(self, obj: dict) -> dict | None:
            log.info(f"{self.resourceName}Dal--postOne-Start")
            try:
                res = requests.post(url=f"{self.apiUrl}/",
                                    json=obj
                                    )
                if res.status_code == 201:
                    log.debug(f"Object created in database:\n{res.json}")
                    return json.loads(res.text)
                else:
                    log.debug(f"Error while creating the object in database:\nStatus code:{res.status_code}\nmessage:{res.content}")
            except Exception as e:
                log.debug(f"Error: {e}")
            log.info(f"{self.resourceName}Dal--postOne-End")

        def postMany(self, objList: list[dict]) -> list[dict] | None:
            log.info(f"{self.resourceName}Dal--postMany-Start")
            res = [ ]
            for obj in objList:
                response = self.postOne(obj)
                if response is not None: res.append(response)
            log.info(f"{self.resourceName}Dal--postMany-End")
            if len(res)>0: return res

        def deleteOne(self, objId: str):
            log.info(f"{self.resourceName}Dal--deleteOne-Start")
            res = requests.delete(
                url=f"{self.apiUrl}/{objId}"
                )
            if res.status_code == 204:
                log.debug(f"Successfully deleted {self.resourceName} with id: {objId}")
            else:
                log.debug(f"Failed to delete {self.resourceName} with id: {objId}")
            log.info(f"{self.resourceName}Dal--deleteOne-End")

        def deleteMany(self, objIds: list[str]):
            log.info(f"{self.resourceName}Dal--deleteMany-Start")
            for objId in objIds:
                self.deleteOne(objId)
            log.info(f"{self.resourceName}Dal--deleteMany-End")

        def deleteAll(self):
            log.info(f"{self.resourceName}Dal--deleteAll-Start")
            itemIds = [item["_id"] for item in self.getAllSumList()]
            log.debug(f"List of received item ids:\n{itemIds}")
            self.deleteMany(itemIds)
            log.info(f"{self.resourceName}Dal--deleteAll-End")
    
    def getSearchQueries(self, countryCode: str = "FR") -> list[str]:
        #return ["kotlin"]
        commonList = [
            "kotlin",
            "python",
            "javascript",
            "c#"
            ]
        countryList = {
            # "FR": ["développeur mobile"],
            "CA": ["mobile developer"],
            "CA-QC": ["développeur mobile"],
        }
        cList: list = countryList[countryCode]
        searchQueries = commonList #[*commonList,*cList]

        return searchQueries
    
    def setSearchContractTypes(self, fullTime: bool, temporary: bool, partTime: bool, internship: bool, apprenticeship: bool, freelance: bool):
        contractTypes = []
        if fullTime: contractTypes.append("fullTime")
        if temporary: contractTypes.append("temporary")
        if partTime: contractTypes.append("partTime")
        if internship: contractTypes.append("internship")
        if apprenticeship: contractTypes.append("apprenticeship")
        if freelance: contractTypes.append("freelance")

        self.searchedGenericContractTypes = contractTypes

    def setCountrySearchedContractTypes(self):
        countryCode = self.countryCode
        countryContractTypes = \
            CONTRACT_TYPES_BY_COUNTRY_CODE[countryCode] \
            if countryCode in CONTRACT_TYPES_BY_COUNTRY_CODE \
            else CONTRACT_TYPES_BY_COUNTRY_CODE["else"]
        
        """
        countrySearchedContractTypes = [ ] 
        for searchedContractType in self.searchedGenericContractTypes:
            countrySearchedContractTypes.append(countryContractTypes[searchedContractType])
        
        self.searchedContractTypes = countrySearchedContractTypes
        v1^
        """
        countrySearchedContractTypes = {contractType: genericContractType for genericContractType, matchingCountryContractTypes in countryContractTypes.items() for contractType in matchingCountryContractTypes}

        self.searchedContractTypes = countrySearchedContractTypes
    
    def isSearchedTypeOfContract(self, jobContractType: str) -> tuple[bool,str|None]:
        jobContractType = jobContractType.lower()
        if jobContractType in self.searchedContractTypes:
            genericContractType = self.searchedContractTypes[jobContractType]
            if self.countryCode == "FR" and genericContractType in ["internship", "apprenticeship"]:
                log.info("ScraperLog - Job SKIPPED - Job is an internship or an apprenticeship in France")
                return (False, None)
            log.debug(f"ScraperLog - Job ({genericContractType}) is in searched list")
            return (True, genericContractType)
        else:
            log.debug(f"ScraperLog - Job SKIPPED - Job ({jobContractType}) is NOT in searched list")
            return (False, None)
        for contractType in self.searchedContractTypes:
            if contractType == jobContractType:
                return (True, contractType)
            
        return (False, None)



    def getJobs(self):
        year = self.year
        month = self.month
        day = self.day

        sessionTimestamp = datetime.now()
        self.fsTimestamp = sessionTimestamp.strftime("%Y-%m-%d_%H-%M-%S")
        self.dbTimestamp = sessionTimestamp.strftime("%Y-%m-%dT%H:%M:%S")
        sessionFilesPath = os.path.join(ROOT_DIR,"logs","sessionFiles",self.fsTimestamp)
        os.makedirs(sessionFilesPath)

        self.sessionDirPath = os.path.join(ROOT_DIR,sessionFilesPath,"jobs")
        os.makedirs(self.sessionDirPath)

        platforms = {
            # "FR_indeed": self.getJobsIndeedFR,
            "CA_indeed": self.getJobsIndeedCAN,
            #"CAN_linkedIn": self.getJobsLinkedin,
            #"FR_linkedIn": self.getJobsLinkedin,
            #"FR_apec": self.getJobsApec,
            #"FR_cadremploi": self.getJobsCadremploi,
            #"FR_hellowork": self.getJobsHellowork,
            #"FR_welcome2jungle": self.getJobsWelcomeJungle,
            #"FR_poleEmploi": self.getJobsPoleEmploi,
            #"FR_weLoveDevs" : self.getJobsWeLoveDevs,
            #"FR_chooseYourBoss": self.getJobsChooseYourBoss,
            #"CAN_Monster": self.getJobsMonsterCAN
        }

        print(f"JobScraper - Started scraping job for:\n{platforms}")
        result = [ ]
        for idx_ptf, platform in enumerate(platforms.keys()):
            self.countryRegionCode = platform.split("_")[0]
            self.countryCode = self.countryRegionCode.split("-")[0]
            self.sessionPlatformFilesPath = os.path.join(self.sessionDirPath,f"{idx_ptf}.{platform}")
            os.makedirs(self.sessionPlatformFilesPath)
            sessionFailuresPath = os.path.join(self.sessionPlatformFilesPath,"failures")
            os.makedirs(sessionFailuresPath)

            self.setCountrySearchedContractTypes()
            
            print(f"Starting to scrap jobs on: {platform}")
            platformJobs = platforms[platform]()
            print(f"Finished scraping jobs on: {platform}")

            if len(platformJobs) >0: 
                print(f"{len(platformJobs)} have been scraped, they are now being added in database")
                res = self.dalJob.postMany(objList=platformJobs)
                if res: result.append(res)

        if len(result)>0:
            print(result)
            print(f"JobScraper - Finished scraping jobs for:\n{platforms}")
            print(f"{len(result)} jobs were successfully added in database (see above)")
        else:
            print(f"JobScraper - Finished scraping jobs for:\n{platforms}")
            print("No jobs were added in database, maybe the jobs were already there? Check log files for more details.")

    


    def getJobsIndeed(self, platform:str) -> list[dict]:
        # Testé pour des recherches d'emploi en France et en Francais
        def cleanPostDescription(html:str | None) -> str:
            if not html: return ""
            
            boldTagPattern = "(<b>).+?(</b>)"
            listItemTagPattern = "(<li>).+?(</li>)"
            lineBreakPattern = "<br>"
            removeRemainingHTMLTagsPattern = "</*.+?>"
            removeHTMLTags = lambda inStr : re.sub(removeRemainingHTMLTagsPattern,"",inStr)

            wkStr = html
            matches = []
            regexFinder = re.compile(boldTagPattern)
            for m in regexFinder.finditer(wkStr):
                matches.append(m)
            matches.reverse()
            for m in matches:
                replacement = "\n# " + removeHTMLTags(wkStr[m.start():m.end()]) + "\n"
                wkStr = wkStr[:m.start()] + replacement + wkStr[m.end():]

            matches = []
            regexFinder = re.compile(listItemTagPattern)
            for m in regexFinder.finditer(wkStr):
                matches.append(m)
            matches.reverse()
            for i,m in enumerate(matches):
                replacement = "- " + removeHTMLTags(wkStr[m.start():m.end()])
                wkStr = wkStr[:m.start()] + replacement + wkStr[m.end():]

            wkStr.replace(lineBreakPattern,"\n")
            wkStr = removeHTMLTags(wkStr)


            wkStr = wkStr.split("\n")
            out = []
            for idx_line, lineEnum in enumerate(wkStr):
                line = lineEnum.strip()
                if line:
                        out.append("\n" + line if (line[0] == "#") else line)
            out = "\n".join(out)
            #print(wkStr)

            return out

        def extractLocationInformations(inStr: str | None) -> tuple[str|None,str,str|None]:
            if inStr is None: return (None,"", None)

            match self.countryCode:
                case "FR":
                    zip = inStr.split(" ")[-1].replace("(","").replace(")","")
                    wkStr = inStr.split(" ")
                    wkStr.pop(-1)
                    city = " ".join(wkStr)
                    district = None
                case "CA":
                    district = inStr.split(", ")[-1]
                    wkStr = inStr.split(", ")
                    wkStr.pop(-1)
                    city = " ".join(wkStr)
                    match city.lower():
                        case "montreal":
                            district = "Quebec"
                        case "toronto":
                            district = "Ontario"
                        case "ottawa":
                            district = "Ontario"
                        case "vancouver":
                            district = "British Columbia"
                        case _:
                            district = district
                    
                    zip = None
                case _:
                    raise Exception("getJobsIndeed implemented only for FR and CAN country codes for now")
                    district = None
                    city = ""
                    zip = None

            return (district, city, zip)

        def urlEncodeQuery(string) -> str:
            substitutions = [
            (',', '%2C'),
            (' ', '+'),
            ]

            for search, replacement in substitutions:
                string = string.replace(search, replacement)
            
            return string

        if platform not in ["fr.indeed.com","ca.indeed.com"]:
            raise Exception("getJobsIndeed implemented only for FR and CAN country codes for now")

        createdAt = self.dbTimestamp
        createdOn = self.dbTimestamp.split("T")[0]
        country = COUNTRY_CODES_MAP[self.countryCode]
        sourceType = "jobBoard"
        

        sessionFilesDir = self.sessionPlatformFilesPath
        self.start(countryCode=self.countryCode)
        self.random_sleep()

        #Start Scraping Logic
        jobSearchLocations = JOB_SEARCH_LOCATIONS[self.countryCode]
        locations = [ ]
        for location in jobSearchLocations:
            if location["query"]:
                if platform in location["query"]:
                    loc = location["query"][platform]
                else:
                    loc = location["query"]["else"]
            else:
                loc = location["city"]
            locations.append({
                "location": loc,
                "queryParam": urlEncodeQuery(loc)
            })

        queries = self.getSearchQueries(self.countryCode)

        # Retrieve all job searches posts urls
        searchRadius = 25 # search radius of x km outside of the given location; available values : 0, 10, 25, 35, 
        fromAge = 1 # jobs from the last x days; available values 1, 3,7,14
        postUrlsDict = {}
        errors=[]
        for idx_loc, locationDict in enumerate(locations):
            #print(f"locationDict: {locationDict}")
            locationQueryParam = locationDict["queryParam"]
            locationName = locationDict["location"]
            print(f"locationName: {locationName}")
            postUrlsDict[locationName] = {} #postUrlsDict[locationName] = {query: {"posts":[],"skipped":[]} for query in queries}
            for idx_q, query in enumerate(queries):
                if query not in postUrlsDict[locationName]:
                    postUrlsDict[locationName][query] = {"posts":[],"skipped":[]}
                queryString = "+".join(query.split(" "))
                url = f"https://{platform}/jobs?q={queryString}&l={locationQueryParam}&sort=date&fromage={fromAge}&radius={searchRadius}"
                page = 1
                log.info(f"ScraperLog - New job search>query:'{query}', location:'{locationName}'\n{url}")
                totalJobsCount = 0
                self.visit_page(url) #Accès aux annonces du jour
                if True:
                    newScreenshotPath = os.path.join(self.sessionPlatformFilesPath,"failures",f"test_{locationName}_{query}_TestScreenshot.png")
                    self.page.screenshot(path=newScreenshotPath, full_page=True)
                #btnDateFilter = self.driver.find_element(By.ID, "filter-dateposted") #On identifie le bouton 
                #self.driver.execute_script("arguments[0].click();", btnDateFilter); # On clique dessus
                jobsFound = True
                lastPage = False
                
                while not lastPage and jobsFound:
                    log.info(f"ScraperLog - Getting job urls on page {page}...")
                    
                    # jobCardsContainer = self.driver.find_elements(By.ID,"mosaic-provider-jobcards")
                    jobCardsContainer = self.page.locator("#mosaic-provider-jobcards")
                    jobCardsContainer = jobCardsContainer[0] if len(jobCardsContainer) >0 else None
                    if jobCardsContainer: 
                        log.debug(f"ScraperLog - Page {page}: Found jobCardsContainer")
                    else:
                        #jobCardsContainer is None 
                        errorMessage = ""
                        # noResultMessageContainer = self.driver.find_elements(By.XPATH,"//div[starts-with(@class,'jobsearch-NoResult-messageContainer')]")
                        noResultMessageContainer = self.page.locator("//div[starts-with(@class,'jobsearch-NoResult-messageContainer')]")
                        if len(noResultMessageContainer) >0:
                            errorMessage = f"No jobs have been found for the current query: {{query:'{query}', location:'{locationName}'}}"
                            print(errorMessage)
                            log.debug(f"ScraperLog - {errorMessage}")
                        else:
                            errorMessage = f"""ScraperLog - Error:\n{json.dumps(obj={
                                "message": f"Error while scraping the main page: 'mosaic-provider-jobcards' not found",
                                " location" : locationName,
                                "query": query,
                                " url": url
                                }, indent=4)}""" #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                            errors.append(errorMessage)
                            newScreenshotPath = os.path.join(self.sessionPlatformFilesPath,"failures",f"error_{len(errors)}_screenshot.png")
                            self.page.screenshot(path=newScreenshotPath, full_page=True)
                        
                        log.debug(f"ScraperLog - Error: {errorMessage}")
                        self.random_sleep()
                        #choice = input("Error while scraping the main page: 'mosaic-provider-jobcards' not found\nDo you want to continue [Y/n]?: ")
                        #if choice == 'n': exit()
                        jobsFound = False
                        continue

                    jobCards = jobCardsContainer.find_elements(By.XPATH,".//div[starts-with(@class,'job_seen_beacon')]")# jobCardsContainer.find_elements(By.XPATH,".//*[@dir]")
                    pageJobsCount = len(jobCards)
                    if pageJobsCount == 0:
                        log.debug(f"ScraperLog - Error: no job card has been found in card holder (no @dir element found in card holder)")
                    totalJobsCount += pageJobsCount
                    log.debug(f"ScraperLog - {pageJobsCount} cards/jobs found on page {page}")
                    for idx_jobCard, jobCard in enumerate(jobCards):
                        log.debug(f"ScraperLog - jobCard #{idx_jobCard}:\n>>>\n{jobCard.get_attribute('innerHTML')}\n<<<\n")
                        aTagId = jobCard.find_elements(By.XPATH,".//h2[starts-with(@class,'jobTitle')]//a")
                        aTagId = aTagId[-1] if len(aTagId) >0 else None
                        if aTagId is None: 
                            errorMessage = f"""ScraperLog - Error:\n{json.dumps(obj={
                            "message": f"Error while scraping the main page: job card hyperlink (a tag) not found",
                            " location" : locationName,
                            "query": query,
                            " url": url
                            }, indent=4)}"""
                            log.debug(f"ScraperLog - Error: {errorMessage}") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                            errors.append(errorMessage)
                            newScreenshotPath = os.path.join(self.sessionPlatformFilesPath,"failures",f"error_{len(errors)}_screenshot.png")
                            self.page.screenshot(path=newScreenshotPath, full_page=True)
                            self.random_sleep()
                            continue
                        else:
                            log.debug(f"ScraperLog - jobCard #{idx_jobCard}:Found a job title: retrieving job ID...")
                            log.debug(f"ScraperLog - Title:\noOoOoOoOoOo\n{aTagId.get_attribute('innerHTML')}\noOoOoOoOoOo\n")
                        
                        # Looking for the direct HTML element holding the job ID
                        aTagId = aTagId.find_elements(By.XPATH,".//*[starts-with(@id,'jobTitle')]")
                        aTagId = aTagId[0] if len(aTagId) >0 else None
                        if aTagId is None: 
                            log.debug(f"""ScraperLog - Error:\n{json.dumps(obj={
                            "message": f"Error while scraping the main page: job card hyperlink (a tag) HTML id holder not found",
                            " location" : locationName,
                            "query": query,
                            " url": url
                            }, indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                            self.random_sleep()
                            continue
                        else:
                            log.debug(f"ScraperLog - jobCard #{idx_jobCard}:Found an ID holder: retrieving job ID...")
                            #log.debug(f"Title:\noOoOoOoOoOo\n{aTagId.get_attribute('innerHTML')}\noOoOoOoOoOo\n")
                        """
                        ^v1
                        -> abandoned by XPath here because it seems WebDriver isnt looking for h2 in every loop subHTML element but rather in the whole document, making `aTagId = aTagId[0] if len(aTagId) >0 else None` always select the first jobCard title a link while the current loop HTML is another card.
                        -> Finally good because we had to add `.` in front of the xpath so that the WebDriver would take over from current position.
                        """

                        """
                        aTagId = jobCard.find_elements(By.TAG_NAME,"h2")[0].find_elements(By.TAG_NAME,"a")[0]
                        ^v2
                        """

                        aTagId = aTagId.get_attribute("id")
                        if aTagId is None:
                            log.debug(f"""ScraperLog - Error:\n{json.dumps(obj={
                            "message": f"Error while scraping the main page: job card hyperlink (a tag) HTML id holder -> ID found Null",
                            " location" : locationName,
                            "query": query,
                            " url": url
                            },indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                            self.random_sleep()
                            continue
                        jobId = re.split("-|_", aTagId)[1] #aTagId.split("_")[1] if aTagId else None
                        log.debug(f"ScraperLog - jobId: {jobId}")
                        if jobId: 
                            jobPostUrl = f"https://{platform}/viewjob?jk={jobId}"
                            if jobPostUrl in self.dalJob.scrapedUrlsInDb:
                                #log.info(f"Post {idx_post} - SKIPPED - Post already scraped: Post Url already in database\nurl: {postUrl}")
                                #print(f"Post {idx_post} - SKIPPED - Post already scraped: Post Url already in database\nurl: {postUrl}")
                                #continue
                                postUrlsDict[locationName][query]["skipped"].append(jobPostUrl)
                            else:
                                postUrlsDict[locationName][query]["posts"].append(jobPostUrl)

                    """
                    ^v2
                    """

                    # btnNext = self.driver.find_elements(By.XPATH, "//a[@data-testid='pagination-page-next']") #On identifie le bouton 
                    btnNext = self.page.locator("//a[@data-testid='pagination-page-next']") #On identifie le bouton 
                    """
                    ^v2
                    """
                    # Check if the element exists and is visible
                    if btnNext.count() > 0:
                        btnNext.first.click()
                        page += 1
                        self.random_sleep()
                    else:
                        lastPage = True
                        log.debug(f"ScraperLog - {totalJobsCount} jobs in total found for the following job search> query:'{query}', location:'{locationName}'")
                        print(f"{totalJobsCount} jobs in total found for the following job search> query:'{query}', location:'{locationName}'")
                        self.random_sleep()
                        
        log.debug(f"ScraperLog - Posts url gathering finished. Here's the list of posts to scrap: {postUrlsDict}")
        if len(errors) != 0:
            with open(os.path.join(sessionFilesDir,f"errors_main_page.json"), "w", encoding='utf-8') as f:
                        f.write(json.dumps(obj=errors, indent=4))

        # Scrap all posts
        posts = {location: {query: [] for query in locationDict.keys()} for location, locationDict in postUrlsDict.items()}
        log.debug(f"ScraperLog - Posts initial / empty dictionnary: {posts}")
        #posts = []
        errors = []
        for location in postUrlsDict.keys():
            for query  in postUrlsDict[location].keys():
                postUrls = postUrlsDict[location][query]["posts"]
                skippedUrls = postUrlsDict[location][query]["skipped"]
                #print(postUrls)# if self.debug else {}
                log.info(f"ScraperLog - Now scraping posts for ({location},{query}). {len(postUrls)} posts found: {postUrls}")
                print(f"Now scraping posts for ({location},{query}). {len(postUrls)} posts found: {postUrls}")
                if len(skippedUrls) >0:
                    log.debug(f"ScraperLog - {len(skippedUrls)} posts have been SKIPPED for ({location},{query}) for being already in the database: {skippedUrls}")
                    print(f"{len(skippedUrls)} posts have been SKIPPED for ({location},{query}) for being already in the database: {skippedUrls}")
                
                for idx_post, postUrlVal in enumerate(postUrls):
                    postUrl = str(postUrlVal)
                    applyUrl = None
                    if self.debug:
                        if idx_post > 2:
                            message = "Debug mode enabled - Scraping interrupted after the third post of each query-location"
                            print(message)
                            log.info(message)
                            break
                    self.visit_page(postUrl) #Accès à la page de l'annonce
                    self.random_sleep()
                    log.info(f"ScraperLog - Scraping Post #{idx_post}: {postUrl}")

                    slug = postUrl.split("/")[-1]

                    try:
                        # Récupération du body de la page:
                        body = self.page.locator("/html/body")

                        """
                        Sauvegarde des sources de la page scrappée sur le disque
                        """
                        if self.debug and False:
                            with open(os.path.join(sessionFilesDir,f"{idx_post}_source.html"), "w", encoding='utf-8') as f:
                                    f.write(self.driver.page_source)

                            with open(os.path.join(sessionFilesDir,f"{idx_post}_source_body.html"), "w", encoding='utf-8') as f:
                                    f.write(str(body.get_attribute("innerHTML")).strip())

                        titleElement = body.find_element(By.XPATH,"//h1[starts-with(@class,'jobsearch-JobInfoHeader-title')]//span")
                        title = titleElement.get_attribute("innerText")

                        companyInfoElement = body.find_element(By.XPATH,"//div[@data-testid='jobsearch-CompanyInfoContainer']")
                        companyNameElement = companyInfoElement.find_element(By.XPATH, "//div[@data-testid='inlineHeader-companyName']//a")
                        companyLocationElement = companyInfoElement.find_element(By.XPATH, "//div[@data-testid='inlineHeader-companyLocation']//div")

                        companyName = companyNameElement.get_attribute("innerText")
                        companyLocation = companyLocationElement.get_attribute("innerText")

                        jobLocationElement = body.find_element(By.XPATH, "//div[@id='jobLocationText']//span")
                        jobLocation = jobLocationElement.get_attribute("innerText")
                        district, city, zipCode = extractLocationInformations(jobLocation)

                        jobDescriptionElement = body.find_element(By.ID, "jobDescriptionText")
                        jobDescriptionHTML = jobDescriptionElement.get_attribute("innerHTML")
                        jobDescription = cleanPostDescription(html=jobDescriptionHTML)

                        salaryInfoAndJobTypeElement = body.find_element(By.ID, "salaryInfoAndJobType")
                        salaryInfoAndJobTypeSubElements = salaryInfoAndJobTypeElement.find_elements(By.TAG_NAME,"span")
                
                        if len(salaryInfoAndJobTypeSubElements) == 1:
                            jobType = "fulltime"
                        else:
                            jobTypeElement = salaryInfoAndJobTypeSubElements[-1]

                            jobType = str(jobTypeElement.get_attribute("innerText")).strip()
                            if jobType:
                                if jobType[0] == "-": jobType = jobType[1:].strip()
                        
                        
                        isSearchedJobType, genericJobType = self.isSearchedTypeOfContract(jobContractType=jobType)
                        if not isSearchedJobType: 
                            log.debug(f"ScraperLog - Post #{idx_post} is not is searchedContractTypes - SKIPPED\nPost url:{postUrl}")
                            continue
                        
                        
                        viewJobButtonContainerElement = body.find_elements(By.XPATH,".//div[@id='jobsearch-ViewJobButtons-container']")[0]
                        indeedApplyButtonElement = viewJobButtonContainerElement.find_elements(By.XPATH, ".//div[starts-with(@class,'jobsearch-IndeedApplyButton')]")
                        extSiteApplyButtonElement = viewJobButtonContainerElement.find_elements(By.XPATH, ".//div[starts-with(@id,'applyButtonLinkContainer')]")
                        applyButtonElement = viewJobButtonContainerElement.find_elements(By.XPATH, ".//button")[0]
                        # jobsearch-ViewJobButtons-container
                        # jobsearch-ViewJobButtons-container
                        
                        if len(extSiteApplyButtonElement)>0:
                            # Application on an external website
                            log.debug(f"ScraperLog - Found external application button: {extSiteApplyButtonElement[0].get_attribute('innerHTML')}")
                            buttonLink = applyButtonElement.get_attribute("href")
                            if buttonLink: 
                                self.visit_page(url=buttonLink) #Accès à la page de l'annonce
                                self.random_sleep()
                                applyUrl = self.currentUrl
                            else:
                                applyUrl = postUrl
                        elif len(indeedApplyButtonElement)>0:
                            log.debug(f"ScraperLog - Found internal application button: {indeedApplyButtonElement[0].get_attribute('innerHTML')}")
                            # Application on Indeed
                            applyUrl = postUrl
                        else:
                            log.debug("ScraperLog - Apply Button (Indeed apply or external apply) was not found in the page.")
                            applyUrl = None


                    except Exception as e:

                        log.debug(f"""ScraperLog - Error:\n{json.dumps(obj={
                                "message": f"Error while scraping the job page: {e}",
                                " url": postUrl
                                }, indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                    

                    skills = []
                    scrapStatus = "new"
                    status = None
                    tags = [
                        query
                    ]

                    
                    if applyUrl is not None:
                        job = {
                        "title": title,
                        "sourceType": sourceType,
                        "platform": platform,
                        "criterias": {
                            "query": query,
                            "location":location
                        },
                        "url": postUrl,
                        "applyUrl": applyUrl,
                        "slug": slug,
                        "motherCompany": companyName,
                        "company": companyName,
                        "country": country,
                        "district": district,
                        "city": city,
                        "zipCode": zipCode,
                        "contractType": genericJobType,
                        "skills": None,
                        "description": jobDescription,
                        "scrapStatus": scrapStatus,
                        "status": None,
                        "applicationDate": None,
                        "timeoutDate": None,
                        "createdAt": createdAt,
                        "createdOn": createdOn,
                        "lastUpdated": None,
                        "tags": tags,
                        "qualificationsRequired": None,
                        "qualificationsPreferred": None,
                        "structuredData": None
                    }
                        
                        posts[location][query].append(job)
                    else:
                        log.debug(f"ScraperLog - Post #{idx_post} - applyUrl is not initialized, job discarded.")
                        #log.debug(f"ScraperLog - Post #{idx_post} - postUrl: '{postUrl}'")
                        #log.debug(f"ScraperLog - Post #{idx_post} - applyUrl: '{applyUrl}'")


                #if len(errors) != 0:
                #    with open(os.path.join(sessionFilesDir,f"errors_job_pages.json"), "w", encoding='utf-8') as f:
                #                f.write(json.dumps(obj=errors, indent=4))
                #End Scraping Logic

                self.random_sleep()


        # self.page.close()
        self.stop()
        self.random_sleep()

        jobPosts = [ ]
        for location in posts.keys():
            for query in posts[location].keys():
                jobPosts = [ *jobPosts, *posts[location][query]]
                posts[location][query] = len(posts[location][query])

        log.info(f"ScraperLog - Finished scraping jobs for {platform}, here's the count of the scraped jobs : {posts}")
        print(f"Finished scraping jobs for {platform}, here's the count of the scraped jobs : {posts}")

        return jobPosts

    def getJobsIndeedFR(self) -> list[dict]:
        posts = self.getJobsIndeed(platform="fr.indeed.com")
        return posts
    
    def getJobsIndeedCAN(self) -> list[dict]:
        posts = self.getJobsIndeed(platform="ca.indeed.com")
        return posts

    def getJobsLinkedin(self) -> list[dict]:
        return []
    def getJobsApec(self) -> list[dict]:
        return []
    def getJobsCadremploi(self) -> list[dict]:
        return []
    def getJobsHellowork(self) -> list[dict]:
        return []
    def getJobsWelcomeJungle(self) -> list[dict]:
        return []
    def getJobsPoleEmploi(self) -> list[dict]:
        return []
    def getJobsWeLoveDevs(self) -> list[dict]:
        return []
    def getJobsChooseYourBoss(self) -> list[dict]:
        return []
    def getJobsMonsterCAN(self) -> list[dict]:
        return []




if __name__ == "__main__":
    scraper = JobScraper()
    #scraper.dalJob.deleteAll()
    articles = scraper.getJobs()

