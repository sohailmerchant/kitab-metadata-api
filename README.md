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
      |- apps.py: a two-line class is created here for the configuration of the app, 
           which is given the name "api"
      |- models.py: in this file, the models (~ tables) are created.
      |- models-v2.py: older version of models.py?
      |- serializers.py: define serializers (which dictate what fields are exposed 
           through the endpoints): AuthorNameSerializer, VersionMetaSerializer, 
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
      |- urls.py: contains only variable `urlpatterns`
      |- wsgi.py: settings for deployment using WSGI 
           (see https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/)
```

# Useful commands:

After changes in the Model you will need to make the migration with the following command

```
python3 manage.py makemigrations
```

After the you have created migration you will have to migrate the changes to the database

```
python3 manage.py migrate
```

To run the django server:

```
python3 manage.py runserver
```

`load_data` is the management command - with the file name load_data.py.  Located in Management\Commands folder

```
python3 manage.py load_data 
```

You can delete all the migration by deleting all the files in kitab\api\migrations (except init.py).

After you have deleted / created a database, you must create a superuser:

```
python3 manage.py createsuperuser
```

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
