
""" Required Dependencies """
import requests
import pandas as pd
import finnhub
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import timedelta
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from firebase_functions import https_fn
from firebase_functions import scheduler_fn

""" Program Defaults """
# Stores program info such as Name, Date Created, Date Edited, Ect.
class Program():
    
    def __init__(self):
        self.name = "APICacheGenerator"
        self.date_created = "08/07/24"
        self.date_edited = "08/07/24"  

""" Helper Functions """

# Data addition decorator function
def detectStatus(func):

    def inner(*args, **kwargs):
        
        # Initializes necessary functions
        program = Program()
        firebase = Firebase()

        # Gets data key argument passes to addData function
        data_key, data_value = args[1], args[2]
        
        if data_value != None:
            attempt = func(*args, **kwargs)

            # Updates status in Firebase status firestore
            firebase.updateStatus("apis", {
                data_key: {
                    "success": True,
                    "updated": datetime.now()
                }
            })

            return attempt
        else:           
            # Error message for local debugging and cloud console
            print(f"{program.name} -> {func.__name__} failed to update API data for {data_key}.")

            # Updates status in Firebase status firestore
            firebase.updateStatus("apis", {
                data_key: {
                    "success": False,
                    "updated": datetime.now()
                }
            })
            return None
            
    return inner

# Firebase wrapper for database editing
class Firebase():
    
    # Vars necessary for interacting with Firebase Database
    def __init__(self):
        self.creds = credentials.Certificate({
        "type": "service_account",
        "project_id": "itsnousv3",
        "private_key_id": "cc1824a69238032b5d84e30a4a5722535f96e1a9",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCRPznd614mVA6G\npYhV7+OPqQUsMQUAvHNpeRg7OX9cIfTqV6U/re+iDbGXn3E3rboD2rC0nKLyuAP1\nMx5E7ps+qfOYCxIJv9u8wX1millOjjzwoI5pRTJNNvYZD1BJJ8DfW0WmUEy3kNbx\n0dW8n83Da3jILhV1OM1sLfEr+0hXmfzZLzAi6fhDvynzCzdORGF6M8UjU5uMB/vI\nsOnF+Q3mdmXaO60Ff10+xRYcI6cqMhgjkQtmlBJiIgoM9wDgJbqUyAdJ6qRFT+K7\nzQotOdjdJucY0QL5vO87ob75zU5GqmxVH8h5mW1gsOnd1mqbmM2Yd8i3PeJlHstX\nEQLGgBzTAgMBAAECggEAA3mfyM940THxpwcO2/+BUk6Y8RW7KOlZWYysJ76YbXvi\ngDjYm01uDlKFjTsjWlGtwanZ0Hhu7Z+5eIRglQWgcT9ftKOPKuyMNVfryChHOrns\ne1VcEui062QFP1Q+d4Gb+7wTToddTocInYCHvJuWMLbBjQiNOuDBCXWP751zfaUI\nTWyBgL8oMk+CXOe/NOPjEPbJpwXVITWVD/sEzZpj9s/xSYiKUl4U8dYJKkjWj4A+\nsIZPW9MvpmbBHk+2bu4DUVGoPVmh2zMulPLZALOmDazUcIXPWWSzLVfR869U2qUW\nk79Y26BSZB7TM1436kBjw38Oo/FqjAERAel2VgciAQKBgQDCaALVDyYUANyzIDWL\nypck+0EmBAB1SBVFPLAEJ6/pK8G5RH6zsLzOb5PvK/+LAKQ/Zvug3BxrQU8CVgeK\nj3zWrUcFs8PG67xRRi1GgFvPg6SQLMayRvCQHE3B5YunBXyH9x4lC6ypGOsWLgmr\n5EB4cTOhfSWOA0zTVyCND1E7mwKBgQC/Q/rl+Yj2TrARiAqMt2qhlNlgyTRuQjL+\nyBJm0qmKaRad+gLgCj7AdJU7yKFcG2G74Fa9yL7sF/EmPAYynk0YQh7K5Daq7abe\nf9b0unmrF7t2s4J/2VIn7oMfxa35N7gkOxR6dENLZE8UooHCjs41LAe5BddFITry\nSfwsp+xDKQKBgCp4KG49Efd6vLwRBEGWr3Avx2qzoxn79lGa0WUG+oH4wihkEz3U\nFVsPuwSb2waVzEvhhoT8sOSpbsY23wzhDcekMQjI3bMeGpSyvP9S2Tu7KX8pmPqn\nTrRcyovaRqjlJPBbBuXW6BBE1k6RHiHECmWFbV8RBNxCUk01EnJeb0OTAoGABxSD\nIyQ7l7KN/fglO9RGVDjoWxbXpAU7Ugch90BxGjiNp8drd9OpQwKNy6q/nmM9GPFT\nBK97sc2pFZs/N3x4qh84eJY+F9G4TaA52tFUU6sLO3elqwnmaqf/npt4tzMC1ASD\n24yWOSI7cy4Y05TpuToqBwVaVKrIPdPTS+vjaRECgYAVKH3x3/E6WuD4uHT/JREZ\nAJAofVAwokrM/CHP9vFf1YwpjG79Q0voN/rt/Z5Wi/91FVBw043NcGeNksu8+Ude\nYejYD6h7VTQvqAk64wWPBNFHtLs3FWFEoq0xH7DiCs5+LdpOs0cHhTuTOVbTnLGU\nhfKvczNHj4GrmC2TvDHTjw==\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk-66v6t@itsnousv3.iam.gserviceaccount.com",
        "client_id": "116580107322819075852",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-66v6t%40itsnousv3.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    })
    
    # Adds data to firebase database
    @detectStatus
    def addData(self, name: str, data: dict):
 
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            db = firestore.client()
            project_ref = db.collection("apis").document(name)
            project_ref.set(data, merge=True)

    # Updates status for firebase database
    def updateStatus(self, name: str, data: dict):
 
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            db = firestore.client()
            project_ref = db.collection("status").document(name)
            project_ref.set(data, merge=True)

