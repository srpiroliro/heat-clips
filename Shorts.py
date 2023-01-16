from pprint import pprint
from pytube import YouTube

# from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.io.VideoFileClip import VideoFileClip

import requests
import json
import re
import os

from urls import *

class Shorts:
    def __init__(self, clip_length:float=30,clip_start_point:float=1/4) -> None:
        self.clip_length=clip_length
        self.clip_start_point=clip_start_point
        
        self.heat_data=None        
        self.downloading_folder="download"
        
    def build(self, video_id:str)->bool:
        print("getting data...")
        self.heat_data=self.get_heat(video_id)
        print("got data.")
        
        print()
        print(self.heat_data)
        print()
        
        if self.heat_data:
            print("downloading files...")
            downloaded_video=self.download(video_id)
            print("downloaded.")
            
            if downloaded_video:
                print("extracting clips")
                e=self.extract_clips(downloaded_video)
                if e: 
                    print(f"CLIPS CREATED IN {e}")
                else: print("error during extraction of clips") 
            else: print("video not downloaded")
        else: print("video doesnt have a heatmap.")
        
        return False

    def get_heat(self,video_id:str, skip_start:bool=False)->list:
        """ returns the top 3 most viewed clips """
        request=requests.get(url=URL_HEAT+video_id)
        data=json.loads(request.text)
        most_replayed=data["items"][0]["mostReplayed"]
        
        if not most_replayed: return None
        
        fd={
            "top":[],
            "clips":[],
            "marker_duration":None,
            "length":0,
            "views":0,
            "likes":0
        }

        heat_markers=data["items"][0]["mostReplayed"]["heatMarkers"]
        fd["marker_duration"]=heat_markers[0]["heatMarkerRenderer"]["markerDurationMillis"]/1000
        
        heat_markers.sort(key=lambda r:-r["heatMarkerRenderer"]["heatMarkerIntensityScoreNormalized"])

        for i,part in enumerate(heat_markers):
            rge=part["heatMarkerRenderer"]["timeRangeStartMillis"]/1000
            
            if ((all([round(abs(x-rge),2)>self.clip_length for x in fd["top"]]) or i==0) and self.clip_length) and (rge!=0 or not skip_start):
                fd["top"].append(rge)
                if len(fd["top"])==3: break

        request=requests.get(url=URL_LENGTH+video_id)
        data=json.loads(request.text)
        duration=data["items"][0]["contentDetails"]["duration"]
        
        fd["length"]=self.__duration2seconds(duration)

        request=requests.get(url=URL_STATS+video_id)
        data=json.loads(request.text)
        stats=data["items"][0]["statistics"]

        fd["views"]=int(stats["viewCount"])
        fd["likes"]=int(stats["likeCount"])
        
        fd["clips"]=[
            [max(0,h-self.clip_length*self.clip_start_point), 
                min(fd["length"],h+self.clip_length*(1-self.clip_start_point))] 
            for h in fd["top"]
        ]

        return fd

    def download(self, video_id:str):
        try:
            video=YouTube(f"https://youtu.be/{video_id}")
            # FIX: picks up 720p when 1080p seems to be available.
            hr=video.streams.get_highest_resolution()
            return hr.download(output_path=self.downloading_folder,filename=f"{video_id}.mp4")
        except Exception as e: 
            print(f"error happend: {e}")
            return False

    def extract_clips(self, source:str):
        n=source.split(".")[0].rsplit("/",1)[-1]
        p=f"clips/{n}"
        
        self.__create404(p)
        
        with VideoFileClip(source) as video:
            for i,clip in enumerate(self.heat_data["clips"]):
                new=video.subclip(clip[0], clip[1])
                new.write_videofile(f"{p}/{i}.mp4", verbose=False, logger=None)
            return p
    
    def __create404(self,p:str):
        tmp=""
        for folder in p.strip("/").split("/"):
            tmp+=folder+"/"
            if not os.path.exists(tmp): os.mkdir(tmp)
    def __duration2seconds(self,duration:str):
        d=re.findall(r"PT(([0-9]+)H)?(([0-9]+)M)(([0-9]+)S)",duration)
        matches=list(d[0])[::-1]
        
        seconds=int(matches[0])
        minutes=int(matches[2])
        hours=0 
        if len(matches)>4 and matches[-1]:
            hours=int(matches[4])
        
        return seconds+(minutes+hours*60)*60
