from datetime import datetime as dt

def datetime_digitavote(field):
    date1, time1 = field.split("T")

    year1, month1, day1 = date1.split("-")
    hour1, minutes1 = time1.split(":")

    d1 = dt(year=int(year1), month=int(month1), day=int(day1), hour=int(hour1), minute=int(minutes1))
    
    return {"datetime": d1, "timestamp": d1.timestamp()}