import datetime
import pytz
from django.db import models
from django.db.models import Q
from django.conf import settings

SERVICE_MONITOR__HTTP = 1
SERVICE_MONITOR__SMS = 2

SERVICE_MONITOR__REQUEST_SENT = 1
SERVICE_MONITOR__VALID_RESPONSE_RECEIVED = 2
SERVICE_MONITOR__NO_RESPONSE = 3
SERVICE_MONITOR__INVALID_RESPONSE_RECEIVED = 4

SERVICE_MONITOR__SERVICE_TYPES = (
    (SERVICE_MONITOR__HTTP, "HTTP")
   ,(SERVICE_MONITOR__SMS, "SMS")
)

SERVICE_MONITOR__REQUEST_STATES = (
    (SERVICE_MONITOR__REQUEST_SENT, "Request Sent")
   ,(SERVICE_MONITOR__VALID_RESPONSE_RECEIVED, "Valid Response Received")
   ,(SERVICE_MONITOR__NO_RESPONSE, "No Response")
   ,(SERVICE_MONITOR__INVALID_RESPONSE_RECEIVED, "Invalid Response Received")
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
    class Meta:
        db_table = "service_monitor_service"
    
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
    
    sms_to_send = models.CharField(
        max_length=160
       ,help_text="For service type SMS only: the SMS to send to the service when checking for responsiveness."
       ,blank=True
    )
    
    valid_response_regex = models.CharField(
        max_length=200
       ,help_text="For service type SMS only: the regular expression used to validate the response from the SMS service. Leave blank to count any response as a valid response."
       ,null=True
       ,blank=True
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
    
    ping_interval_minutes = models.IntegerField(
        help_text="The number of minutes between each ping of the service."
    )
    
    timeout_minutes = models.IntegerField(
        help_text="The number of minutes to wait before determining that the service has timed out."
    )
    
    active = models.BooleanField(
        default=True
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
            delta = datetime.timedelta(minutes=self.ping_interval_minutes)
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
            delta = datetime.timedelta(minutes=self.timeout_minutes)
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
    class Meta:
        db_table = "service_monitor_pinglog"
    
    service = models.ForeignKey("Service",db_index=True)
    date = models.DateTimeField(db_index=True)
    ping_state = models.IntegerField(choices=SERVICE_MONITOR__REQUEST_STATES,db_index=True)

