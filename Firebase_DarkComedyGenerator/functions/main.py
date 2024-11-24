
""" Required Dependencies """

# Dependencies for 'animate.py' to function
from PIL import Image

# Dependencies for 'assist.py' to function
import cv2
from mutagen.mp3 import MP3
from moviepy.editor import *
import random
import requests
import os
from datetime import datetime
import numpy as np
import tempfile
import math

# Dependencies for 'library.py' to function
import time

# Dependencies for 'character.py' to function
from PIL import ImageFont, ImageDraw

# Dependencies for 'cloud_functions.py' to function
from google.cloud import storage
import io

# Dependencies for AWS
from boto3 import Session
from contextlib import closing

# Dependencies for firebase
import firebase_admin
from firebase_admin import firestore
from firebase_admin import storage as firebase_storage
from firebase_admin import credentials
from firebase_functions import https_fn
from firebase_functions import scheduler_fn

# Install libraries below using pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
import pandas as pd
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

""" Helper Functions """

def debug(statement: str):
    if True:
        print(statement)

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
            bucket = firebase_storage.bucket(name="itsnousv3.appspot.com")
            blob = bucket.blob(f"Credentials/token_youtube_v3.json")

            blob.upload_from_string(json_data, content_type='application/json')
            blob.make_public()
            return blob.public_url

    # Retrieves default youtube description
    def retrieveYouTubeDescriptionTemplate(self, line: str):    
        response = requests.get("https://storage.googleapis.com/itsnousv3.appspot.com/YouTubeDefaults/YouTubeDefaultDescription.json")
        return response.text.replace("[PLACEHOLDER]", line)

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

class AWS():
    
    # Vars neccessary for interacting with Amazon Polly
    def __init__(self):
        self.session = Session(
            aws_access_key_id="[Redacted]",
            aws_secret_access_key="[Redacted]"
        )
        self.polly_client = self.session.client(
            "polly",
            region_name='us-west-2'
        )
        self.firebase = Firebase()

    # Generates speech
    def genSpeech(self, text: str):
        response = self.polly_client.synthesize_speech(
            Text=text, 
            OutputFormat="mp3",
            VoiceId="Matthew",
            Engine="neural"
        )

        audio = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )

        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                try:
                    audio.write(stream.read())
                    return audio
                except IOError as error:
                     debug(error)
                     return None
        else:
            print("Nothing")
            return None
        
    def get_text_audio(self, text: str):
        # Cloud credentials

        list_of_words = text.split(" ")
        # debug("text_audio")
        generated_audio = self.genSpeech(text)
        try:
            debug(generated_audio.name)
            audio_file = MP3(generated_audio.name)
            audio_length = audio_file.info.length
        except:
            audio_length = 1
        finally:
            duration_words = []
            for i in range(len(list_of_words)):
                duration_words.append(math.trunc(audio_length)/len(list_of_words))

            if ((len(list_of_words) % 2) == 1):
                list_of_words.append("")
                duration_words.append(0.1)
            
            debug("Joke recieved and processed.")
        return list_of_words, duration_words, generated_audio

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
            debug(e)
            debug(f'Failed to create service instance for {API_SERVICE_NAME}')
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
            
            debug(f"YouTube video upload failed with this error: {error}")
            
            self.status["uploaded"] = {
                "success": False,
                "updated": datetime.now()
            }
            
            return self.status
    
    # Sets thumbnail for video (Quota Cost: 50 units)
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
            
            debug(f"YouTube failed to set thumbnail for video with this error: {error}")
            
            self.status["thumbnail"] = {
                "success": False,
                "updated": datetime.now()
            }
            
            return self.status

    # Adds default thumbnail
    def addThumbnail(self, thumbnail_url: str):
          
        self.status["thumbnail"] = {
            "success": True,
            "thumbnail": thumbnail_url,
            "updated": datetime.now()
        }

        return self.status
    
    # Adds to YouTube playlist (Quota Cost: 50 units)
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
            
            debug(f"YouTube failed to add video to playlist with this error: {error}")
            
            self.status["playlist"] = {
                "success": False,
                "updated": datetime.now()
            }
            
            return self.status

    # Retrieves number of videos in a playlist (Quota Cost: 1 unit)
    def retrievePlaylist(self, playlist_id: str):
        
        # Retrieve playlist items
        results = self.service.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50  
        ).execute()

        return results["pageInfo"]["totalResults"]
    
    # Retrieves status of youtube video upload
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