# Fault detection decorator function
def detectFault(func):
    
    def inner(*args, **kwargs):
        
        # Initializes necessary functions
        program = Program()
        
        try:
            return func(*args, **kwargs)
        except Exception as error:
            print(f"{program.name} -> {func.__name__} failed and gave this error: {error}")
            return None

    return inner

# Manages dates
class DateManager():
    
    # Essential vars for Date Manager
    def __init__(self):
        self.today = datetime.now()

    # Get date today in string
    def getTodayStr(self):
        return self.today.strftime("%Y-%m-%d")
    
    # Gets date that is certain number of days in future
    def getFutureDateStr(self, days: int):
        return datetime.strftime((self.today + timedelta(days=days)), '%Y-%m-%d')
    
    # Gets date that is certain number of days in future
    def getFutureYearStr(self, years: int):
        return datetime.strftime((self.today - relativedelta(years=years)), '%Y-%m-%d')

    # Calculates difference between date now and later
    def getDayDifference(self, date: str):
        difference = datetime.strptime(date, '%Y-%m-%d') - datetime.now()
        return difference.days

""" API Wrappers """

# U.S. Bureau of Economic Analysis
class BEA_Gov():

    # Essential vars for BEA Gov API
    def __init__(self):
        self.display_name = "U.S. Bureau of Economic Analysis"
        self.description = "The U.S. Bureau of Economic Analysis is a government provided source of accurate and objective data about the nation's economy."
        self.link = "https://www.bea.gov/"
        self.key = "713E8652-FB92-48A4-A9E3-47AADEEC29A7"
        self.base_url = "https://apps.bea.gov/api/data"

    # Helper Function to get possible Datasets
    @detectFault
    def getDatasets(self):
        params = {
            "UserID": self.key,
            "Method": "GETDATASETLIST",
            "ResultFormat": "JSON"
        }
        return requests.get(self.base_url, params=params).json()["BEAAPI"]["Results"]

    # Helper Function to get Params
    @detectFault
    def getParams(self, dataset_name: str):
        params = {
            "UserID": self.key,
            "Method": "GETPARAMETERLIST",
            "ResultFormat": "JSON",
            "DatasetName": dataset_name
        }
        return requests.get(self.base_url, params=params).json()["BEAAPI"]["Results"]
    
    # Helper Function to get possible Param Values
    @detectFault
    def getParamsValues(self, dataset_name: str, parameter_name: str):
        params = {
            "UserID": self.key,
            "Method": "GETPARAMETERVALUES",
            "ResultFormat": "JSON",
            "DatasetName": dataset_name,
            "ParameterName": parameter_name
        }
        return requests.get(self.base_url, params=params).json()["BEAAPI"]["Results"]
    
    # Helper Function to get Data
    @detectFault
    def getData(self, dataset_name: str, table_name: str, additional_params: list[tuple]):
        params = {
            "UserID": self.key,
            "Method": "GETDATA",
            "ResultFormat": "JSON",
            "DatasetName": dataset_name,
            "TableName": table_name
        }

        for param in additional_params:
            params[param[0]] = param[1]

        return requests.get(self.base_url, params=params).json()["BEAAPI"]["Results"]
    
    # Processes Personal Consumption Expenditure Data
    @detectFault
    def processPCEData(self, data: dict):
        PCE_Data = {}

        for line_number in range(1, 31):
            dataframe = pd.DataFrame(data, columns = ['LineNumber', 'LineDescription', 'TimePeriod', 'DataValue'])
            dataframe = dataframe.loc[dataframe['LineNumber'] == f"{line_number}"]
            PCE_Data[dataframe['LineDescription'].loc[dataframe.index[0]]] = {
                "key": dataframe["TimePeriod"].tolist(),
                "value": dataframe["DataValue"].tolist()
            }
          
        return PCE_Data
    
    # Processes Gross Domestic Product Data
    @detectFault
    def processGDPData(self, data: list):
        GDP_Data = {}

        for line_number in range(1, 26):
            dataframe = pd.DataFrame(data, columns = ['LineNumber', 'LineDescription', 'TimePeriod', 'DataValue'])
            dataframe = dataframe.loc[dataframe['LineNumber'] == f"{line_number}"]
            
            try:
                GDP_Data[dataframe['LineDescription'].loc[dataframe.index[0]]] = {
                    "key": dataframe["TimePeriod"].tolist(),
                    "value": dataframe["DataValue"].tolist()
                }
            except:
                None
          
        return GDP_Data

    # References Table 2.8.5 from BEA Government showing "Personal Consumption Expenditures by Major Type of Product, Monthly (M)"
    @detectFault
    def getPCEbyMonthValue(self):
        data = self.getData(
            "NIPA",
            "T20805",
            [
                ("Frequency", "M"),
                ("Year", DateManager().today.year)
            ]
        )["Data"]

        return self.processPCEData(data)
    
    # References Table 2.8.1 from BEA Government showing "Percent Change From Preceding Period in Real Personal Consumption Expenditures by Major Type of Product, Monthly (M)"
    @detectFault
    def getPCEbyMonthPercentChange(self):
        data = self.getData(
            "NIPA",
            "T20801",
            [
                ("Frequency", "M"),
                ("Year", DateManager().today.year)
            ]
        )["Data"]

        return self.processPCEData(data)
    
    # References Table 1.1.5 from BEA Government showing "Gross Domestic Product (A) (Q)"
    @detectFault
    def getGDPByQuartersValue(self):
        data = self.getData(
            "NIPA",
            "T10105",
            [
                ("Frequency", "Q"),
                ("Year", f"{DateManager().today.year-1}, {DateManager().today.year}")
            ]
        )["Data"]

        return self.processGDPData(data)
    
    # References Table 1.1.1 from BEA Government showing "Percent Change From Preceding Period in Real Gross Domestic Product (Q)"
    @detectFault
    def getGDPByQuartersPercentChange(self):
        data = self.getData(
            "NIPA",
            "T10101",
            [
                ("Frequency", "Q"),
                ("Year", f"{DateManager().today.year-1}, {DateManager().today.year}")
            ]
        )["Data"]
        
        return self.processGDPData(data)
    
    # References Table _._._ from BEA Government showing "Percent Change From Preceding Period in Real Gross Domestic Product Price (Q)"
    @detectFault
    def getGDPByQuartersPricePercentChange(self):
        data = self.getData(
            "NIPA",
            "T10107",
            [
                ("Frequency", "Q"),
                ("Year", f"{DateManager().today.year-1}, {DateManager().today.year}")
            ]
        )["Data"]
        
        return self.processGDPData(data)

