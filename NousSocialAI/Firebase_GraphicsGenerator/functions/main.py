
""" Required Dependencies """
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from firebase_admin import storage
from firebase_functions import scheduler_fn
from firebase_functions import https_fn
import random
import matplotlib.pyplot as plt
from PIL import Image
import requests
import io
from boto3 import Session
from contextlib import closing
import numpy as np
from datetime import datetime

""" Program Defaults """
# Stores program info such as Name, Date Created, Date Edited, Ect.
class Program():
    
    def __init__(self):
        self.name = "GraphicsGenerator"
        self.date_created = "08/08/24"
        self.date_edited = "08/08/24"  

""" Helper Functions """

# Object container for return
class Asset():
    
    def __init__(self, asset_id: int, text: str, graphic: str, directory = "wallstreetwaves"):
        self.text = text
        self.audio = AWS().genSpeech(
            asset_id, 
            directory,
            self.text
        )
        self.graphic = graphic

    def to_dict(self):
        return {
            "text": self.text,
            "audio": self.audio,
            "graphic": self.graphic
        }
    
# Wrapper for base asset class but designed for Comedy
class ComedyAsset():
    
    def __init__(self, id: int, text: str):
        self.graphics = Graphics()
        self.asset = Asset(
            id,
            text,
            self.graphics.genComedyGraphic(
                id, 
                text
            ),
            "comedy"
        )

    def to_dict(self):
        return self.asset.to_dict()
    
# Wrapper for base asset class but designed for Fact
class FactAsset():
    
    def __init__(self, id: int, text: str):
        self.graphics = Graphics()
        self.asset = Asset(
            id,
            text,
            self.graphics.genFactGraphic(
                id, 
                text
            ),
            "fact"
        )

    def to_dict(self):
        return self.asset.to_dict()

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
        self.img_directory = "NousSocialGraphics/"
        self.audio_directory = "NousSocialAudio/"

    # Retrieves cache of api data
    def retrieveAPICache(self):
        
        api_cache = []
        
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            db = firestore.client()
            docs = (
                db.collection("apis").stream()
            )

            for doc in docs:

              api_cache.append(doc.to_dict())
        
        return api_cache
    
    # Retrieves default youtube description
    def retrieveYouTubeDescriptionTemplate(self, line: str):    
        response = requests.get("https://storage.googleapis.com/itsnousv3.appspot.com/YouTubeDefaults/YouTubeDefaultDescription.json")
        return response.text.replace("[PLACEHOLDER]", line)

    # Uploads image from BytesIO
    def uploadImgfromCache(self, file_name: str, image_data: io.BytesIO):
        
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            bucket = storage.bucket(name="itsnousv3.appspot.com")
            blob = bucket.blob(f"{self.img_directory}{file_name}")

            blob.upload_from_string(image_data.getvalue(), content_type='application/png')
            image_data.close()
            blob.make_public()
            return blob.public_url
        
    # Uploads audio from data
    def uploadAudiofromCache(self, file_name: str, audio_data: str):
        
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            bucket = storage.bucket(name="itsnousv3.appspot.com")
            blob = bucket.blob(f"{self.audio_directory}{file_name}")

            blob.upload_from_string(audio_data, content_type='application/mpeg')

            blob.make_public()
            return blob.public_url
        
    # Adds data to firebase database
    def addData(self, name: str, data: dict):
 
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            db = firestore.client()
            project_ref = db.collection("scripts").document(name)
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
        
# References Amazon Web Services Polly Engine for Text-to-Speech
class AWS():
    
    # Vars neccessary for interacting with Amazon Polly
    def __init__(self):
        self.session = Session(
            aws_access_key_id="AKIA5P5MKHY3WPJ2WIHE",
            aws_secret_access_key="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"
        )
        self.polly_client = self.session.client(
            "polly",
            region_name='us-west-2'
        )
        self.firebase = Firebase()

    # Generates speech
    def genSpeech(self, id: int, directory: str, text: str):
        response = self.polly_client.synthesize_speech(
            Text=text, 
            OutputFormat="mp3",
            VoiceId="Matthew",
            Engine="neural"
        )

        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                try:
                    return self.firebase.uploadAudiofromCache(
                        f"{directory}/audio_{id}.mp3", 
                        stream.read()
                    )
                except IOError as error:
                     return None
        else:
            return None

""" Main Graphics Creation """ 

