from pprint import pprint
import requests,json, re

ROOT_API="https://yt.lemnoslife.com/"
URL_HEAT=ROOT_API+"videos?part=mostReplayed&id="
URL_LENGTH=ROOT_API+"noKey/videos?part=contentDetails&id="
URL_STATS=ROOT_API+"noKey/videos?part=statistics&id="


def get_heat(video_id:str, clip_length:float=None, skip_start:bool=False, clip_start_point:float=3/4)->list:
    """ returns the top 3 most viewed clips """
    request=requests.get(url=URL_HEAT+video_id)
    data=json.loads(request.text)
    most_replayed=data["items"][0]["mostReplayed"]
    
    fd={
        "top":[],
        "clips":[],
        "marker_duration":None,
        "length":0,
        "views":0,
        "likes":0
    }

    if most_replayed:
        heat_markers=data["items"][0]["mostReplayed"]["heatMarkers"]
        fd["marker_duration"]=heat_markers[0]["heatMarkerRenderer"]["markerDurationMillis"]/1000
        
        heat_markers.sort(key=lambda r:-r["heatMarkerRenderer"]["heatMarkerIntensityScoreNormalized"])

        for i,part in enumerate(heat_markers):
            data=part["heatMarkerRenderer"]
            
            rge=data["timeRangeStartMillis"]/1000
            # prev=heat_markers[max(i-1,0)]["heatMarkerRenderer"]["timeRangeStartMillis"]/1000
            
            if ((all([round(abs(x-rge),2)>clip_length for x in fd["top"]]) or i==0) and clip_length) and (rge!=0 or not skip_start):
                fd["top"].append(rge)
                if len(fd["top"])==3: break
        
        fd["clips"]=[[h-clip_length*clip_start_point, h+clip_length*(1-clip_start_point)] for h in fd["top"]]


    request=requests.get(url=URL_LENGTH+video_id)
    data=json.loads(request.text)
    duration=data["items"][0]["contentDetails"]["duration"]
    
    fd["length"]=duration2seconds(duration)

    request=requests.get(url=URL_STATS+video_id)
    data=json.loads(request.text)
    stats=data["items"][0]["statistics"]

    fd["views"]=int(stats["viewCount"])
    fd["likes"]=int(stats["likeCount"])
    
    

    return fd

def duration2seconds(duration:str):
    d=re.findall(r"PT(([0-9]+)H)?(([0-9]+)M)(([0-9]+)S)",duration)
    matches=list(d[0])[::-1]
    
    seconds=int(matches[0])
    minutes=int(matches[2])
    hours=0 
    if len(matches)>4 and matches[-1]:
        hours=int(matches[4])
    
    return seconds+(minutes+hours*60)*60
    
pprint(get_heat("im2DetQWs24", 20, True, 1/2))