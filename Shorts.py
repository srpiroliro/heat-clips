from pprint import pprint
from pytube import YouTube

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

import requests
import json
import re

from secret import *

class Shorts:
    def __init__(self, video_id:str,clip_length:float=None) -> None:
        self.clip_length=clip_length
        self.video_id=video_id
        
        self.heat_data=None
        self.original_vid=None
        
        self.downloading_folder="download"

    def get_heat(self,video_id:str, skip_start:bool=False,clip_start_point:float=3/4)->list:
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
            data=part["heatMarkerRenderer"]
            
            rge=data["timeRangeStartMillis"]/1000
            # prev=heat_markers[max(i-1,0)]["heatMarkerRenderer"]["timeRangeStartMillis"]/1000
            
            if ((all([round(abs(x-rge),2)>self.clip_length for x in fd["top"]]) or i==0) and self.clip_length) and (rge!=0 or not skip_start):
                fd["top"].append(rge)
                if len(fd["top"])==3: break
        
        fd["clips"]=[[h-self.clip_length*clip_start_point, h+self.clip_length*(1-clip_start_point)] for h in fd["top"]]


        request=requests.get(url=URL_LENGTH+video_id)
        data=json.loads(request.text)
        duration=data["items"][0]["contentDetails"]["duration"]
        
        fd["length"]=self.__duration2seconds(duration)

        request=requests.get(url=URL_STATS+video_id)
        data=json.loads(request.text)
        stats=data["items"][0]["statistics"]

        fd["views"]=int(stats["viewCount"])
        fd["likes"]=int(stats["likeCount"])

        # return fd
        self.heat_data=fd

    def download(self,video_id:str):
        video=YouTube(f"https://youtu.be/{video_id}")
        try:
            # FIX: picks up 720p when 1080p seems to be available.
            video.streams.get_highest_resolution().download(out_path=self.downloading_folder,filename=video_id)
        except Exception as e: print(f"error happend: {e}")
        else:
            self.original_vid=self.downloading_folder+video_id

    def extract_clips(self):
        download_
        # https://stackoverflow.com/questions/37317140/cutting-out-a-portion-of-video-python
        for i,clip in enumerate(self.heat_data["clips"]):
            ffmpeg_extract_subclip(self.original_vid, clip[0], clip[1], targetname=f"clip{i}.mp4")

    def __duration2seconds(self,duration:str):
        d=re.findall(r"PT(([0-9]+)H)?(([0-9]+)M)(([0-9]+)S)",duration)
        matches=list(d[0])[::-1]
        
        seconds=int(matches[0])
        minutes=int(matches[2])
        hours=0 
        if len(matches)>4 and matches[-1]:
            hours=int(matches[4])
        
        return seconds+(minutes+hours*60)*60
