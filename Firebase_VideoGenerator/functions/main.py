
""" Required Dependencies """
import firebase_admin
from firebase_admin import firestore
from firebase_admin import storage
from firebase_admin import credentials
from firebase_functions import https_fn
from firebase_functions import scheduler_fn
from moviepy.editor import *
import io
from PIL import Image
import requests
import matplotlib.pyplot as plt
import numpy as np
import tempfile
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime
import pandas as pd

""" Program Defaults """
# Stores program info such as Name, Date Created, Date Edited, Ect.
class Program():
    
    def __init__(self):
        self.name = "VideoGenerator"
        self.date_created = "08/08/24"
        self.date_edited = "08/08/24"  

""" Helper Functions """

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

# Firebase wrapper for database editing
class Firebase():
    
    # Vars necessary for interacting with Firebase Database
    def __init__(self):
    
    # Retrieves a json file from storage url
    def retrieveJSONFile(self, url: str):
        response = requests.get(url)
        return response.json()
    
    # Updates YouTube Token with new info
    def updateYouTubeToken(self, json_data: str):
        
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            bucket = storage.bucket(name="itsnousv3.appspot.com")
            blob = bucket.blob(f"Credentials/token_youtube_v3.json")

            blob.upload_from_string(json_data, content_type='application/json')
            blob.make_public()
            return blob.public_url

    # Retrieves cache of scripts
    def retrieveScripts(self):
        
        scripts_cache = []
        
        try:
            firebase_admin.get_app()
        except:
            firebase_admin.initialize_app(self.creds)
        finally:
            db = firestore.client()
            docs = (
                db.collection("scripts").stream()
            )

            for doc in docs:

              scripts_cache.append(doc.to_dict())
        
        return scripts_cache
    
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