# Wrapper to generate basic graphics
class Graphics():
    
    def __init__(self):
        self.graphics = []
        self.firebase = Firebase()

    # Gets image from url and resizes
    def getImage(self, url: str, resize = (False, (0, 0))):
        
        image = io.BytesIO()   

        r = requests.get(url, stream=True)
        if r.status_code == 200:
            for chunk in r:
                image.write(chunk)
                
        if resize[0] == True:
            return Image.open(image).resize(resize[1])
        else:
            return np.array(Image.open(image))
          
    # Splits up title and processes
    def processText(self, character_break: int, max_lines: int, sentence: str):
        
        p_list = []
        words = sentence.split()
        line = 0

        for word in words:
            
            if not p_list:
                p_list.insert(
                    line, 
                    f"{word} "
                )
            elif len(p_list[line]+word) > character_break:
                if (line == max_lines):
                    p_list[line] += "..."
                    break
                else:
                    line += 1
                    p_list.insert(
                        line, 
                        f"{word} "
                    )
            else:
                p_list[line] += f"{word} "

        return p_list
    
    # Generates a news graphic
    def genNewsGraphic(self, id: int, img_url: str, text: str, subtitle: str):
        
        fig = plt.figure()
        fig.figimage(
            self.getImage(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/basicGraphicTemplateActive.png"
            ), 
            resize=True
        )

        # Processes text and fontsize parameters
        text = self.processText(18, 3, text)
        fontsize = 16
        y_point = 0.9

        # Thumbnail Image
        fig.figimage(
            self.getImage(
                img_url,
                (True, (130, 130))
            ), 
            xo = 10, 
            yo = 10, 
            origin ='upper'
        )

        for phrase in text:
            # Headline Line
            fig.text(
                0.35, 
                y_point, 
                phrase, 
                fontsize=fontsize, 
                va="top", 
                fontweight ="bold"
            )
            fig.canvas.draw()
            y_point -= 0.15

        # Subheading Line
        fig.text(0.35, y_point, subtitle, fontsize=10, va="top", fontweight ="semibold", color="gray")

        fig.canvas.draw()

        output_file = io.BytesIO()
        plt.savefig(output_file, format="PNG")
        plt.close(fig)

        return self.firebase.uploadImgfromCache(f"WallstreetWaves/graphic_{id}.png", output_file)
    
    # Generates a Graph
    def genGraphGraphic(self, id: int, data: list, text: str):
        
        # Variable options
        indicators = ["basicGraphicIndicatorPositive.png", "basicGraphicIndicatorNegative.png"]
        color = [("g", "green"), ("r", "red")]
        current_data = float(data[-1])
        variable_choice  = 0 if (current_data > 0) else 1
        text_breakpoint = 13
        fontsize = 25 if (len(text) > text_breakpoint) else 35
        text = text if (len(text) < text_breakpoint) else f"{text[0:text_breakpoint]}..."
        text_y_pos = 112.5 if (len(text) > text_breakpoint) else 100
        
        # Processes data and scales it accordingly
        data = [float(point) for point in data]

        y_offset = 10
        y_scale = 100
        if any(point < 0 for point in data):
            y_norm_data = [y_offset + (y_scale * ((float(point) - min(data))/(max(data) - min(data)))) for point in data]
        else:
            y_norm_data = [y_offset + (y_scale * (float(point)/max(data))) for point in data]

        x_offset = 10
        x_scale = 400
        x_norm_data = [x_offset + (index * (x_scale/(len(data)-1))) for index in range(len(data))]

        x = np.array(x_norm_data)
        y = np.array(y_norm_data)

        # Load the image
        fig, ax = plt.subplots()
        fig.figimage(
            self.getImage(
                f"https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/{indicators[variable_choice]}"
            ), 
            xo = 530, 
            yo = 30, 
            origin ='upper',
            zorder=1
        )

        # Graphic text
        ax.text(
            20, 
            text_y_pos, 
            f"{text} ({data[-1]}%)", 
            fontsize = fontsize, 
            fontweight ="semibold"
        )

        # Loads background template
        img = self.getImage(
            "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/basicGraphicTemplateActive.png"
        )
        ax.imshow(img)

        # Plots data and initializes settings
        ax.plot(x, y, c=color[variable_choice][0])
        plt.gca().invert_yaxis()
        ax.fill_between(
            x_norm_data, 
            10, 
            y_norm_data, 
            alpha=0.3,
            color=color[variable_choice][1]
        )
        ax.axis('off') 
        plt.tight_layout()
        
        output_file = io.BytesIO()
        plt.savefig(output_file, format="PNG", bbox_inches='tight', transparent=True)

        return self.firebase.uploadImgfromCache(f"WallstreetWaves/graphic_{id}.png", output_file)

    # Generates a basic graphic for comedy videos
    def genComedyGraphic(self, id: int, text: str):
        
        # Initializes image and figure
        fig = plt.figure()
        fig.figimage(
            self.getImage(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/comedyPlaceholderTemplate.png"
            ),
            resize=True
        )

        # Processes text and fontsize parameters
        text = self.processText(23, 6, text)
        fontsize = 48
        y_point = 0.55

        for phrase in text:
            fig.text(
                0.5, 
                y_point, 
                phrase, 
                fontsize=fontsize, 
                va='center', 
                fontweight ="bold",
                horizontalalignment='center',
                verticalalignment='center',
                zorder=1
            )
            fig.canvas.draw()
            y_point -= 0.075

        # Overlay Image
        fig.figimage(
            self.getImage(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/comedyPlaceholderOverlay.png"
            ), 
            xo = 50, 
            yo = 0, 
            origin ='upper',
            zorder=4
        )

        fig.canvas.draw()

        output_file = io.BytesIO()
        plt.savefig(output_file, format="PNG", transparent=True)
        plt.close(fig)

        return self.firebase.uploadImgfromCache(f"Comedy/graphic_{id}.png", output_file)
    
    # Generates a basic graphic for fact videos
    def genFactGraphic(self, id: int, text: str):
        
        # Initializes image and figure
        fig = plt.figure()
        fig.figimage(
            self.getImage(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/factPlaceholderTemplate.png"
            ), 
            resize=True
        )

        # Processes text and fontsize parameters
        text = self.processText(20, 6, text)
        fontsize = 48
        y_point = 0.75

        for phrase in text:
            fig.text(
                0.5, 
                y_point, 
                phrase, 
                fontsize=fontsize, 
                va='center', 
                fontweight ="bold",
                horizontalalignment='center',
                verticalalignment='center',
                zorder=1
            )
            fig.canvas.draw()
            y_point -= 0.12

        fig.canvas.draw()

        output_file = io.BytesIO()
        plt.savefig(output_file, format="PNG", transparent=True)
        plt.close(fig)

        return self.firebase.uploadImgfromCache(f"Fact/graphic_{id}.png", output_file)
    
