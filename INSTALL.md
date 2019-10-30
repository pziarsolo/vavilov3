
INSTALLATION
------------

Steps to install  Vavilov3

Previous Notes
-------------
The application is made in python3, minimun required version being 3.5

  
Important files
--------------------
    In the vavilov3_web directory you can find and example directory of a django project with almosta all needed configurations.

Steps
--------------

1) install
7) Configurar la base de datos de progress:
    En el fichero settings.py del projecto crf tenemos la informacion de accesso a la base de datos:

    DATABASE: {
        'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'crf_db',
                'USER': 'crf_user',
                'HOST': 'localhost',
                'PASSWORD': 'crf_pass'}}

    Necesitamos un usuario y una base de datos  que coincidan con los nombre que aquí pongamos. 
    Se pueden modificar, si la base de datos está en remoto, tambien se puede configurar. 
    El usuario tiene que poder escribir en la base de datos. 
    Si quieres poder correr tests unitarios de la aplicacion tambien tiene que ser capaz de crear bases de datos(-d)
        
        Con el ususario administrador que tengais. En el caso de debian es postgres teneis que correr los comandos siguientes.
        $ createuser -U postgres -d crf_user -P
        $ createdb -U postgres --owner crf_user crf_db


10) Inicializar la base de datos:
    $ cd crf/crf_web
    $ source $VIRTUALENV_DIR/bin/activate

    # crea la base de datos vacia
    $ ./manage.py migrate
 
    # Añade datos minimos que necesita a base de datos. El fichero user ha de tener un usuario admin al menos.
    Para ser admin tiene que pertenecer al grupo admin. 
    
    $ ./manage.py initialize_db -u ~/users.csv
    
    El formato del fichero de usuarios es(Una cabecera y luego una linea por usuario):

username,mail,password,group
admin,p@example.com,tomate..,admin


15) Configurar Celery:
    Hay que poner a correr celery como un daemon. Existen varias formas de hacerlo, pero en todas ellas hay que configurar el worker en conjunto con la configuracion de django.
    
    El el proyecto crf en la carpeta deployment teneis un par de fichero para configurarlo en debian con el sistema de inicio sysvinit.
    
    1) teneis que crear un usuario y grupo celery. Necesita tener una shell activa.
    2) Teneis que adecuar los ficheros de configuracion. Hay rutas que hay que cambiar.
    3) En debian hacer los links en los directorios que toca. Para saber la ruta hay que cambiar los "_" por "/"
    4) Una vez lo tengais todo preparado, iniciais el celery como demonio y todo deberia funcionar 

It requires to have a working postgres database. Configuration