class GoogleCloud():
    
    def __init__(self):
      self.bucket_name = "itsnousv3.appspot.com"
      self.directory_offset = "GraphicsTemplates/T2DecComedyAssets/"

    # Deletes file from google cloud storage bucket
    def delete_file(self, destination_blob_name):
        # Initialize the Google Cloud Storage client with the credentials
        storage_client = storage.Client.from_service_account_info(self.credentials)
        # Get the target bucket
        bucket = storage_client.bucket(self.bucket_name)
        blob = bucket.blob(f"{self.directory_offset}{destination_blob_name}")
        # Deletes blob
        generation_match_precondition = None
        blob.reload()  # Fetch blob metadata to use in generation_match_precondition.
        generation_match_precondition = blob.generation
        blob.delete(if_generation_match=generation_match_precondition)
        # Returns True if file is deleted
        return True

    # Uploads file with content to google cloud storage bucket
    def create_file(self, content, destination_blob_name):
        # Initialize the Google Cloud Storage client with the credentials
        storage_client = storage.Client.from_service_account_info(self.credentials)
        # Get the target bucket
        bucket = storage_client.bucket(self.bucket_name)
        # Upload the file to the bucket
        file_uploaded = False
        start_wait_time = 0
        while not file_uploaded:
            try:
                blob = bucket.blob(f"{self.directory_offset}{destination_blob_name}")
                with blob.open("wb") as f:
                    f.write(content)
                file_uploaded = True
            except:
                file_uploaded = False
                start_wait_time += 0.5
                time.sleep(start_wait_time)
            
        debug(f"File {destination_blob_name} uploaded to gs://{self.bucket_name}/{self.directory_offset}{destination_blob_name}")
        return destination_blob_name

    # Reads file content from google cloud storage bucket
    def read_file(self, destination_blob_name):
        # Initialize the Google Cloud Storage client with the credentials
        storage_client = storage.Client.from_service_account_info(self.credentials)
        # Get the target bucket
        bucket = storage_client.bucket(self.bucket_name)
        # Read file from the bucket
        file_read = False
        start_wait_time = 0
        while not file_read:
            try:
                blob = bucket.blob(f"{self.directory_offset}{destination_blob_name}")
                with blob.open("rb") as f:
                    answer = f.read()
                file_read = True
                debug(f"File {destination_blob_name} read from gs://{self.bucket_name}/{self.directory_offset}{destination_blob_name}")
            except Exception as error:
                debug(error)
                file_read = False
                start_wait_time += 0.5
                time.sleep(start_wait_time)
        return answer

    # Empty's frame folder to prevent overwriting problems
    def empty_cache(self, folder):
        # Initialize the Google Cloud Storage client with the credentials
        storage_client = storage.Client.from_service_account_info(self.credentials)
        # Get the target bucket
        bucket = storage_client.bucket(self.bucket_name)
        blobs = list(bucket.list_blobs(prefix=f'{self.directory_offset}{folder}/'))
        for blob in blobs:
            generation_match_precondition = None
            blob.reload()  # Fetch blob metadata to use in generation_match_precondition.
            generation_match_precondition = blob.generation
            blob.delete(if_generation_match=generation_match_precondition)
        return True

    # Reads frame folder to prevent overwriting problems
    def get_all_frames(self, folder):
        # Initialize the Google Cloud Storage client with the credentials
        storage_client = storage.Client.from_service_account_info(self.credentials)
        # Get the target bucket
        bucket = storage_client.bucket(self.bucket_name)
        return_list = []
        blobs = list(bucket.list_blobs(prefix=f'{self.directory_offset}{folder}/'))
        for blob in blobs:
            return_list += [blob.name]
        return return_list

    def save_image(self, object, filename):
        image_file = io.BytesIO()
        object.save(image_file, format='PNG')
        return self.create_file(self.bucket_name, image_file.getvalue(), filename, self.credentials)