# FiscalData Treasury Government
class FiscalData_Treasury_Gov():
    
    # Essential vars for FiscalData Treasury Gov
    def __init__(self):
        self.display_name = "U.S. Treasury Fiscal Data"
        self.description = "The U.S. Treasury Fiscal Data is provided by the department of treasury and consolidates federal financial data."
        self.link = "https://fiscaldata.treasury.gov/"
        self.base_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"

    # Helper function to get Average Interest Rates
    @detectFault
    def processAvgInterestRates(self, data: list):
        dataframe = pd.DataFrame(data)
        return {
            "AvgInterestRates": {
                "key": dataframe["record_date"].tolist(),
                "value": dataframe["avg_interest_rate_amt"].tolist()
            }
        }

    # References FiscalData Treasury API to get interest rates on Treasury Floating Rate Notes
    @detectFault
    def getAvgInterestRates(self):
        params = {
            "fields": "record_date,avg_interest_rate_amt",
            "format": "json",
            "filter": f"record_date:gte:{DateManager().getFutureYearStr(1)},security_desc:eq:Treasury Floating Rate Notes (FRN)"
        }
        return self.processAvgInterestRates(
            requests.get(f"{self.base_url}v2/accounting/od/avg_interest_rates", params=params).json()["data"]
        )

# Finnhub Wrapper for stock data and trends
class Finnhub():
    
    # Vars neccessary for requests to Finnhub
    def __init__(self):
        self.display_name = "Finnhub API"
        self.description = "Finnhub is a financial institution that provides finance data used by institutions like Google, Coca-Cola, and Baidu."
        self.link = "https://finnhub.io/"
        self.key = "cqe75npr01qgmug3pc6gcqe75npr01qgmug3pc70"
        self.finnhub_client = finnhub.Client(api_key="cqe75npr01qgmug3pc6gcqe75npr01qgmug3pc70")

    # Gets market status and determines if it is open
    @detectFault
    def getMarketStatus(self):
        return self.finnhub_client.market_status(exchange='US')["isOpen"]
    
    # Gets realtime price of a stock
    @detectFault
    def getStockPrice(self, symbol: str):
        return self.finnhub_client.quote(symbol)
    
    # Gets sentiment regarding stocks
    @detectFault
    def getStockSentiment(self, symbol: str):
        return self.finnhub_client.stock_insider_sentiment(symbol, DateManager().getTodayStr(), DateManager().getTodayStr())["data"]
    
    # Gets info regarding company name from symbol
    @detectFault
    def getStockInfo(self, symbol: str):
        return self.finnhub_client.symbol_lookup(symbol)["result"][0]["description"]
    
    # Processes the earnings calender data
    @detectFault
    def processUpcomingEarnings(self, data: list):
        p_earnings = []
        
        for earningsData in data:
            p_earnings.append(
                {
                    "symbol": earningsData["symbol"],
                    "company_name": self.getStockInfo(earningsData["symbol"]),
                    "date": earningsData["date"],
                    "dateFromNow": DateManager().getDayDifference(
                        earningsData["date"]
                    )
                }
            )
            
            if len(p_earnings) > 5:
                break
        
        return {
            "UpcomingEarnings": p_earnings
        }
    
    # Proccesses news object list
    @detectFault
    def processNews(self, data: list, type: str):
        p_news = []

        for newsData in data:
            p_news.append(
                {
                    "title": newsData["headline"],
                    "image": newsData["image"],
                    "url": newsData["url"],
                    "source": newsData["source"]
                }
            )
            
            if len(p_news) > 5:
                break
        
        return {
            type: p_news
        }
 
    # Gets values of major ETFs
    @detectFault
    def getMajorETFs(self):
        major_ETFs = {
            "TotalMarket": [
                "VTI"
            ],
            "S&P500": [
                "SPY",
                "VOO",
                "OEF",
                "RPG",
                "RPV",
                "IVE"
            ],
            "NASDAQ100": [
                "QQQ",
            ],
            "Russell1000": [
                "IWM",
                "IWB",
                "IWF"
            ]
        }

        for index in major_ETFs.keys():
            ETFs = major_ETFs[index]
            p_ETFs = []
            for symbol in ETFs:
                p_ETFs.append(
                    {
                        "symbol": symbol,
                        "data": self.getStockPrice(symbol)
                    }
                )
            major_ETFs[index] = p_ETFs

        return major_ETFs

    # Gets earnings dates of company's for next seven days
    @detectFault
    def getUpcomingEarnings(self):
        return self.processUpcomingEarnings(
            self.finnhub_client.earnings_calendar(
                _from=DateManager().getTodayStr(), 
                to=DateManager().getFutureDateStr(2), 
                symbol="",
                international=False
            )["earningsCalendar"]
        )
    
    # Gets general market news
    @detectFault
    def getMarketNews(self):
        return self.processNews(
            self.finnhub_client.general_news(
                'general', 
                min_id=0
            ),
            "MarketNews"
        )
    
    # Gets market news regarding mergers
    @detectFault
    def getMarketMergers(self):
        return self.processNews(
            self.finnhub_client.general_news(
                'merger', 
                min_id=0
            ),
            "Mergers"
        )

