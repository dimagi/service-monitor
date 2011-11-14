import datetime
import pytz

from .models import *
from rapidsms.apps.base import AppBase
from scheduler.models import *
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

class App(AppBase):
    
    """
    Upon starting the router, create an EventSchedule to do
    the periodic pinging if it has not yet been created.
    """
    def start(self):
        try:
            e = EventSchedule.objects.get(description="Service Monitor Schedule")
        except ObjectDoesNotExist:
            e = EventSchedule(
                description="Service Monitor Schedule"
               ,callback="service_monitor.tasks.run"
               ,minutes=ALL_VALUE
            )
            e.save()
    
    """
    When a message comes in, lookup the service associated with
    the mobile number it was sent from and mark that service as
    having responded.
    """
    def handle(self, message):
        try:
            # Mark the service as having responded
            current_date = datetime.datetime.now(tz=pytz.utc)
            service = Service.objects.get(connection=message.connection)
            service.last_response_date = current_date
            service.ping_state = SERVICE_MONITOR__RESPONSE_RECEIVED
            service.save()
            
            # Create an entry in the PingLog
            pinglog_entry = PingLog(service=service,date=current_date,ping_state=service.ping_state)
            pinglog_entry.save()
        except Exception:
            pass
        
        # This should always return true to prevent any auto-texting of default messages back and forth
        return True