# Neccessary functions to intereact with YouTube Data API V3
class YouTubeVideo():
    """ 
    Source: https://learndataanalysis.org/source-code-automate-video-upload-to-youtube-with-python-and-youtube-api/
    """

    # Vars neccessary for YouTube Data API V3
    def __init__(self, title: str, description: str):
        self.credentials = "Credentials/client_NousSocialAIV1.json"
        self.api_name = "youtube"
        self.version = "v3"
        self.scopes = [
            'https://www.googleapis.com/auth/youtube',
            'https://www.googleapis.com/auth/youtube.channel-memberships.creator',
            'https://www.googleapis.com/auth/youtube.force-ssl',
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtubepartner',
            'https://www.googleapis.com/auth/youtubepartner-channel-audit'
        ]

        # Retrieves functions for working with Firebase
        self.firebase = Firebase()

        # Initiates service
        self.service = None
        self.getService()

        # Video upload defaults
        self.title = title
        self.description = description
        self.upload_time = datetime.now().isoformat() + '.000Z'
        self.max_retries = 10
        self.status = {}

    # Function to interface with YouTube API
    def createService(self, api_name, api_version, *scopes, prefix=''):
        
        """ 
        Source: https://learndataanalysis.org/google-py-file-source-code/
        """

        API_SERVICE_NAME = api_name
        API_VERSION = api_version
        SCOPES = [scope for scope in scopes[0]]
        firebase = Firebase()
        creds = None

        creds = Credentials.from_authorized_user_info(
            info=firebase.retrieveJSONFile("https://storage.googleapis.com/itsnousv3.appspot.com/Credentials/token_youtube_v3.json"),
            scopes=SCOPES
        )

        creds.refresh(Request())
        self.firebase.updateYouTubeToken(creds.to_json())

        try:
            service = build(API_SERVICE_NAME, API_VERSION, credentials=creds, static_discovery=False)
            print(API_SERVICE_NAME, API_VERSION, 'service created successfully')
            return service
        except Exception as e:
            print(e)
            print(f'Failed to create service instance for {API_SERVICE_NAME}')
            return None

    # Gets service via helper function
    def getService(self):
        self.service = self.createService(
            self.api_name, 
            self.version, 
            self.scopes
        )

    # Retrieve possible list of categories for YouTube video (Quota Cost: 1 unit)
    def getCategories(self):
        video_categories = self.service.videoCategories().list(part='snippet', regionCode='US').execute()
        df = pd.DataFrame(video_categories.get('items'))
        return pd.concat([df['id'], df['snippet'].apply(pd.Series)[['title']]], axis=1)
    
    # Uploads video with private status to YouTube (Quota Cost: 1600 units)
    @detectFault
    def uploadVideo(self, video_file: str, tags: list, category_id: str):
        
        video_metadata = {
            'snippet': {
                'title': self.title,
                'description': self.description,
                'categoryId': category_id,
                'tags': tags
            },
            'status': {
                'privacyStatus': 'public',
                'publishedAt': self.upload_time,
                'selfDeclaredMadeForKids': False
            },
            'notifySubscribers': False
        }
        
        media_file = MediaFileUpload(video_file)

        try:
            response_video_upload = self.service.videos().insert(
                part='snippet,status',
                body=video_metadata,
                media_body=media_file
            ).execute()

            self.status["uploaded"] = {
                "success": True,
                "updated": datetime.now(),
                "video_id": response_video_upload.get("id")
            }

            return self.status

        except Exception as error:
            
            print(f"YouTube video upload failed with this error: {error}")
            
            self.status["uploaded"] = {
                "success": False,
                "updated": datetime.now()
            }
            
            return self.status
    
    # Sets thumbnail for video (Quota Cost: 50 units)
    @detectFault
    def setThumbnail(self, thumbnail: str):
        
        try:
            response_thumbnail_upload = self.service.thumbnails().set(
                videoId=self.status["uploaded"]["video_id"],
                media_body=MediaFileUpload(thumbnail)
            ).execute()

            self.status["thumbnail"] = {
                "success": True,
                "thumbnail": response_thumbnail_upload.get("items")[0]["medium"]["url"],
                "updated": datetime.now()
            }

            return self.status
        
        except Exception as error:
            
            print(f"YouTube failed to set thumbnail for video with this error: {error}")
            
            self.status["thumbnail"] = {
                "success": False,
                "updated": datetime.now()
            }
            
            return self.status

    # Adds default thumbnail
    @detectFault
    def addThumbnail(self, thumbnail_url: str):
          
        self.status["thumbnail"] = {
            "success": True,
            "thumbnail": thumbnail_url,
            "updated": datetime.now()
        }

        return self.status
    
    # Adds to YouTube playlist (Quota Cost: 50 units)
    @detectFault
    def addPlaylist(self, playlist_id: str):
        
        playlist_metadata = {
            "contentDetails": {
                "videoId": self.status["uploaded"]["video_id"]
            },
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    "kind": "youtube#video",
                    "videoId": self.status["uploaded"]["video_id"],
                }
            }
        }
        
        try:
            response_playlist_upload = self.service.playlistItems().insert(
                part='snippet, contentDetails',
                body=playlist_metadata
            ).execute()

            self.status["playlist"] = {
                "success": True,
                "updated": datetime.now()
            }

            return self.status
        
        except Exception as error:
            
            print(f"YouTube failed to add video to playlist with this error: {error}")
            
            self.status["playlist"] = {
                "success": False,
                "updated": datetime.now()
            }
            
            return self.status

    # Retrieves number of videos in a playlist (Quota Cost: 1 unit)
    @detectFault
    def retrievePlaylist(self, playlist_id: str):
        
        # Retrieve playlist items
        results = self.service.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50  
        ).execute()

        return results["pageInfo"]["totalResults"]
    
    # Retrieves status of youtube video upload
    @detectFault
    def updateStatus(self):
        
        if (self.status["uploaded"]["success"]):
            self.firebase.updateStatus(
                "social",
                {
                    self.status["uploaded"]["video_id"]: {
                        "video_status": self.status,
                        "updated": datetime.now()
                    }
                }
            )

        return self.status

