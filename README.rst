Service Monitor
===============

Overview
========
This app allows for monitoring responses of any number of services. If no response is received within the allotted timeout phase for a given service, an email notification is sent to the specified users. The services can be of the following types:

  * SMS: Periodically, an SMS is sent to the mobile number for a given service. If no response is received within the timeout phase, an email notification is sent.

  * HTTP: Periodically, the app tries to open the given url. If no response is received within the timeout phase, an email notification is sent. Note that only a "200 OK" response constitues as a valid response (response codes of 404, 500, etc. will result in a notification being sent).

Installation
============
1. Retrieve the code:
  
    git clone git@github.com:dimagi/service-monitor.git
    cd service-monitor
  
2. Ensure that all packages in requirements/apt-packages are installed (if any are not already installed, use apt-get to install them).
  
3. Install pip and virtualenv:
  
    easy_install pip
    pip install -U virtualenv
    pip install -U virtualenvwrapper
  
4. Create a virtual environment for the deployment:
  
    mkvirtualenv --distribute service-monitor
    workon service-monitor
  
5. Install all required python apps:
  
    pip install -r requirements/apps.txt

6. Create the database:
  
    createdb service_monitor
  
7. Copy and configure localsettings.py:
  
    cp localsettings.py.example localsettings.py
  
8. Setup the database:
  
    python manage.py syncdb --settings localsettings
  
9. Run each of the following commands in separate console windows (don't forget to `workon service-monitor` in each console):
  
    python manage.py runserver 0.0.0.0:8080 --settings localsettings
    python manage.py runrouter --settings localsettings
    python manage.py celeryd --settings localsettings
    python manage.py celerybeat --settings localsettings

Usage
=====
All services to monitor are specified as Service objects. To monitor another service, create another Service object by going to the admin interface:

* To create an SMS Service, fill out the following information:

1. Name - This is the name that will show up in notification emails.
2. Service Type - Select "SMS".
3. Connection - Select the RapidSMS Connection object associated with the gateway to monitor. If none exists, create one by clicking on the "+" and filling out the appropriate fields. There is no need to create a RapidSMS Contact for this Connection.
4. SMS to Send - This is the SMS that will be sent to monitor gateway responsiveness.
5. Valid Response Regex - Optionally, a regular expression used to validate the response from the gateway. If blank, any response is considered valid.
6. Email list - A pipe-delimited list of recipients of the notification emails for this service.
    
* To create an HTTP Service, fill out the following information:

1. Name - This is the name that will show up in notification emails.
2. Service Type - Select "HTTP".
3. Url - The url to invoke when checking for uptime.
4. Email list - A pipe-delimited list of recipients of the notification emails for this service.

Design Overview
===============
The Service Monitor primarily relies on three apps:
    * RapidSMS
    * Django-scheduler
    * The monitor app bundled in this repository

The data model of the monitor app consists of two main entities: the Service, and the PingLog. Each service to monitor is created as a separate Service object, and the PingLog simply contains one entry for each request sent, response received, and timeout processed.

For SMS services, every minute, a task runs to see if the proper wait time has passed to send another ping request to the service and sends it accordingly. Or, if a request has already been sent and no valid response has been received, the task checks to see if the timeout interval has passed and sends a notification email accordingly.

For HTTP services, the same task checks to see if the proper wait time has passed to send another ping request to the service and sends it accordingly. The timeout is processed as an Exception raised when trying to open the URL.

To configure the two intervals mentioned above, set the following constants in localsettings.py:

 * SERVICE_MONITOR__PING_INTERVAL
   
   This is the number of minutes to wait between sending requests to each service.
 
 * SERVICE_MONITOR__WAIT_TIME
 
   This is the number of minutes to wait before considering an unresponsive service as being timed out, for both SMS and HTTP services.