# Wrapper for all Wallstreet Waves script creation
class WallstreetWavesScript():

    # Vars neccessary for script generation
    def __init__(self):
        self.market_open = False
        self.script = []
        self.firebase = Firebase()
        self.api_data = self.firebase.retrieveAPICache()
        self.graphic = Graphics()
        self.asset_id = 0
        self.categories = [0, 2, 3, 4, 5, 7, 8, 9]
        self.success = False
        self.updatedAt = datetime.now()

    # Retrieves and updates asset_id
    def updateAssetID(self):
        self.asset_id += 1
        return (self.asset_id - 1)

    # Generates intro part of script
    def genIntro(self):
        
        self.script.append(
            Asset(
                self.updateAssetID(),
                "Welcome to Wall Street Waves.",
                None
            )
        )

        return self.script
        
    # Generates wheelspin part of script
    def genWheelSpin(self, intro: str):
        
        category_id = random.choice(self.categories)
        
        possible_categories = [
            "upcoming company earnings",
            "PLACEHOLDER",
            "the U.S. GDP",
            "stock indexs",
            "inflation in the economy",
            "interest rates",
            "PLACEHOLDER",
            "market news. In recent news,",
            "potential mergers. Upcoming mergers include:",
            "consumer spending"
        ]

        self.script.append(
            Asset(
                self.updateAssetID(),
                f"{intro} we will be looking at {possible_categories[category_id]}.",
                None
            )
        )

        self.categories.remove(category_id)

        return category_id
        
    # Generates actual content based on wheelspin part
    def genContent(self, category_id: int):
        
        api_data = self.api_data[category_id]

        match category_id:
            
            case 0:
                data = api_data["UpcomingEarnings"]

                for data_entry in data:
                        
                    name = data_entry["company_name"]

                    if data_entry["company_name"] == None:
                        name = data_entry["symbol"]
                    
                    if data_entry == data[-1]:
                        self.script.append(
                            Asset(
                                self.updateAssetID(),
                                f"And {name} will release earnings in {data_entry['dateFromNow']} days.",
                                self.graphic.genNewsGraphic(
                                    self.asset_id,
                                    "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/defaultNewsIcon.png",
                                    name,
                                    f"Earnings in {data_entry['dateFromNow']} days"
                                )
                            )
                        )
                    else:
                        self.script.append(
                            Asset(
                                self.updateAssetID(),
                                f"{name} will release earnings in {data_entry['dateFromNow']} days.",
                                self.graphic.genNewsGraphic(
                                    self.asset_id,
                                    "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/defaultNewsIcon.png",
                                    name,
                                    f"Earnings in {data_entry['dateFromNow']} days"
                                )
                            )
                        )

            case 2:
                data = [
                    ("The GDP", "is", api_data["Gross domestic product"]["key"], api_data["Gross domestic product"]["value"]), 
                    ("Investments", "are", api_data["Gross private domestic investment"]["key"], api_data["Gross private domestic investment"]["value"]), 
                    ("Consumer Spending", "is", api_data["Personal consumption expenditures"]["key"], api_data["Personal consumption expenditures"]["value"]),
                    ("Government Spending", "is", api_data["Government consumption expenditures and gross investment"]["key"], api_data["Government consumption expenditures and gross investment"]["value"]),
                    ("U.S. Exports", "are", api_data["Exports"]["key"], api_data["Exports"]["value"]),
                    ("U.S. Imports", "are", api_data["Imports"]["key"], api_data["Imports"]["value"])
                ]

                for data_entry in data:
                    if float(data_entry[3][-1]) > 0:
                        adjective = "up"
                    else:
                        adjective = "down"

                    self.script.append(
                        Asset(
                            self.updateAssetID(),
                            f"{data_entry[0]} {data_entry[1]} {adjective} {round(float(data_entry[3][-1]), 2)}% from last quarter.",
                            self.graphic.genGraphGraphic(
                                self.asset_id,
                                data_entry[3],
                                data_entry[0]
                            )
                        )
                    )

            case 3:
                data = [
                    api_data["TotalMarket"][0],
                    api_data["NASDAQ100"][0], 
                    api_data["Russell1000"][0], 
                    api_data["S&P500"][0]
                ]

                for data_entry in data:
                    if data_entry['data']['dp'] > 0:
                        adjective = "up"
                    else:
                        adjective = "down"

                    self.script.append(
                        Asset(
                            self.updateAssetID(),
                            f"The {data_entry['symbol']} index is {adjective} {round(float(data_entry['data']['dp']), 2)}%.",
                            self.graphic.genGraphGraphic(
                                self.asset_id,
                                [0, float(data_entry['data']['dp'])],
                                data_entry['symbol']
                            )
                        )
                    )
                
            case 4:
                data = api_data["Gross domestic product"]["value"]

                if float(data[-1]) > 0:
                    adjective = "up"
                else:
                    adjective = "down"

                self.script.append(
                    Asset(
                        self.updateAssetID(),
                        f"The price of goods is {adjective} {round(float(data[-1]), 2)}%.",
                        self.graphic.genGraphGraphic(
                            self.asset_id,
                            data,
                            "Inflation"
                        )
                    )
                )
                
            case 5:
                data = api_data["AvgInterestRates"]["value"]

                if (float(data[-1]) - float(data[-2])) > 0:
                    adjective = "up"
                else:
                    adjective = "down"

                self.script.append(
                    Asset(
                        self.updateAssetID(),
                        f"The federal funds rate is hovering at {data[-1]}%. This is {adjective} {round(float(data[-1]) - float(data[-2]), 2)}% from last month.",
                        self.graphic.genGraphGraphic(
                            self.asset_id,
                            data,
                            "Interest Rates"
                        )
                    )
                )
                
            case 7:
                data = api_data["MarketNews"]

                for data_entry in data:
                    
                    if data_entry == data[-1]:
                        self.script.append(
                            Asset(
                                self.updateAssetID(),
                                f"And {data_entry['title']}.",
                                self.graphic.genNewsGraphic(
                                    self.asset_id,
                                    data_entry['image'],
                                    data_entry['title'],
                                    data_entry['source']
                                )
                            )
                        )
                    else:
                        self.script.append(
                            Asset(
                                self.updateAssetID(),
                                f"{data_entry['title']}.",
                                self.graphic.genNewsGraphic(
                                    self.asset_id,
                                    data_entry['image'],
                                    data_entry['title'],
                                    data_entry['source']
                                )
                            )
                        )
                                   
            case 8:
                data = api_data["Mergers"]

                for data_entry in data:
                    
                    if data_entry == data[-1]:
                        self.script.append(
                            Asset(
                                self.updateAssetID(),
                                f"And {data_entry['title']}.",
                                self.graphic.genNewsGraphic(
                                    self.asset_id,
                                    data_entry['image'],
                                    data_entry['title'],
                                    data_entry['source']
                                )
                            )
                        )
                    else:
                        self.script.append(
                            Asset(
                                self.updateAssetID(),
                                f"{data_entry['title']}.",
                                self.graphic.genNewsGraphic(
                                    self.asset_id,
                                    data_entry['image'],
                                    data_entry['title'],
                                    data_entry['source']
                                )
                            )
                        )
                
            case 9:
                data = [
                    ("Clothing and footwear", api_data["Clothing and footwear"]["key"], api_data["Clothing and footwear"]["value"]), 
                    ("Food services and accomodations", api_data["Food services and accommodations"]["key"], api_data["Food services and accommodations"]["value"]), 
                    ("Gasoline and other energy goods", api_data["Gasoline and other energy goods"]["key"], api_data["Gasoline and other energy goods"]["value"]),
                    ("Health care", api_data["Health care"]["key"], api_data["Health care"]["value"]),
                    ("Housing and utilities", api_data["Housing and utilities"]["key"], api_data["Housing and utilities"]["value"]),
                    ("Recreation services", api_data["Recreation services"]["key"], api_data["Recreation services"]["value"])
                ]

                for data_entry in data:
                    if float(data_entry[2][-1]) > 0:
                        adjective = "up"
                    else:
                        adjective = "down"

                    self.script.append(
                        Asset(
                            self.updateAssetID(),
                            f"Consumer spending in the category of {data_entry[0]} is {adjective} {round(float(data_entry[2][-1]), 2)}% from last month.",
                            self.graphic.genGraphGraphic(
                                self.asset_id,
                                data_entry[2],
                                data_entry[0]
                            )
                        )
                    )
        
        return self.script

    # Generates content segment based on wheel spin
    def genContentSegment(self, intro: str, testing = (False, 0)):
        
        if testing[0] == False:
            category_id = self.genWheelSpin(intro)
            self.genContent(category_id)
        else:
            self.genContent(testing[1])

        return self.script

    # Generates conclusion part of script
    def genConclusion(self):
        
        self.script.append(
            Asset(
                self.updateAssetID(),
                "Thats been today's Wall Street Wave episode. Thanks for watching and check out the description for more market info.",
                None
            )
        )

        return self.script

    # Retrieves total script
    def retrieveScript(self):
        p_response = []
        
        for phrase in self.script:
            p_response.append(
                phrase.to_dict()
            )

        # Processes title and description
        title_limit = 36
        title = f"{p_response[2]['text'][0:title_limit]}..." if (len(p_response[2]["text"]) > title_limit) else f"{p_response[2]['text']}..."
        description = self.firebase.retrieveYouTubeDescriptionTemplate(
            "This is today's Wall Street Waves Episode which provides a concise summary of the market from credible sources like Finnhub, BEA.gov, and others."
        )

        return {
            "type": "wallstreetwaves",
            "title": title,
            "description": description,
            "script": p_response
        }
    
    # Default video generation
    def createDefaultVideo(self):
        try:
            self.genIntro()
            self.genContentSegment("First, ")
            self.genContentSegment("Next,")
            self.genContentSegment("Lastly,")
            self.genConclusion()
            self.success = True
            self.updatedAt = datetime.now()
            return self.success
        except Exception as error:
            print(f"Error occurred in WallStreetWaves Script Generation which states: {error}")
            self.success = False
            self.updatedAt = datetime.now()
            return self.success
            