# Wrapper for APINinjas
class APINinjas():
    
    def __init__(self):
        self.display_name = "API Ninjas"
        self.description = "API Ninjas hosts over 80 individual endpoints that are used by organizations like IBM and Cisco."
        self.link = "https://api-ninjas.com/"
        self.key = "aC4UuyXTr3AjN8EDKVvmMw==BOOtkOWnsI8KBtMW"
        self.base_url = "https://api.api-ninjas.com/v1/facts"

    # Retrieves one random fact
    @detectFault
    def getFact(self):
        headers = {
            "X-Api-Key": self.key
        }

        response = requests.get(
            f"{self.base_url}",
            headers=headers
        )

        return response.json()[0]["fact"]
    
    # Retrieves specified number of facts
    @detectFault
    def getFacts(self, number: int):
        response = {
            "Facts": []
        }
        
        for index in range(number):
            response["Facts"].append(
                {
                    "Fact": self.getFact()
                }
            )

        return response
    
# Wrapper for Humor API
class HumorAPI():
    
    def __init__(self):
        self.key = "aab9f4d1bef74c8d98449dd2273f44fb"
    
    # Retrieves one random joke
    def getJoke(self):
        params = {
            "min-rating": 8,
            "api-key": self.key
        }

        response = requests.get("https://api.humorapi.com/jokes/random", params=params)

        joke = response.json()["joke"]
        p_joke = []

        if "\n" in joke:
            p_joke += joke.split("\n")
        else:
            p_joke += [joke]
        
        return p_joke
    
    # Retrieves specified number of jokes and returns response
    @detectFault
    def getJokes(self, number: int):
        
        response = {
            "Jokes": []
        }
        
        for index in range(number):
            response["Jokes"].append(
                {
                    "Joke": self.getJoke()
                }
            )

        return response

