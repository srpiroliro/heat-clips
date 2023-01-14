from pprint import pprint
import requests,json, re

ROOT_API="https://yt.lemnoslife.com/"
URL_HEAT=ROOT_API+"videos?part=mostReplayed&id="
URL_LENGTH=ROOT_API+"noKey/videos?part=contentDetails&id="
URL_STATS=ROOT_API+"noKey/videos?part=statistics&id="


def get_heat(video_id:str)->list:
    """ returns the top 3 most viewed clips """
    request=requests.get(url=URL_HEAT+video_id)
    data=json.loads(request.text)
    most_replayed=data["items"][0]["mostReplayed"]
    
    final_data={
        "top":[],
        "marker_duration":None,
        "length":0,
        "views":0,
        "likes":0
    }
    
    if most_replayed:
        heat_markers=data["items"][0]["mostReplayed"]["heatMarkers"]
        heat_markers.sort(key=lambda r:-r["heatMarkerRenderer"]["heatMarkerIntensityScoreNormalized"])
        
        for i,part in enumerate(heat_markers):
            data=part["heatMarkerRenderer"]
            final_data["marker_duration"]=data["markerDurationMillis"]/1000
            
            rge=data["timeRangeStartMillis"]/1000
            prev=heat_markers[max(i-2,max(i-1,0))]["heatMarkerRenderer"]["timeRangeStartMillis"]/1000
            print(prev, round(abs(prev-rge),2))
            if i==0 or round(abs(prev-rge),2)>final_data["marker_duration"]:
                final_data["top"].append(rge)
                if len(final_data["top"])==3: break
            
            

    request=requests.get(url=URL_LENGTH+video_id)
    data=json.loads(request.text)
    duration=data["items"][0]["contentDetails"]["duration"]
    
    final_data["length"]=duration2seconds(duration)

    request=requests.get(url=URL_STATS+video_id)
    data=json.loads(request.text)
    stats=data["items"][0]["statistics"]

    final_data["views"]=int(stats["viewCount"])
    final_data["likes"]=int(stats["likeCount"])

    return final_data

def duration2seconds(duration:str):
    d=re.findall(r"PT(([0-9]+)H)?(([0-9]+)M)(([0-9]+)S)",duration)
    matches=list(d[0])[::-1]
    
    seconds=int(matches[0])
    minutes=int(matches[2])
    hours=0 
    if len(matches)>4 and matches[-1]:
        hours=int(matches[4])
    
    return seconds+(minutes+hours*60)*60
    
pprint(get_heat("k-GH3mbvUro"))