# Wrapper for all Comedy script creation
class ComedyScript():
    
    # Vars neccessary for script generation
    def __init__(self):
        self.script = []
        self.firebase = Firebase()
        self.api_data = self.firebase.retrieveAPICache()
        self.graphic = Graphics()
        self.asset_id = 0
        self.success = False
        self.updatedAt = datetime.now()

    # Retrieves and updates asset_id
    def updateAssetID(self):
        self.asset_id += 1
        return (self.asset_id - 1)
    
    # Generates intro part of script
    def genContent(self):
        
        api_data = self.api_data[6]["Jokes"][0]["Joke"]
        
        for joke in api_data:
            self.script.append(
                ComedyAsset(
                    self.updateAssetID(),
                    joke
                )
            )

        return self.script
    
    # Retrieves total script
    def retrieveScript(self):
        p_response = []
        
        for phrase in self.script:
            p_response.append(
                phrase.to_dict()
            )

        # Processes title and description
        title_limit = 36
        title = f"{p_response[0]['text'][0:title_limit]}... #shorts" if (len(p_response[0]["text"]) > title_limit) else f"{p_response[0]['text']}... #shorts"
        description = self.firebase.retrieveYouTubeDescriptionTemplate(
            p_response[0]["text"]  
        )

        return {
            "type": "comedy",
            "title": title,
            "description": description,
            "script": p_response
        }
    
    # Default video generation
    def createDefaultVideo(self):
        try:
            self.genContent()
            self.success = True
            self.updatedAt = datetime.now()
            return self.success
        except Exception as error:
            print(f"Error occurred in Comedy Script Generation which states: {error}")
            self.success = False
            self.updatedAt = datetime.now()
            return self.success
    