class ImageHelper():
    
    def __init__(self, image_repository):
        self.googlecloud = GoogleCloud()
        self.image_repository = image_repository

    # Overlays image on backdrop
    def overlay(self, base, overlay_list, coords):
        current_base = base.copy()
        byteIO = io.BytesIO()
        for counter in range(len(overlay_list)):
            current_base.paste(overlay_list[counter], coords[counter], mask=overlay_list[counter])
        current_base.save(byteIO, format='PNG')
        # current_base.save(result, quality=95)
        return Image.open(byteIO).convert("RGBA")

    # Scales image given a certain factor
    def scale(self, image, factor):
        width, height = image.size
        resized_img = image.resize((int(width*factor), int(height*factor)))
        return resized_img

    # Gets image based on code_id
    def get_image(self, id, factor):
        # Scales image appropriately
        if factor != 1.0:
            return self.scale(
                Image.open(self.image_repository[id]).convert("RGBA"), 
                factor
            )
        else:
            return Image.open(self.image_repository[id]).convert("RGBA")

class VideoHelper():

    def __init__(self):
        self.googlecloud = GoogleCloud()
        
    def concatenate_audio_moviepy(self, audio_clip_paths):
        
        # Concatenates several audio files into one audio file using MoviePy and save it to `output_path`. Note that extension (mp3, etc.) must be added to `output_path`
        final_clip = concatenate_audioclips(audio_clip_paths)

        return final_clip

    # Combines image files into video (format: .mp4) (duration: (s))
    def render_video(self, frames, width, height, duration, audio_files):
        
        time_btwn_frames = len(frames)/duration
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')

        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        video = cv2.VideoWriter(temp.name, fourcc, time_btwn_frames, (width, height))

        for frame in frames:
            img_bytes = io.BytesIO()
            frame.save(img_bytes, format='PNG')
            img = cv2.imdecode(np.frombuffer(img_bytes.getvalue(), np.uint8), 1)
            video.write(img)

        video.release()

        processed_audio_files = []
        for file in audio_files:
            desired_length = file[1][1] - file[1][0]    
            try:
                processed_audio_files += [AudioFileClip(file[0].name).subclip(0, desired_length)]
            except:
                processed_audio_files += [AudioFileClip(file[0].name)]                                                       

        final_video = VideoFileClip(temp.name)
        final_audio = self.concatenate_audio_moviepy(processed_audio_files)

        debug("Rendering raw video.")
        output_video_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        final_video.set_audio(final_audio).write_videofile(
            output_video_file.name,
            codec="libx264", 
            preset="ultrafast",
            fps=30
        )

        try:
            for file in audio_files:
                file[0].close()
                os.unlink(file[0].name)
            temp.close()
            os.unlink(temp.name)
        except Exception as error:
            print(error)

        return output_video_file

class JokeAPI():
    
    def __init__(self):
        self.base_url = "https://v2.jokeapi.dev/joke/"

    def getJoke(self):

        success = False

        while (not success):
            r = requests.get(f'{self.base_url}Programming,Miscellaneous,Dark,Pun,Spooky,Christmas?amount=1&blacklistFlags=racist')
            processed_content = r.json()
            return_element = []
            if (processed_content["type"] == "twopart"):
                return_element += [True]
                return_element += [processed_content["setup"]]
                if len(processed_content["delivery"].split(" ")) > 2:
                    return_element += [processed_content["delivery"]]
                    success = True
            else:
                return_element += [False]
                return_element += [processed_content["joke"]]
        
        debug(return_element)
        return return_element

