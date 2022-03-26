# After changes in the Model you will need to make the migration with the following command
python3 manage.py makemigrations

# After the you have created migration you will have to migrate the changes to the database
python3 manage.py migrate

# To run the django server
python3 manage.py runserver

# load_data is the management command - with the file name load_data.py.  Located in Management\Commands folder
python3 manage.py load_data 

# You can delete all the migration by deleting all the files except init.py.  Located in kitab\api\migrations

# create superuser after you have deleted / new a database
python3 manage.py createsuperuser

# To create a shell in the application
python3 manage.py shell


# TO DO

- Check model for required field - ensure if field is not required we change it
- Find the way to deal with Person relation
- At the load, populate aggregatedstats data e.g. number of authors, number of versions, etc...
- Search and Filter on the endpoints
- Find a way to update the database dynamically everyday without the downtime
- New database per version and upload the data