# Wrapper to generate basic graphics
class Graphics():
    
    def __init__(self):
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

    # Retrieves audio file
    def retrieveAudio(self, audio_url: str):

        audio = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) 

        r = requests.get(audio_url, stream=True)
        if r.status_code == 200:
            for chunk in r:
                audio.write(chunk)
                
        return audio

    # Retrieves video file
    def retrieveVideo(self, video_url: str):

        video = tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        ) 

        r = requests.get(video_url, stream=True)
        if r.status_code == 200:
            for chunk in r:
                video.write(chunk)
                
        return video

    # Generates thumbnail for Wallstreet Waves
    def genWallStreetWavesThumbnail(self, ep_number: int):
        # Creates figure and retrieves background template
        fig = plt.figure()
        fig.figimage(
            self.getImage(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/wallStreetWavesThumbnailTemplate.png"
            ), 
            resize=True
        )

        # Determines font size for figure text
        fontsize = 130 if (ep_number >= 100) else 180

        # Places overlay image
        """
        Src: https://matplotlib.org/3.3.0/api/_as_gen/matplotlib.pyplot.text.html
        """
        fig.text(
            0.975, 
            0.15, 
            f"#{ep_number}", 
            fontsize=fontsize, 
            va='center', 
            fontweight ="black",
            horizontalalignment='right',
            verticalalignment='center',
            zorder=1,
            color="white"
        )

        fig.canvas.draw()

        output_file = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) 
        plt.savefig(
            output_file, 
            format="PNG"
        )
        return output_file 
    
    # Generates Wallstreet Waves frame
    def genWallStreetWavesFrame(self, background, overlay_url: str, y_offset: int):
        
        # Creates figure and retrieves background template
        fig = plt.figure()
        fig.figimage(
            background, 
            resize=True
        )

        # Places overlay image
        fig.figimage(
            self.getImage(
                overlay_url,
                (True, (420, 150))
            ), 
            xo = 838, 
            yo = y_offset, 
            origin ='upper'
        )

        fig.canvas.draw()

        output_file = io.BytesIO()
        plt.savefig(output_file, format="PNG")

        return np.array(Image.open(output_file))
    
    # Generates transition for Wallstreet Waves
    def genTransition(self, line: dict):
        """
        Src: https://www.geeksforgeeks.org/python-test-if-string-contains-element-from-list/
        """

        # Stores return objects
        frames = []
        audio_temp_files = []
        video_temp_files = []

        # Assist function to see if phrase is in sentence
        contains_word = lambda s, l: any(map(lambda x: x in s, l))

        # Current possible list of categories
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

        # Transition video files
        video_files = [
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/company_earnings_wheel_spin.mp4",
          "PLACEHOLDER",
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/gdp_wheel_spin.mp4",
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/stock_indexes_wheel_spin.mp4",
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/inflation_wheel_spin.mp4",
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/interest_rates_wheel_spin.mp4",
          "PLACEHOLDER",
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/market_news_wheel_spin.mp4",
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/mergers_wheel_spin.mp4",
          "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/consumer_spending_wheel_spin.mp4"
        ]
        
        cursor = 0
        for category in possible_categories:
            if contains_word(line["text"], [category]):
                break
            else:
                cursor += 1

        video = self.retrieveVideo(
            video_files[cursor]
        )
        video_temp_files.append(
            video
        )
        
        audio = self.retrieveAudio(
            line["audio"]
        )
        audio_temp_files.append(
            audio
        )
            
        frames.append(
            VideoFileClip(
                video.name
            ).set_audio(
                AudioFileClip(
                    audio.name
                )
            )
        )

        return frames, audio_temp_files, video_temp_files

    # Generates content segment for Wallstreet Waves
    def genContentSegment(self, script: list):

        # Frames storage
        frames = []
        audio_temp_files = []
        
        # Creates figure and retrieves background template
        background = self.getImage(
            "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/wallStreetWavesBackgroundTemplate.png"
        )
        
        y_start = 560
        increment = 180
        for line in script:
            
            if (y_start >= 0):
                # Saves last edited image in storage
                background = self.genWallStreetWavesFrame(
                    background,
                    line["graphic"],
                    y_start
                )
            else:
                # Resets to prevent overflow
                y_start = 560
                background = self.genWallStreetWavesFrame(
                    self.getImage(
                        "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/wallStreetWavesBackgroundTemplate.png"
                    ),
                    line["graphic"],
                    y_start
                )

            audio = self.retrieveAudio(
                line["audio"]
            )
            audio_temp_files.append(
                audio
            )
            audio_object = AudioFileClip(
                audio.name
            )
            frames.append(
                ImageClip(
                    background
                ).set_audio(
                    audio_object
                ).set_duration(audio_object.duration)
            )       

            y_start -= increment

        return frames, audio_temp_files
        
    # Generates a comedy frame
    def genComedyFrame(self, line: dict):
        
        # Creates figure and retrieves background template
        fig = plt.figure()
        fig.figimage(
            self.getImage(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/comedyBackgroundTemplate.png"
            ), 
            resize=True
        )

        # Places overlay image
        fig.figimage(
            self.getImage(
                line["graphic"]
            ), 
            xo = 67, 
            yo = 950, 
            origin ='upper'
        )

        fig.canvas.draw()

        output_file = io.BytesIO()
        plt.savefig(output_file, format="PNG")

        # Sets neccessary variables
        image = np.array(Image.open(output_file))
        audio = self.retrieveAudio(line["audio"])
        audio_object = AudioFileClip(audio.name)

        # Creates image clip given audio
        return_object = ImageClip(
            image
        ).set_audio(
            audio_object
        ).set_duration(
            audio_object.duration
        )

        return return_object, audio
    
    # Generates a fact frame
    def genFactFrame(self, line: str):
        
        # Creates figure and retrieves background template
        fig = plt.figure()
        fig.figimage(
            self.getImage(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/factBackgroundTemplate.png"
            ), 
            resize=True
        )

        # Places overlay image
        fig.figimage(
            self.getImage(
                line["graphic"]
            ), 
            xo = 67, 
            yo = 920, 
            origin ='upper'
        )

        fig.canvas.draw()

        output_file = io.BytesIO()
        plt.savefig(output_file, format="PNG")

        # Sets neccessary variables
        image = np.array(Image.open(output_file))
        audio = self.retrieveAudio(line["audio"])
        audio_object = AudioFileClip(audio.name)

        # Creates image clip given audio
        return_object = ImageClip(
            image
        ).set_audio(
            audio_object
        ).set_duration(
            audio_object.duration
        )

        return return_object, audio