class Character():
    
    def __init__(self, image_repository):
        self.image_repository = image_repository
        self.imagehelper = ImageHelper(self.image_repository)

    def get_rand_angle(self, lower_bound, upper_bound):
        return random.randint(lower_bound, upper_bound)

    def get_character(self, left_arm_angles, right_arm_angles, leg_angles, face_image):

        backdrop = self.imagehelper.get_image("character_container", 0.8)

        character_face = self.imagehelper.get_image(face_image, 0.8)
        character_body = self.imagehelper.get_image("character_structure", 0.8)

        character_limb_left_arm_upper = self.imagehelper.get_image("character_limb", 0.8).rotate(left_arm_angles[0], expand=1) # angle limit : 15 < theta < 75 
        character_limb_left_arm_lower = self.imagehelper.get_image("character_limb", 0.8).rotate(-left_arm_angles[1], expand=1) # angle limit : -75 < theta < -15 
        character_limb_right_arm_upper = self.imagehelper.get_image("character_limb", 0.8).rotate(-right_arm_angles[0], expand=1) # angle limit : -75 < theta < -15  
        character_limb_right_arm_lower = self.imagehelper.get_image("character_limb", 0.8).rotate(right_arm_angles[1], expand=1) # angle limit : 15 < theta < 75

        character_limb_left_leg_upper = self.imagehelper.get_image("character_limb", 0.8).rotate(leg_angles[0], expand=1) # angle limit : 15 < theta < 75
        character_limb_left_leg_lower = self.imagehelper.get_image("character_limb", 0.8).rotate(-leg_angles[1], expand=1) # angle limit : -75 < theta < -15
        character_limb_right_leg_upper = self.imagehelper.get_image("character_limb", 0.8).rotate(-leg_angles[0], expand=1) # angle limit : -75 < theta < -15
        character_limb_right_leg_lower = self.imagehelper.get_image("character_limb", 0.8).rotate(-leg_angles[1], expand=1) # angle limit : -75 < theta < -15

        return self.imagehelper.overlay(
            backdrop, 
            [
                character_limb_right_leg_upper,
                character_limb_right_leg_lower,
                character_limb_left_leg_upper,
                character_limb_left_leg_lower, 
                character_limb_left_arm_upper, 
                character_limb_right_arm_upper, 
                character_limb_left_arm_lower, 
                character_limb_right_arm_lower, 
                character_body, 
                character_face
            ],
            [   
                (int(backdrop.width/2-character_body.width/2), character_body.height-30+character_face.height),
                (int(backdrop.width/2-character_body.width/2+character_limb_right_leg_upper.width-30), int(character_body.height+character_limb_right_leg_upper.height+character_face.height-60)),
                (int(backdrop.width/2-character_limb_right_leg_upper.width+character_body.width/2), character_body.height-30+character_face.height),
                (int(backdrop.width/2-character_body.width/2-character_limb_left_leg_upper.width+30), int(character_body.height+character_limb_left_leg_upper.height+character_face.height-60)),
                (int(backdrop.width/2-character_limb_left_arm_upper.width+character_body.width/2), 300), 
                (int(backdrop.width/2-character_body.width/2), 300), 
                (int(backdrop.width/2-character_limb_left_arm_upper.width-character_limb_left_arm_lower.width+character_body.width/2)+30, 300+character_limb_left_arm_upper.height-character_limb_left_arm_lower.height), 
                (int(backdrop.width/2+character_limb_right_arm_upper.width-character_body.width/2)-30, 300+character_limb_right_arm_upper.height-character_limb_right_arm_lower.height), 
                (int(backdrop.width/2-character_body.width/2), character_face.height), 
                (int(backdrop.width/2-character_face.width/2), 10)]
        )
    
    def move_character(self, initial_coords, final_coords, duration, frame_start, fps, backdrop, character_initial, character_final):

        # Contains total frames of animation
        frames = []

        # Initializes necessary variables for character angles and position of character
        [x_shift, y_shift, 
        left_arm_upper, 
        left_arm_lower, 
        right_arm_upper, 
        right_arm_lower, 
        legs_upper, 
        legs_lower] = [0, 0, 0, 0, 0, 0, 0, 0]

        # Calculates total frames needed for animation
        total_frames_count = int(duration*fps)

        # Creates every frame of the animation
        for frame in range(total_frames_count):

            # Adds frame to animation
            frames.append(
                # Generates frame
                self.imagehelper.overlay(
                    backdrop, 
                    [
                        self.get_character(
                            (
                                character_initial[0][0] + left_arm_upper, 
                                character_initial[0][1] + left_arm_lower
                            ),
                            (
                                character_initial[1][0] + right_arm_upper, 
                                character_initial[1][1] + right_arm_lower
                            ),
                            (
                                character_initial[2][0] + legs_upper, 
                                character_initial[2][1] + legs_lower
                            ),
                            "character_face"
                        )
                    ],
                    [
                        (int(initial_coords[0]+x_shift), int(initial_coords[1]+y_shift))
                    ]
                )
            )

            # Applies pixel shift necessary to create fluid animation
            x_shift += (final_coords[0] - initial_coords[0]) / (duration*fps)
            y_shift += (final_coords[1] - initial_coords[1]) / (duration*fps)
            left_arm_upper += (character_final[0][0] - character_initial[0][0])/(duration*fps)
            left_arm_lower += (character_final[0][1] - character_initial[0][1])/(duration*fps) 
            right_arm_upper += (character_final[1][0] - character_initial[1][0])/(duration*fps) 
            right_arm_lower += (character_final[1][1] - character_initial[1][1])/(duration*fps) 
            legs_upper += (character_final[2][0] - character_initial[2][0])/(duration*fps) 
            legs_lower += (character_final[2][1] - character_initial[2][1])/(duration*fps)

        return frames

    def get_text(self, text, backdrop):

        # Speech Bubble
        backdrop = backdrop.copy()
        draw = ImageDraw.Draw(backdrop)

        # Contains Text with Default Font
        font_size = 90
        ft = ImageFont.truetype(io.BytesIO(self.image_repository['font']), font_size)
        text_w = draw.textlength(text, font=ft)
        text_h = font_size
        backdrop_w, backdrop_h = backdrop.width, backdrop.height
        draw.text((backdrop_w/2-text_w/2, backdrop_h/2-text_h/2-10), text, fill =(0, 0, 0), font=ft)

        return backdrop

    def move_character_w_text(self, initial_coords, final_coords, duration, frame_start, fps, backdrop, character_initial, character_final, text_initial, text_final, text, speech_bubble, face):

        # contains frames of animation
        frames = []

        # Initializes necessary variables
        [x_shift, y_shift, 
        text_y_shift, 
        left_arm_upper, 
        left_arm_lower, 
        right_arm_upper, 
        right_arm_lower, 
        legs_upper, 
        legs_lower] = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Calculates total frames needed for animation
        total_frames_count = int(duration*fps)

        # Creates every frame of the animation
        for frame in range(total_frames_count):

            # adds frame to animation
            frames.append(
                # generates frame
                self.imagehelper.overlay(
                    backdrop, 
                    [
                        self.get_character(
                            (
                                character_initial[0][0] + left_arm_upper, 
                                character_initial[0][1] + left_arm_lower
                            ),
                            (
                                character_initial[1][0] + right_arm_upper, 
                                character_initial[1][1] + right_arm_lower
                            ),
                            (
                                character_initial[2][0] + legs_upper, 
                                character_initial[2][1] + legs_lower
                            ),
                            face
                        ),
                        self.get_text(text, speech_bubble)
                    ],
                    [
                        (int(initial_coords[0]+x_shift), int(initial_coords[1]+y_shift)), 
                        (int(backdrop.width/2-speech_bubble.width/2), int(text_initial+text_y_shift))
                    ]
                )
            )

            # applies pixel shift
            x_shift += (final_coords[0] - initial_coords[0]) / (duration*fps)
            y_shift += (final_coords[1] - initial_coords[1]) / (duration*fps)
            text_y_shift += (text_final - text_initial) / (duration*fps)
            left_arm_upper += (character_final[0][0] - character_initial[0][0])/(duration*fps)
            left_arm_lower += (character_final[0][1] - character_initial[0][1])/(duration*fps) 
            right_arm_upper += (character_final[1][0] - character_initial[1][0])/(duration*fps) 
            right_arm_lower += (character_final[1][1] - character_initial[1][1])/(duration*fps) 
            legs_upper += (character_final[2][0] - character_initial[2][0])/(duration*fps) 
            legs_lower += (character_final[2][1] - character_initial[2][1])/(duration*fps)

        return frames