# Wrapper for all Fact script creation
class FactScript():
    
    # Vars neccessary for script generation
    def __init__(self):
        self.script = []
        self.firebase = Firebase()
        self.api_data = self.firebase.retrieveAPICache()
        self.graphic = Graphics()
        self.asset_id = 0
        self.success = False
        self.updatedAt = datetime.now()

    # Retrieves and updates asset_id
    def updateAssetID(self):
        self.asset_id += 1
        return (self.asset_id - 1)
    
    # Generates intro part of script (number -> [1 - 4])
    def genContent(self, number: int):
        
        api_data = self.api_data[1]["Facts"]
        
        for index in range(number):
            self.script.append(
                FactAsset(
                    self.updateAssetID(),
                    api_data[index]["Fact"]
                )
            )

        return self.script
    
    # Retrieves total script
    def retrieveScript(self):
        p_response = []
        
        for phrase in self.script:
            p_response.append(
                phrase.to_dict()
            )

        # Processes title and description
        title_limit = 36
        title = f"{p_response[0]['text'][0:title_limit]}... #shorts" if (len(p_response[0]["text"]) > title_limit) else f"{p_response[0]['text']}... #shorts"
        description = self.firebase.retrieveYouTubeDescriptionTemplate(
            p_response[0]["text"]  
        )

        return {
            "type": "fact",
            "title": title,
            "description": description,
            "script": p_response
        }
    
    # Default video generation
    def createDefaultVideo(self):
        try:
            self.genContent(3)
            self.success = True
            self.updatedAt = datetime.now()
            return self.success
        except Exception as error:
            print(f"Error occurred in Fact Script Generation which states: {error}")
            self.success = False
            self.updatedAt = datetime.now()
            return self.success

