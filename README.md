Vavilov3
-------

Vavilov3 is django rest API application. It can deal with passport and phenotyping data.

It contains the application and an example python project with all the configurations needed.

INSTALLATION
------------

Vavilov3 folder must be in the python path.

1) Install all requeriments:
    pip install -r requeriments

2) It needs a celery worker running in order to be able to add data in bulk.
This celery worker configuration must be in your django project, side by side with your project settings.
In the vailov3_web folder
    2a) Got To your DJANGO PROJECT  and run:
        celery worker -A PROJECT_NAME  -l info
    2b) Install cellery and make it run as a system service. Configure the worker with the given configuration




It requires to have a working postgres database. Configuration