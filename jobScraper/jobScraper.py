from selenium import webdriver #Webdriver de Selenium qui permet de contrôler un navigateur
from selenium.webdriver.common.by import By #Permet d'accéder aux différents élements de la page web
#from selenium.webdriver.remote.webelement

from webdriver_manager.chrome import ChromeDriverManager #Assure la gestion du webdriver de Chrome

from datetime import datetime, timedelta
import math
import time
import requests

import warnings
warnings.filterwarnings("ignore")
import os
import json
from definitions import ROOT_DIR, COUNTRY_CODES_MAP
import re

import logging as log
log.basicConfig(filename=os.path.join(ROOT_DIR,"logs","scraper.log"), encoding='utf-8', filemode='w', format='%(asctime)s-%(levelname)s:%(message)s', level=log.DEBUG)

class JobScraper:
    def __init__(self) -> None:
        self.debug = False
        self.dalJob = self.DataAccessLayer(resourceName="job")#, apiUrl="http://192.168.1.99:8000")
        self.today = datetime.now()
        self.targetDay = self.today
        self.year = str(self.targetDay.year)
        self.month = str(self.targetDay.month)
        self.day = "0" + str(self.targetDay.day) if len(str(self.targetDay.day)) < 2 else str(self.targetDay.day) #on ajoute 0 devant le jour s'il est compris entre 1 et 9
        self.driver = None #webdriver.Chrome()#ChromeDriverManager().install()) 
        #time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante 
        self.sessionDirPath = ""
        self.sessionPlatformFilesPath = ""
        self.fsTimestamp = ""
        self.dbTimestamp = ""
        self.countryCode = ""
        self.antibotFlagPauseSeconds = 2.5
        
    
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
        
        def postOne(self, obj: dict):
            log.info(f"{self.resourceName}Dal--postOne-Start")
            try:
                res = requests.post(url=f"{self.apiUrl}/",
                                    json=obj
                                    )
                if res.status_code == 201:
                    log.debug(f"Object created in database:\n{res.json}")
                else:
                    log.debug(f"Error while creating the object in database:\nStatus code:{res.status_code}\nmessage:{res.content}")
            except Exception as e:
                log.debug(f"Error: {e}")
            log.info(f"{self.resourceName}Dal--postOne-End")

        def postMany(self, objList: list[dict]):
            log.info(f"{self.resourceName}Dal--postMany-Start")
            for obj in objList:
                self.postOne(obj)
            log.info(f"{self.resourceName}Dal--postMany-End")

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
        return ["kotlin"]
        commonList = [
            "kotlin",
            "flutter",
            "python",
            "javascript"
            ]
        countryList = {
            "FR": ["développeur mobile"],
            "CAN": ["mobile developer"],
            "CAN-QC": ["développeur mobile"],
        }
        cList: list = countryList[countryCode]
        return [*commonList,*cList]

    def getJobs(self):
        year = self.year
        month = self.month
        day = self.day

        sessionTimestamp = datetime.now()
        self.fsTimestamp = sessionTimestamp.strftime("%Y-%m-%d_%H-%M-%S")
        self.dbTimestamp = sessionTimestamp.strftime("%Y-%m-%dT%H:%M:%S")
        sessionFilesPath = os.path.join(ROOT_DIR,"logs","sessionFiles",self.fsTimestamp)
        os.mkdir(sessionFilesPath)

        self.sessionDirPath = os.path.join(ROOT_DIR,sessionFilesPath,"jobs")
        os.mkdir(self.sessionDirPath)

        platforms = {
            #"FR_linkedIn": self.getJobsLinkedin,
            "FR_indeed": self.getJobsIndeed,
            #"FR_apec": self.getJobsApec,
            #"FR_cadremploi": self.getJobsCadremploi,
            #"FR_hellowork": self.getJobsHellowork,
            #"FR_welcome2jungle": self.getJobsWelcomeJungle,
            #"FR_poleEmploi": self.getJobsPoleEmploi,
            #"FR_weLoveDevs" : self.getJobsWeLoveDevs,
            #"FR_chooseYourBoss": self.getJobsChooseYourBoss,
            #"CAN_Monster": self.getJobsMonsterCAN
        }

        for idx_ptf, platform in enumerate(platforms.keys()):
            self.countryCode = platform.split("_")[0]
            self.sessionPlatformFilesPath = os.path.join(self.sessionDirPath,f"{idx_ptf}.{platform}")
            os.mkdir(self.sessionPlatformFilesPath)
            sessionFailuresPath = os.path.join(self.sessionPlatformFilesPath,"failures")
            os.mkdir(sessionFailuresPath)
            
            platformJobs = platforms[platform]()

            if len(platformJobs) >0: self.dalJob.postMany(objList=platformJobs)


    def getJobsIndeed(self) -> list[dict]:
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

        def extractZipCodeFromCity(inStr: str | None) -> tuple[str,str]:
            if inStr is None: return ("","")
            zip = inStr.split(" ")[-1].replace("(","").replace(")","")
            wkStr = inStr.split(" ")
            wkStr.pop(-1)
            city = " ".join(wkStr)
            return (city, zip)

        platform = "fr.indeed.com"
        createdAt = self.dbTimestamp
        createdOn = self.dbTimestamp.split("T")[0]
        country = COUNTRY_CODES_MAP[self.countryCode]
        sourceType = "jobBoard"
        

        sessionFilesDir = self.sessionPlatformFilesPath
        self.driver = webdriver.Chrome()#ChromeDriverManager().install()) 
        time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante

        #Start Scraping Logic
        locations = ["Île-de-France"]#, "Lyon"]
        queries = self.getSearchQueries()
        postUrlsDict = {}
        errors=[]
        for idx_loc, location in enumerate(locations):
            for idx_q, query in enumerate(queries):
                queryString = "+".join(query.split(" "))
                url = f"https://fr.indeed.com/jobs?q={queryString}&l={location}&sort=date&fromage=1"
                page = 1
                log.info(f"ScraperLog - New job search>query:'{query}', location:'{location}'\n{url}")
                totalJobsCount = 0
                self.driver.get(url=url) #Accès aux annonces du jour'
                #btnDateFilter = self.driver.find_element(By.ID, "filter-dateposted") #On identifie le bouton 
                #self.driver.execute_script("arguments[0].click();", btnDateFilter); # On clique dessus
                lastPage = False
                
                while not lastPage:
                    log.info(f"ScraperLog - Getting job urls on page {page}...")
                    """
                    try:
                        jobCardsContainer = self.driver.find_element(By.ID,"mosaic-provider-jobcards")
                        jobCards = jobCardsContainer.find_elements(By.XPATH,"//ul//child:li")
                        for jobCard in jobCards:
                            aTagId = jobCard.find_element(By.XPATH,"//h2[starts-with(@class,'jobTitle')]//a").get_attribute("id")
                            jobId = aTagId.split("_")[1] if aTagId else None
                            
                            if jobId: 
                                jobPostUrl = f"https://fr.indeed.com/viewjob?jk={jobId}"
                                postUrls[jobId] = jobPostUrl
                    except Exception as e: #
                        log.debug({
                            "message": f"Error while scraping the main page: {e}",
                            " location" : location,
                            "query": query,
                            " url": url
                            }) #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                    ^v1
                    """

                    
                    jobCardsContainer = self.driver.find_elements(By.ID,"mosaic-provider-jobcards")
                    jobCardsContainer = jobCardsContainer[0] if len(jobCardsContainer) >0 else None
                    if jobCardsContainer is None: 
                        log.debug(f"""ScraperLog - Error:\n{json.dumps(obj={
                            "message": f"Error while scraping the main page: 'mosaic-provider-jobcards' not found",
                            " location" : location,
                            "query": query,
                            " url": url
                            }, indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                        continue

                    jobCards = jobCardsContainer.find_elements(By.XPATH,".//*[@dir]")#jobCardsContainer.find_elements(By.XPATH,"//ul//child:li")
                    pageJobsCount = len(jobCards)
                    totalJobsCount += pageJobsCount
                    log.debug(f"ScraperLog - {pageJobsCount} cards/jobs found on page {page}")
                    for idx_jobCard, jobCard in enumerate(jobCards):
                        log.debug(f"ScraperLog - jobCard #{idx_jobCard}:\n>>>\n{jobCard.get_attribute('innerHTML')}\n<<<\n")
                        aTagId = jobCard.find_elements(By.XPATH,".//h2[starts-with(@class,'jobTitle')]//a")
                        aTagId = aTagId[-1] if len(aTagId) >0 else None
                        if aTagId is None: 
                            log.debug(f"""ScraperLog - Error:\n{json.dumps(obj={
                            "message": f"Error while scraping the main page: job card hyperlink (a tag) not found",
                            " location" : location,
                            "query": query,
                            " url": url
                            }, indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                            continue
                        else:
                            log.debug(f"ScraperLog - jobCard #{idx_jobCard}:Found a job title: retrieving job ID...")
                            log.debug(f"Title:\noOoOoOoOoOo\n{aTagId.get_attribute('innerHTML')}\noOoOoOoOoOo\n")
                        
                        # Looking for the direct HTML element holding the job ID
                        aTagId = aTagId.find_elements(By.XPATH,".//*[starts-with(@id,'jobTitle')]")
                        aTagId = aTagId[0] if len(aTagId) >0 else None
                        if aTagId is None: 
                            log.debug(f"""ScraperLog - Error:\n{json.dumps(obj={
                            "message": f"Error while scraping the main page: job card hyperlink (a tag) HTML id holder not found",
                            " location" : location,
                            "query": query,
                            " url": url
                            }, indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
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
                            " location" : location,
                            "query": query,
                            " url": url
                            },indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
                            continue
                        jobId = re.split("-|_", aTagId)[1] #aTagId.split("_")[1] if aTagId else None
                        log.debug(f"ScraperLog - jobId: {jobId}")
                        if jobId: 
                            jobPostUrl = f"https://fr.indeed.com/viewjob?jk={jobId}"
                            postUrlsDict[jobPostUrl] = {
                                "url": jobPostUrl,
                                "query": query,
                                "location": location
                            }

                    """
                    ^v2
                    """

                    """
                    try:
                        btnNext = self.driver.find_element(By.XPATH, "//a[@data-testid='pagination-page-next']") #On identifie le bouton 
                    except Exception as e:
                        print(e)
                        btnNext = None
                    ^v1
                    """
                    btnNext = self.driver.find_elements(By.XPATH, "//a[@data-testid='pagination-page-next']") #On identifie le bouton 
                    btnNext = btnNext[0] if len(btnNext) >0 else None
                    """
                    ^v2
                    """
                    if btnNext: 
                        self.driver.execute_script("arguments[0].click();", btnNext); # On clique dessus
                        page +=1
                        time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante

                    else:
                        lastPage = True
                        log.debug(f"ScraperLog - {totalJobsCount} jobs in total found for the following job search> query:'{query}', location:'{location}'")
                        time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante
                        

        if len(errors) != 0:
            with open(os.path.join(sessionFilesDir,f"errors_main_page.json"), "w", encoding='utf-8') as f:
                        f.write(json.dumps(obj=errors, indent=4))

        postUrls = list(postUrlsDict.keys())
        #print(postUrls)# if self.debug else {}
        log.debug(f"ScraperLog - postsUrls: {postUrls}")
        posts = []
        errors = []

        for idx_post, postUrl in enumerate(postUrls):
            if postUrl in self.dalJob.scrapedUrlsInDb:
                log.info(f"Post {idx_post} - SKIPPED - Post already scraped: Post Url already in database\nurl: {postUrl}")
                continue
            self.driver.get(url=postUrl)
            time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante
            log.info(f"ScraperLog - Scraping Post #{idx_post}: {postUrl}")

            slug = postUrl.split("/")[-1]

            try:
                # Récupération du body de la page:
                body = self.driver.find_element(By.XPATH, "/html/body")

                """
                Sauvegarde des sources de la page scrappée sur le disque
                """
                if self.debug:
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
                city, zipCode = extractZipCodeFromCity(jobLocation)

                jobDescriptionElement = body.find_element(By.ID, "jobDescriptionText")
                jobDescriptionHTML = jobDescriptionElement.get_attribute("innerHTML")
                jobDescription = cleanPostDescription(html=jobDescriptionHTML)

                applyButtonElement = body.find_elements(By.XPATH,".//div[@id='jobsearch-ViewJobButtons-container']")[0].find_elements(By.XPATH, ".//button")[0]
                applyButtonText = applyButtonElement.get_attribute("innerText")
                applyUrl = None
                match applyButtonText:
                    case "Continuer pour postuler":
                        buttonLink = applyButtonElement.get_attribute("href")
                        if buttonLink: 
                            self.driver.get(url=buttonLink)
                            time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante
                            applyUrl = self.driver.current_url
                    case "Postuler maintenant":
                        # Indeed Apply
                        applyUrl = postUrl
                    case _:
                        log.debug("ScraperLog - Apply Button was not found in the page.")

            except Exception as e:
                log.debug(f"""ScraperLog - Error:\n{json.dumps(obj={
                        "message": f"Error while scraping the job page: {e}",
                        " url": postUrl
                        }, indent=4)}""") #On ajoute dans une liste tous les articles dont n'où n'avons pas pu scrapper le contenu
            

            skills = []
            scrapStatus = "new"
            status = None
            tags = [
                postUrlsDict[postUrl]["query"]
            ]

            job = {
                "title": title,
                "sourceType": sourceType,
                "platform": platform,
                "criterias": {
                    "query": postUrlsDict[postUrl]["query"],
                    "location":postUrlsDict[postUrl]["location"]
                },
                "url": postUrl,
                "applyUrl": applyUrl,
                "slug": slug,
                "motherCompany": companyName,
                "company": companyName,
                "country": country,
                "district": None,
                "city": city,
                "zipCode": zipCode,
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
                "qualificationsPreferred": None
            }
            posts.append(job)

        if len(errors) != 0:
            with open(os.path.join(sessionFilesDir,f"errors_job_pages.json"), "w", encoding='utf-8') as f:
                        f.write(json.dumps(obj=errors, indent=4))
        #End Scraping Logic

        time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante 
        self.driver.close()
        time.sleep(self.antibotFlagPauseSeconds) #Ajout d'un temps de deux secondes avant de lancer l'action suivante
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

