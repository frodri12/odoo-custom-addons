import datetime
import pytz

from datetime import datetime
from pytz import timezone

date = "2025-03-25T13:24:15 -04:00"

tz_value = date.split(" ")[1]
date_value = date.split(" ")[0]

date1 = date_value.split("T")[0]
date2 = date_value.split("T")[1]

dateTime = datetime.strptime( date_value + tz_value.replace(":",""), "%Y-%m-%dT%H:%M:%S%z")

utc_date = dateTime.astimezone( pytz.timezone("UTC"))
odoo_fmt = datetime.strptime( utc_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")

print( dateTime)
print( utc_date)
print( odoo_fmt)