""" Main Video Generation """

# Wrapper for all video generation
class VideoGenerator():
    
    # Vars neccessary for generating video
    def __init__(self):
        self.firebase = Firebase()
        self.scripts = self.firebase.retrieveScripts()
        self.graphics = Graphics()

    # Retrieves title and description
    def retrieveVidInfo(self, id: int):
        script = self.scripts[id]
        return {
            "title": script["title"],
            "description": script["description"]
        }

    # Generates comedy video
    def genComedyVid(self):
        script = self.scripts[0]["script"]
        frames = []
        audio_temp_files = []

        for line in script:
            
            # Frame and Audio
            frame, audio = self.graphics.genComedyFrame(
                line
            )
            
            frames.append(frame)
            audio_temp_files.append(audio)

        video = concatenate_videoclips(
            frames
        )

        output_file = tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        ) 
        video.write_videofile(
            output_file.name, 
            codec="libx264", 
            preset="ultrafast",
            fps=24
        )

        for audio_clip in audio_temp_files:
            audio_clip.close()
            os.unlink(audio_clip.name)

        for clip in frames:
            clip.close()

        return output_file
        
    # Generates fact video
    def genFactVid(self):
        script = self.scripts[1]["script"]
        frames = []
        audio_temp_files = []

        for line in script:
            
            # Frame and Audio
            frame, audio = self.graphics.genFactFrame(
                line
            )
            
            frames.append(frame)
            audio_temp_files.append(audio)

        video = concatenate_videoclips(
            frames
        )

        output_file = tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        ) 
        video.write_videofile(
            output_file.name, 
            codec="libx264", 
            preset="ultrafast",
            fps=24
        )

        for audio_clip in audio_temp_files:
            audio_clip.close()
            os.unlink(audio_clip.name)

        for clip in frames:
            clip.close()

        return output_file    

    # Generates wallstreet waves video
    def genWallstreetWavesVid(self):
        script = self.scripts[2]["script"]
        frames = []
        audio_temp_files = []
        video_temp_files = []

        # Cuts intro and adds frames
        intro = script[0]
        intro_audio = self.graphics.retrieveAudio(
            intro["audio"]
        )
        intro_video = self.graphics.retrieveVideo(
            "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/wallStreetWavesIntroSequence.mp4"
        )
        audio_temp_files.append(
            intro_audio
        )
        video_temp_files.append(
            intro_video
        )
        frames.append(
            VideoFileClip(
                intro_video.name
            ).set_audio(
                AudioFileClip(
                    intro_audio.name   
                )
            )
        )
        script.remove(intro)

        # Cuts conclusion
        conclusion = script[-1]
        script.remove(conclusion)
        
        # Splits up content into segments
        cursor = -1
        cached_content = []
        for line in script:
            if line["graphic"] == None:

                if (cursor >= 0):
                    # Processes previous segment
                    r_frames, r_audio_temp_files = self.graphics.genContentSegment(cached_content[cursor])
                    frames += r_frames
                    audio_temp_files += r_audio_temp_files

                # Prepares transition to next segment
                r_frames, r_audio_temp_files, r_video_temp_files = self.graphics.genTransition(line)
                frames += r_frames
                audio_temp_files += r_audio_temp_files
                video_temp_files += r_video_temp_files
                
                # Prepares next segment
                cursor += 1
                cached_content.insert(cursor, [])

            else:
                cached_content[cursor] += [line]
        
        # Generates last segment
        r_frames, r_audio_temp_files = self.graphics.genContentSegment(cached_content[-1])
        frames += r_frames
        audio_temp_files += r_audio_temp_files

        # Adds conclusion frame
        conclusion_audio = self.graphics.retrieveAudio(
            conclusion["audio"]
        )
        audio_temp_files.append(
            conclusion_audio
        )
        conclusion_audio_object = AudioFileClip(
            conclusion_audio.name
        )
        frames.append(
            ImageClip(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/Videos/wallStreetWavesEndingTemplate.png"
            ).set_audio(
                conclusion_audio_object
            ).set_duration(conclusion_audio_object.duration)
        )

        video = concatenate_videoclips(
            frames
        )

        output_file = tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        ) 
        video.write_videofile(
            output_file.name, 
            codec="libx264", 
            preset="ultrafast",
            fps=24
        )

        for audio_clip in audio_temp_files:
            audio_clip.close()
            os.unlink(audio_clip.name)

        # for video_clip in video_temp_files:
        #     # video_clip.close()
        #     os.unlink(video_clip.name)

        for clip in frames:
            clip.close()

        return output_file

