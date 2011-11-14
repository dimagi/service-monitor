import datetime
import pytz
import urllib2

from .models import *
from django.db.models import Q
from rapidsms.contrib.messaging.utils import send_message
from django.core.mail import EmailMessage
from django.conf import settings
from urllib2 import URLError

"""
Sends a "Service Not Responding" email to the list of email 
recipients specified for the given service.
"""
def send_notification_email(service):
    subject_text = "Service Monitor: Service '" + service.name + "' Not Responding"
    body_text = ""
    
    if service.service_type == SERVICE_MONITOR__SMS:
        body_text = "Mobile Number: " + service.connection.identity
    elif service.service_type == SERVICE_MONITOR__HTTP:
        body_text = "URL: " + service.url
    
    recipients = service.email_list.split("|")
    
    email = EmailMessage (
        subject = subject_text
       ,body = body_text
       ,to = recipients
    )
    email.send()

"""
This is the callback function that is called by the
EventSchedule every minute. For each service in the 
database, this function will see if enough time has
passed to ping the service again, and ping the service
accordingly.
"""
def run(*args, **kwargs):
    for service in Service.objects.all():
        if service.service_type == SERVICE_MONITOR__SMS:
            #
            # Handle SMS Monitoring
            #
            if service.can_ping_again():
                # Mark the request as being sent for this service
                current_date = datetime.datetime.now(tz=pytz.utc)
                service.last_request_date = current_date
                service.last_response_date = None
                service.ping_state = SERVICE_MONITOR__REQUEST_SENT
                service.save()
                
                # Create an entry in the PingLog
                pinglog_entry = PingLog(service=service,date=current_date,ping_state=service.ping_state)
                pinglog_entry.save()
                
                # Send the SMS
                send_message(service.connection, "Ping Request")
            elif service.ping_state == SERVICE_MONITOR__REQUEST_SENT and service.has_timed_out():
                # Mark the request as having no response
                service.ping_state = SERVICE_MONITOR__NO_RESPONSE
                service.save()
                
                # Create an entry in the PingLog
                current_date = datetime.datetime.now(tz=pytz.utc)
                pinglog_entry = PingLog(service=service,date=current_date,ping_state=service.ping_state)
                pinglog_entry.save()
                
                # Send an email notification
                send_notification_email(service)
        elif service.service_type == SERVICE_MONITOR__HTTP:
            #
            # Handle HTTP Monitoring
            #
            if service.can_ping_again():
                # Mark the request as being sent for this service
                current_date = datetime.datetime.now(tz=pytz.utc)
                service.last_request_date = current_date
                service.last_response_date = None
                service.ping_state = SERVICE_MONITOR__REQUEST_SENT
                service.save()
                
                # Create an entry in the PingLog
                pinglog_entry = PingLog(service=service,date=current_date,ping_state=service.ping_state)
                pinglog_entry.save()
                
                # Try to send the request
                timeout_minutes = getattr(settings,"SERVICE_MONITOR__WAIT_TIME",SERVICE_MONITOR__DEFAULT_WAIT_TIME)
                try:
                    result = urllib2.urlopen(service.url,timeout=timeout_minutes*60)
                    
                    # Mark the service as having responded 
                    current_date = datetime.datetime.now(tz=pytz.utc)
                    service.last_response_date = current_date
                    service.ping_state = SERVICE_MONITOR__RESPONSE_RECEIVED
                    service.save()
                    
                    # Create an entry in the PingLog
                    pinglog_entry = PingLog(service=service,date=current_date,ping_state=service.ping_state)
                    pinglog_entry.save()
                except URLError:
                    # Mark the request as having no response
                    service.ping_state = SERVICE_MONITOR__NO_RESPONSE
                    service.save()
                    
                    # Create an entry in the PingLog
                    current_date = datetime.datetime.now(tz=pytz.utc)
                    pinglog_entry = PingLog(service=service,date=current_date,ping_state=service.ping_state)
                    pinglog_entry.save()
                    
                    # Send an email notification
                    send_notification_email(service)

