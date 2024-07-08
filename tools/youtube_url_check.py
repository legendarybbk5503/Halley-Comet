from urllib.parse import urlparse

class Check():
    
    def __init__(self):
        pass
    
    def is_yt_url(self, url:str) -> bool:
        domain = urlparse(url).netloc
        
        if domain in ("youtu.be", "m.youtube.com", "youtube.com", "www.youtube.com"):
            return True
        return False

    def is_watch_url(self, url:str) -> bool:
        if self.is_yt_url(url):
            return url.__contains__("watch")

    def is_playlist_url(self, url:str) -> bool:
        if self.is_yt_url(url):
            return url.__contains__("playlist")