""" Firebase Functions """

# The Google Cloud Config for this function is 1 vCPU and 256 Mi (mebibyte)
# 5:00 AM UTC -> 1:00 AM EST
# Firebase function to update api data daily to reduce redundant api calls
@scheduler_fn.on_schedule(schedule="every day 05:00")
def updateAPIDataDaily(event: scheduler_fn.ScheduledEvent) -> None:
    
    # Retrieves relevant Firebase functions
    firebase = Firebase()
    
    # Updates data from Finnhub
    finnhub = Finnhub()

    firebase.addData("market_news", finnhub.getMarketNews())
    # print(finnhub.getMarketNews())

    firebase.addData("mergers", finnhub.getMarketMergers())
    # print(finnhub.getMarketMergers())

    firebase.addData("earnings", finnhub.getUpcomingEarnings())
    # print(finnhub.getUpcomingEarnings())

    firebase.addData("indexs", finnhub.getMajorETFs())
    # print(finnhub.getMajorETFs())

    # Updates data from FiscalData
    fiscaldata = FiscalData_Treasury_Gov()

    firebase.addData("interest_rates", fiscaldata.getAvgInterestRates())
    # print(fiscaldata.getAvgInterestRates())

    # Updates data from BEA
    bea = BEA_Gov()

    firebase.addData("spending", bea.getPCEbyMonthPercentChange())
    # print(bea.getPCEbyMonthPercentChange())

    firebase.addData("gdp", bea.getGDPByQuartersPercentChange())
    # print(bea.getGDPByQuartersPercentChange())

    firebase.addData("inflation", bea.getGDPByQuartersPricePercentChange())
    # print(bea.getGDPByQuartersPricePercentChange())

    # Updates data from HumourAPI
    humor_api = HumorAPI()

    firebase.addData("jokes", humor_api.getJokes(5))
    # print(humor_api.getJokes(5))

    # Updates data from APINinjas
    apininjas = APINinjas()

    firebase.addData("facts", apininjas.getFacts(5))
    # print(apininjas.getFacts(5))

    return https_fn.Response("Success")