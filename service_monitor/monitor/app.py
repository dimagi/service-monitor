from datetime import datetime
import pytz
import re

from .tasks import send_notification_email
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
               ,callback="monitor.tasks.run"
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
            # Get the regular expression which the response should match
            service = Service.objects.get(connection=message.connection)
            valid_response_regex = service.valid_response_regex
            if (valid_response_regex is None) or (valid_response_regex == ""):
                valid_response_regex = r"^(.+)$"
            regex = re.compile(valid_response_regex)
            
            # Mark the service as having responded, either with a valid or invalid response
            current_date = datetime.now(tz=pytz.utc)
            service.last_response_date = current_date
            if regex.match(message.text):
                service.ping_state = SERVICE_MONITOR__VALID_RESPONSE_RECEIVED
            else:
                service.ping_state = SERVICE_MONITOR__INVALID_RESPONSE_RECEIVED
            service.save()
            
            # Create an entry in the PingLog
            pinglog_entry = PingLog(service=service,date=current_date,ping_state=service.ping_state)
            pinglog_entry.save()
            
            # If an invalid response was received, send a notification email
            if service.ping_state == SERVICE_MONITOR__INVALID_RESPONSE_RECEIVED:
                send_notification_email(service)
        except Exception, e:
            self.exception(e)
        
        # This should always return true to prevent any auto-texting of default messages back and forth
        return True

