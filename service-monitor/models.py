import datetime
import pytz
from django.db import models
from django.db.models import Q
from django.conf import settings

SERVICE_MONITOR__DEFAULT_PING_INTERVAL = 30 #Default number of minutes to wait between sending pings
SERVICE_MONITOR__DEFAULT_WAIT_TIME = 5      #Default number of minutes to wait before considering a ping request to be timed out

SERVICE_MONITOR__HTTP = 1
SERVICE_MONITOR__SMS = 2

SERVICE_MONITOR__REQUEST_SENT = 1
SERVICE_MONITOR__RESPONSE_RECEIVED = 2
SERVICE_MONITOR__NO_RESPONSE = 3

SERVICE_MONITOR__SERVICE_TYPES = (
    (SERVICE_MONITOR__HTTP, "HTTP")
   ,(SERVICE_MONITOR__SMS, "SMS")
)

SERVICE_MONITOR__REQUEST_STATES = (
    (SERVICE_MONITOR__REQUEST_SENT, "Request Sent")
   ,(SERVICE_MONITOR__RESPONSE_RECEIVED, "Response Received")
   ,(SERVICE_MONITOR__NO_RESPONSE, "No Response")
)

"""
A model which defines a service to monitor. To monitor another
service, create another Service entry with the following fields 
and save it to the database (all other fields can be left blank
on creation):

name
service_type
connection
url
email

"""
class Service(models.Model):
    name = models.CharField(
        max_length=50
       ,help_text="The name of this service."
    )
    
    service_type = models.IntegerField(
        choices=SERVICE_MONITOR__SERVICE_TYPES
    )
    
    connection = models.ForeignKey(
        "rapidsms.Connection"
       ,null=True
       ,blank=True
       ,help_text="For service type SMS only: the connection to use when sending the SMS."
    )
    
    url = models.CharField(
        max_length=200
       ,null=True
       ,blank=True
       ,help_text="For service type HTTP only: the url to ping."
    )
    
    email_list = models.CharField(
        max_length=500
       ,help_text="A list of recipients for the email notification if the service is not responding (separate multiple email addresses with a | )."
    )
    
    last_request_date = models.DateTimeField(
        null=True
       ,blank=True
    )
    
    last_response_date = models.DateTimeField(
        null=True
       ,blank=True
    )
    
    ping_state = models.IntegerField(
        choices=SERVICE_MONITOR__REQUEST_STATES
       ,null=True
       ,blank=True
    )
    
    def __unicode__(self):
        return self.name
    
    """
    Returns True if the proper amount of time has passed since the 
    last ping request to send another ping request, otherwise False.
    If a ping request has not yet been made, returns True.
    """
    def can_ping_again(self):
        if self.last_request_date is None:
            return True
        else:
            delta = datetime.timedelta(minutes=getattr(settings,"SERVICE_MONITOR__PING_INTERVAL",SERVICE_MONITOR__DEFAULT_PING_INTERVAL))
            next_ping_time = self.last_request_date + delta
            current_time = datetime.datetime.now()
            # Note: Django returns self.last_request_date as a naive datetime object, converted to the local timezone
            #       Also, datetime.datetime.now() is a naive datetime object in the local time zone
            #       So comparing the two is ok
            return (current_time > next_ping_time)

    """
    (Right now this only applies to SMS requests)
    Returns True if the proper amount of time has passed since the
    ping request was made to constitute a timeout.
    If a ping request has not yet been made, returns False.
    """
    def has_timed_out(self):
        if self.last_request_date is None:
            return False
        else:
            delta = datetime.timedelta(minutes=getattr(settings,"SERVICE_MONITOR__WAIT_TIME",SERVICE_MONITOR__DEFAULT_WAIT_TIME))
            timeout_time = self.last_request_date + delta
            current_time = datetime.datetime.now()
            # Note: Django returns self.last_request_date as a naive datetime object, converted to the local timezone
            #       Also, datetime.datetime.now() is a naive datetime object in the local time zone
            #       So comparing the two is ok
            return (current_time > timeout_time)

"""
All ping requests, responses, and timeouts are
stored in the PingLog (one per entry).
"""
class PingLog(models.Model):
    service = models.ForeignKey("Service",db_index=True)
    date = models.DateTimeField(db_index=True)
    ping_state = models.IntegerField(choices=SERVICE_MONITOR__REQUEST_STATES,db_index=True)