# Function to upload videos after generation
class YouTubeUploader():
    
    def __init__(self):
        self.vidGen = VideoGenerator()
        self.graphics = Graphics()

    @detectFault
    def createComedyVid(self):
        
        # Initializes YouTube Video
        vid_info = self.vidGen.retrieveVidInfo(0)
        vid = YouTubeVideo(
            vid_info["title"],
            vid_info["description"]
        )

        # Generates vid and uploads video
        vid_file = self.vidGen.genComedyVid()
        vid.uploadVideo(
            video_file=vid_file.name,
            tags=["comedy", "funny", "shorts", "jokes"],
            category_id="24"
        )

        # Adds default thumbnail
        vid.addThumbnail(
            "https://storage.googleapis.com/itsnousv3.appspot.com/YouTubeDefaults/comedyBackgroundThumbnail.png"
        )

        # Adds vid to playlist and cleans up temp files
        vid.addPlaylist("PLizmHl7t7otfGrDlRY195hn0aslP8jiPS")
        vid_file.close()
        os.unlink(vid_file.name)

        # Updates status
        return vid.updateStatus()
    
    @detectFault
    def createFactVid(self):
        
        # Initializes YouTube Video
        vid_info = self.vidGen.retrieveVidInfo(1)
        vid = YouTubeVideo(
            vid_info["title"],
            vid_info["description"]
        )

        # Generates vid and uploads video
        vid_file = self.vidGen.genFactVid()
        vid.uploadVideo(
            video_file=vid_file.name,
            tags=["facts", "learn", "shorts", "knowledge", "interesting", "cool"],
            category_id="27"
        )

        # Adds default thumbnail
        vid.addThumbnail(
            "https://storage.googleapis.com/itsnousv3.appspot.com/YouTubeDefaults/factBackgroundThumbnail.png"
        )

        # Adds vid to playlist and cleans up temp files
        vid.addPlaylist("PLizmHl7t7otebrMZtCzxbnqG5krTysXRU")
        vid_file.close()
        os.unlink(vid_file.name)

        # Updates status
        return vid.updateStatus()
    
    @detectFault
    def createWallstreetWavesVid(self):
        
        # Initializes YouTube Video
        vid_info = self.vidGen.retrieveVidInfo(2)
        vid = YouTubeVideo(
            f"{vid_info['title']}",
            vid_info["description"]
        )
        episode_number = vid.retrievePlaylist("PLizmHl7t7otdmEFw5RMV4tXdGNWklNk1d")+1
        vid.title = f"{vid_info['title']} (Episode #{episode_number})"

        # Generates vid and uploads video
        vid_file = self.vidGen.genWallstreetWavesVid()
        vid.uploadVideo(
            video_file=vid_file.name,
            tags=["finance", "news", "wallstreetwaves", "overview", "daily"],
            category_id="25"
        )

        # Creates and sets thumbnail
        thumbnail = self.graphics.genWallStreetWavesThumbnail(
            episode_number
        )
        vid.setThumbnail(thumbnail.name)
        thumbnail.close()
        os.unlink(thumbnail.name)

        # Adds default thumbnail
        vid.addThumbnail(
            "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/wallStreetWavesThumbnailTemplate.png"
        )

        # Adds vid to playlist and cleans up temp files
        vid.addPlaylist("PLizmHl7t7otdmEFw5RMV4tXdGNWklNk1d")
        vid_file.close()
        os.unlink(vid_file.name)

        # Updates status
        return vid.updateStatus()
    
""" Firebase Functions """

# The Google Cloud Config for this function is 2 vCPU and 2 Gi (gibibyte)
# The timeout is also custom at 360 seconds.
# 7:00 AM UTC -> 3:00 AM EST
# Firebase function which generates and uploads videos to YouTube daily
@scheduler_fn.on_schedule(schedule="every day 07:00")
def uploadVideosDaily(event: scheduler_fn.ScheduledEvent) -> None:

    # Retrieves YouTubeUploader functions
    youtubeUpload = YouTubeUploader()

    # Creates and uploads video 1
    youtubeUpload.createComedyVid()

    # Creates and uploads video 2
    youtubeUpload.createFactVid()   

    # Creates and uploads video 3
    youtubeUpload.createWallstreetWavesVid()
    
    return https_fn.Response("Success")