""" Firebase Functions """

# The Google Cloud Config for this function is 1 vCPU and 512 Mi (mebibyte)
# 6:00 AM UTC -> 2:00 AM EST
# Firebase function to generate scripts based on templates and API data
@scheduler_fn.on_schedule(schedule="every day 06:00")
def updateScriptsDaily(event: scheduler_fn.ScheduledEvent) -> None:
     
    # Retrieves Firebase functions
    firebase = Firebase()
    
    # Retrieves WallstreetWaves Script
    video1 = WallstreetWavesScript()
    if (video1.createDefaultVideo()):
        firebase.addData(
            "wallstreetwaves",
            video1.retrieveScript()
        )

    # Retrieves Comedy Script
    video2 = ComedyScript()
    if (video2.createDefaultVideo()):
        firebase.addData(
            "comedy",
            video2.retrieveScript()
        )

    # Retrieves Fact Script
    video3 = FactScript()
    if (video3.createDefaultVideo()):
        firebase.addData(
            "fact",
            video3.retrieveScript()
        )

    # Updates Status
    firebase.updateStatus("social", {
        "AssetGeneration": {
            "wallstreetwaves": {
                "success": video1.success,
                "updated": video1.updatedAt
            },
            "comedy": {
                "success": video2.success,
                "updated": video2.updatedAt
            },
            "fact": {
                "success": video3.success,
                "updated": video3.updatedAt
            }
        }
    })

    return https_fn.Response("Success")