class CharacterAnimation():
    
    def __init__(self, image_repository):
        self.image_repository = image_repository
        self.imagehelper = ImageHelper(self.image_repository)
        self.character = Character(self.image_repository)

    def wave_animation(self, repeat, backdrop, character, curr_frame):

        animation_frames = []
        animation_duration = []

        for counter in range(repeat):

            animation_frames += self.character.move_character(
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
                1, 
                curr_frame + len(animation_frames), 
                30, 
                backdrop,
                [(60, 30), (15, 30), (60, 90)],
                [(30, 30), (15, 60), (60, 90)]
            )

            animation_frames += self.character.move_character(
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100),
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100),
                1,
                curr_frame + len(animation_frames),
                30,
                backdrop,
                [(30, 30), (15, 60), (60, 90)],
                [(60, 30), (15, 30), (60, 90)]
            )

            animation_duration += [1, 1]

        return animation_frames, animation_duration

    def fall_animation(self, duration, backdrop, character, curr_frame):

        animation_frames = []
        animation_duration = [duration]

        animation_frames += self.character.move_character(
            (int(backdrop.width/2-character.width/2), 0),
            (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100),
            duration,
            curr_frame,
            30,
            backdrop,
            [(30, 30), (15, 30), (30, 90)],
            [(60, 30), (15, 30), (60, 90)]
        )

        return animation_frames, animation_duration

    def image_animation(self, duration, image, curr_frame, fps):

        animation_frames = []
        animation_duration = [duration]

        # Calculates total frames needed for animation
        total_frames_count = int(duration*fps)

        # Creates every frame of the animation
        for frame in range(total_frames_count):      
            animation_frames.append(
                image
            )

        return animation_frames, animation_duration

    def explain_animation(self, duration, backdrop, character, curr_frame, words, speech_bubble, offset):

        animation_frames = []
        animation_duration = []
        counter = 0

        animation_frames += self.character.move_character_w_text(
            (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
            (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
            0.5, 
            curr_frame + len(animation_frames), 
            30, 
            backdrop,
            [(30, 20), (30, 20), (60, 90)],
            [(60, 30), (60, 30), (60, 90)],
            -speech_bubble.height, 
            offset, 
            words[0],
            speech_bubble,
            "character_face"
        )
        animation_duration += [0.5]

        for iteration in range(int(len(words)/2)):

            animate_location = [(self.character.get_rand_angle(25, 45), self.character.get_rand_angle(15, 25)), 
                                (self.character.get_rand_angle(25, 45), self.character.get_rand_angle(15, 25)),
                                (60, 90)]

            animation_frames += self.character.move_character_w_text(
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
                duration[counter], 
                curr_frame + len(animation_frames), 
                30, 
                backdrop,
                [(60, 30), (60, 30), (60, 90)],
                animate_location,
                offset, 
                offset, 
                words[counter],
                speech_bubble,
                "character_face_1"
            )

            animation_duration += [duration[counter]]
            counter += 1

            animation_frames += self.character.move_character_w_text(
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), # initial coords
                (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), # final coords
                duration[counter], # duration
                curr_frame + len(animation_frames), # frame start
                30, # fps
                backdrop, # backdrop
                animate_location,
                [(60, 30), (60, 30), (60, 90)],
                offset, 
                offset, 
                words[counter],
                speech_bubble,
                "character_face_2"
            )

            animation_duration += [duration[counter]]
            counter += 1

        animation_frames += self.character.move_character_w_text(
            (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
            (int(backdrop.width/2-character.width/2), int(backdrop.height/2-character.height/2)+100), 
            0.5, 
            curr_frame + len(animation_frames), 
            30, 
            backdrop,
            [(60, 30), (60, 30), (60, 90)],
            [(30, 20), (30, 20), (60, 90)],
            offset, 
            -speech_bubble.height, 
            words[len(words)-1],
            speech_bubble,
            "character_face"
        )
        animation_duration += [0.5]

        return animation_frames, animation_duration

class VideoGenerator():
    
    def __init__(self, short):

        self.JokeAPI = JokeAPI()
        self.googlecloud = GoogleCloud()
        self.firebase = Firebase()
        self.aws = AWS()
        
        self.image_repository = {
            "backdrop" : io.BytesIO(self.googlecloud.read_file("video_assets/backdrop_basic_dark.png")),
            "backdrop_portrait" : io.BytesIO(self.googlecloud.read_file("video_assets/backdrop_basic_dark_portrait.png")),
            "character" : io.BytesIO(self.googlecloud.read_file("video_assets/character_template.png")),
            "character_container" : io.BytesIO(self.googlecloud.read_file("video_assets/backdrop_transparent.png")),
            "character_face" : io.BytesIO(self.googlecloud.read_file("character_dynamic/neutral_face.png")),
            "character_face_1" : io.BytesIO(self.googlecloud.read_file("character_dynamic/character_face_1.png")),
            "character_face_2" : io.BytesIO(self.googlecloud.read_file("character_dynamic/character_face_2.png")),
            "character_structure" : io.BytesIO(self.googlecloud.read_file("character_dynamic/structure.png")),
            "character_limb" : io.BytesIO(self.googlecloud.read_file("character_dynamic/limb.png")),
            "speech_bubble" : io.BytesIO(self.googlecloud.read_file("video_assets/speech_bubble_extended.png")),
            "speech_bubble_short" : io.BytesIO(self.googlecloud.read_file("video_assets/speech_bubble_short.png")),
            "crowd_silence" : io.BytesIO(self.googlecloud.read_file("video_assets/crowd_empty_scene.png")),
            "crowd_silence_short" : io.BytesIO(self.googlecloud.read_file("video_assets/crowd_empty_scene_portrait.png")),
            "font" : requests.get("https://github.com/docrepair-fonts/belanosima-fonts/blob/main/fonts/ttf/Belanosima-SemiBold.ttf?raw=true").content
        }

        self.imagehelper = ImageHelper(self.image_repository)
        self.character = Character(self.image_repository)
        self.characteranimation = CharacterAnimation(self.image_repository)
        self.videohelper = VideoHelper()

        self.SHORT = short

        if (short):
            self.BACKDROP = self.imagehelper.get_image("backdrop_portrait", 1.0)
            self.SPEECH_BUBBLE = self.imagehelper.get_image("speech_bubble_short", 0.8)
            self.SPEECH_BUBBLE_POSITION_Y = 375
            self.VIDEO_WIDTH, self.VIDEO_HEIGHT = 1080, 1920
        else:
            self.BACKDROP = self.imagehelper.get_image("backdrop", 1.0)
            self.SPEECH_BUBBLE = self.imagehelper.get_image("speech_bubble", 0.8)
            self.SPEECH_BUBBLE_POSITION_Y = 100
            self.VIDEO_WIDTH, self.VIDEO_HEIGHT = 1920, 1080

        self.DEFAULT_CHARACTER = self.character.get_character((60, 30), (15, 30), (25, 90), "character_face")

        self.total_frames = []
        self.times_frames = []
        self.audio_files = []
        self.seconds_processed = 0
        self.text_id = 0
        self.video_title = "Joke Of The Day "
        self.pre_joke = "t2dec is da best"
        self.joke = "Ka Ching..."
        self.video_file = ""
        self.video_link = ""

        debug("All video generation assets loaded.")

    def clean_files(self):
        # Emptys Cache to prevent overwriting files
        try:
            self.googlecloud.empty_cache(self.BUCKET_NAME, "frames", self.CREDENTIALS)
            self.googlecloud.delete_file(self.BUCKET_NAME, "video_assets/character.png", self.CREDENTIALS)
            self.googlecloud.delete_file(self.BUCKET_NAME, "video_output/result.mp4", self.CREDENTIALS)
            self.googlecloud.delete_file(self.BUCKET_NAME, "audio/joke0.mp3", self.CREDENTIALS)
            self.googlecloud.delete_file(self.BUCKET_NAME, "audio/joke1.mp3", self.CREDENTIALS)
            debug("Cache Cleared.")
        except:
            debug("Cache Cleared - Already Empty.")

    def get_fall_animation(self, duration):

        animation_frames, animation_time_frames = self.characteranimation.fall_animation(
            duration, 
            self.BACKDROP, 
            self.DEFAULT_CHARACTER, 
            len(self.total_frames)
        )

        self.seconds_processed += duration
        self.total_frames += animation_frames
        self.times_frames += animation_time_frames
        self.audio_files.append((
            self.firebase.retrieveAudio(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/T2DecComedyAssets/audio/mute.mp3"
            ), 
            (0, duration)
        ))

        debug("Fall animation succesfully created.")
        return "Fall animation succesfully created."
    
    def get_text_animation(self, text):

        words, times, filename = self.aws.get_text_audio(text)
        # self.audio_files.append((
        #     self.firebase.retrieveAudio(
        #         "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/T2DecComedyAssets/audio/mute.mp3"
        #     ), 
        #     (self.seconds_processed, self.seconds_processed+0.25)
        # ))

        # self.seconds_processed += 0.25
        self.audio_files.append((filename, (self.seconds_processed, self.seconds_processed+sum(times))))

        animation_frames, animation_time_frames = self.characteranimation.explain_animation(
            times, 
            self.BACKDROP, 
            self.DEFAULT_CHARACTER, 
            len(self.total_frames), 
            words,
            self.SPEECH_BUBBLE,
            self.SPEECH_BUBBLE_POSITION_Y
        )
        
        self.seconds_processed += sum(times)
        self.total_frames += animation_frames
        self.times_frames += animation_time_frames
        
        self.text_id += 1

        debug("Simple text animation succesfully created.")
        return "Simple text animation succesfully created."
    
    def show_static_image(self, image, duration):

        animation_frames, animation_time_frames = self.characteranimation.image_animation(duration,
                                                                image,
                                                                len(self.total_frames),
                                                                30)
        
        self.seconds_processed += duration
        self.total_frames += animation_frames
        self.times_frames += animation_time_frames

        debug("Static image animation succesfully created.")
        return "Static image animation succesfully created."
    
    def show_crowd(self, duration):

        if self.SHORT:
            self.show_static_image(self.imagehelper.get_image("crowd_silence_short", 1), duration)
        else:
            self.show_static_image(self.imagehelper.get_image("crowd_silence", 1), duration)

        self.audio_files.append((
            self.firebase.retrieveAudio(
                "https://storage.googleapis.com/itsnousv3.appspot.com/GraphicsTemplates/T2DecComedyAssets/audio/mute.mp3"
            ), 
            (self.seconds_processed, self.seconds_processed+(duration*2))
        ))

        return True
    
    def create_video(self):

        # Starts recording time to create video
        start_time = time.time()
        
        # Intro
        self.get_fall_animation(0.25)

        # Joke Retrieved
        joke_element = self.JokeAPI.getJoke()

        # Prevents character limit problem for youtube title
        if (len(joke_element[1]) > 64):
            self.video_title = joke_element[1][0:64]
        else:
            self.video_title = joke_element[1]

        # Allows for greater varitey of jokes
        if (joke_element[0] == True):
            # Joke Setup
            self.get_text_animation(f"I have an amazing joke for you: {joke_element[1]}")
            self.pre_joke = joke_element[1]
            self.joke = joke_element[2]
            # Intermission
            self.show_crowd(1)

            # Joke Delivery
            # debug(joke_element[2])
            self.get_text_animation(joke_element[2])
        else:
            # Joke Setup
            self.get_text_animation(f"I have an amazing joke for you: {joke_element[1]}")
            self.pre_joke = joke_element[1]
            self.joke = ""

        # Records total time to create video elements
        debug(f"--- {(time.time() - start_time)} seconds to create all video elements. ---")

        return True
    
    def render(self):

        # Starts recording time to create video
        start_time = time.time()

        self.video_file = self.videohelper.render_video(
            self.total_frames, 
            self.VIDEO_WIDTH, 
            self.VIDEO_HEIGHT, 
            sum(self.times_frames), 
            self.audio_files
        )
        
        # Records total time to create video elements
        debug(f"--- {(time.time() - start_time)} seconds to render video. ---")

        return self.video_file

    def retrieveVidInfo(self):
        return {
            "title": f"{self.video_title}.. #shorts",
            "description": f"{self.pre_joke} {self.joke}"
        }

# Function to upload videos after generation
class YouTubeUploader():
    
    def __init__(self):
        self.vidGen = VideoGenerator(True)
        self.firebase = Firebase()

    def createDarkComedyVid(self):
        
        # Initializes YouTube Video
        self.vidGen.create_video()
        vid_info = self.vidGen.retrieveVidInfo()
        vid_description = self.firebase.retrieveYouTubeDescriptionTemplate(
            vid_info["description"]
        )
        vid = YouTubeVideo(
            vid_info["title"],
            vid_description
        )

        # Generates vid and uploads video
        vid_file = self.vidGen.render()
        vid.uploadVideo(
            video_file=vid_file.name,
            tags=["dark", "comedy", "funny", "shorts", "jokes"],
            category_id="24"
        )

        # Adds default thumbnail
        vid.addThumbnail(
            "https://storage.googleapis.com/itsnousv3.appspot.com/YouTubeDefaults/darkComedyBackgroundThumbnail.png"
        )

        # Adds vid to playlist and cleans up temp files
        vid.addPlaylist("PLizmHl7t7otdYRHcWX8Q6RQGYHpD-D-WE")
        vid_file.close()
        os.unlink(vid_file.name)

        # Updates status
        return vid.updateStatus()

""" Firebase Functions """

# The Google Cloud Config for this function is 2 vCPU and 4 Gi (gibibyte)
# The timeout is also custom at 360 seconds.
# 7:10 AM UTC -> 3:10 AM EST
# Firebase function which generates and uploads videos to YouTube daily
@scheduler_fn.on_schedule(schedule="every day 07:10")
def uploadDarkComedyVideoDaily(event: scheduler_fn.ScheduledEvent) -> None:

    # Retrieves YouTubeUploader functions
    youtubeUpload = YouTubeUploader()
    num_videos = 2

    for counter in range(0, num_videos):
        try:
            # Creates and uploads video
            youtubeUpload.createDarkComedyVid()
        except Exception as error:
            print(f"error - {counter}")
    
    return https_fn.Response("Success")