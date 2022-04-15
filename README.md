

Django REST API documentation: https://www.django-rest-framework.org/tutorial/1-serialization/

# Django folder structure:

```
kitab-metadata-api
  |- README.md: this document
  |- db.sqlite3: the database that contains the API's data
  |- manage.py: the top-level script that must be called 
       for all API actions (see below)
  |- api
      |- management
          |- commands: 
              |- load_data.py: this script loads all data 
                   from the metadata csv file to the database
              |- create_dummy_aggregate_data.py: this scripts loads 
                   some dummy data to the AggregatedStats model
      |- migrations: 
          |- ...: the migrations folder contains a file 
               for each of the migrations (= changes to the database model) made
      |- admin.py: the models are registered in this file
           so they can be accessed from the admin panel (?)
      |- apps.py: a two-line class is created here for the configuration of the app, 
           which is given the name "api"
      |- models.py: in this file, the models (~ tables) are created.
      |- models-v2.py: older version of models.py?
      |- serializers.py: define serializers (which create JSON representations
           of the data in the database): 
           AuthorNameSerializer, VersionMetaSerializer, 
           TextSerializer, AuthorMetaSerializer, AggregatedStatsSerializer
      |- tests.py: (empty file)
      |- urls.py: creates endpoint URLs, each connected with a specific view 
           (see views.py)
      |- utility.py: contains utility functions for loading the data: 
           read_json(), bulk_load()
      |- views.py: a class is created per page view (endpoint), 
           each of which get their own url in urls.py; 
           each view uses a serializer defined in serializers.py
  |- kitab
      |- asgi.py: settings for deployment using ASGI 
           (see https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/)
      |- settings.py: contains settings for Django 
           (incl. pagination, throttle, ...)
      |- urls.py: contains urls for all apps in the application; 
           partly duplicates api/urls.py.
      |- wsgi.py: settings for deployment using WSGI 
           (see https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/)
```

# Useful commands:

## Virtual environment:

**After installation, first make a virtual environment:**

If virtualenv is not installed, install it first: 

```
py -3.8 –m pip install virtualenv
```

Create the virtual environment: 

```
py -3.8 –m virtualenv -p <link_to_your_python.exe> my_django_environment
```


Activate the virtual environment: 

```
my_django_environment\Scripts\activate
```

Install django, djangorestframework and other libraries inside the activated virtual environment
using the requirements.txt file in the kitab-metadata-api folder: 

```
pip3 install -r requirements.txt
```


## Django: 

** always make sure the virtual environment is activated!**

### Creating a new Django app - this was already done by Sohail!

Running the command `django-admin startproject <project_name>` will set up a folder 
with the name <project_name>, in which you'll find a manage.py file, a database (db.sqlite3) 
and another folder called <project_name>, which contains some settings files
(the "kitab" folder in the kitab-metadata-api folder 
is this folder that was automatically created by the django-admin startproject command).

Test if this worked by running the server: 

```
mkdir django_test
cd django_test
django-admin startproject mytestsite
cd mytestsite
python manage.py runserver
```

If you go to http://127.0.0.1:8000/ , the test server should be running.

You can now run the following function to create a new app: 

```
python manage.py startapp <app_name>
```

This will create a folder with the name <app_name>, which contains
the scaffolding for your app: 
- admin.py
- apps.py
- models.py
- tests.py
- views.py
- migrations folder

(in our API, this app folder is called "api" )

Finally, create a superuser to access the database: 

```
python manage.py createsuperuser
```

### Useful Django commands:

**All commands should be run from the kitab-metadata-api folder.**

**Always make sure the virtual environment is activated!**

```
my_django_environment\Scripts\activate
```

#### Running the server locally:

To run the django server locally:

```
python3 manage.py runserver
```

You will now be able to access the api on http://127.0.0.1:8000/ 

#### Migrations

After any change in the models.py file, you will need to make a migration (= apply these changes) with the following commands:

```
python3 manage.py makemigrations
python3 manage.py migrate
```



To run the django server:

```
python3 manage.py runserver
```

# load data from the metadata csv:

`load_data` is the management command - with the file name load_data.py.  Located in Management\Commands folder

```
python3 manage.py load_data 
```

# delete the database

You can delete all the migration by deleting all the files in kitab\api\migrations (except init.py), and the database itself (db.sqlite3).

After you have deleted / created a database, you must create a superuser:

```
python3 manage.py createsuperuser
```

# 

To create a shell in the application, from which you can query the api:

```
python3 manage.py shell
```

# TO DO

- Check model for required field - ensure if field is not required we change it
- Find the way to deal with Person relation
- At the load, populate aggregatedstats data e.g. number of authors, number of versions, etc...
- Search and Filter on the endpoints
- Find a way to update the database dynamically everyday without the downtime
- New database per version and upload the data
