import datetime

class DatetimeFormatting():
    
    def __init__(self):
        pass

    def format_time(self, time):
        """format time into mm:ss or h:mm:ss if h > 0

        Args:
            time (datetime.datetime): time

        Returns:
            str: str in the format specfied above
        """
        h, r = divmod(time.seconds, 3600)
        m, s = divmod(r, 60)
                
        if h: return f"{h}:{m:02d}:{s:02d}"
        else: return f"{m:02d}:{s:02d}"