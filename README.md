Vavilov3
-------

Vavilov3 is django rest API application. It is made to deal with passport and phenotyping data.

It contains the application and an example python project with all the configurations needed.


INSTALLATION
------------

Pasos para instalar vavilov3

Notas previas
-------------

La aplicacion  esta hecha con python3, la version minima que funciona es python3.5

Para poder instalarlo necesitamos 2 "paquetes de python":
    a) por un lado una "aplicacion/project django" llamada "crf" que contiene informacion especifica sobre la pagina web del crf y que es la que usara la aplicacion vavilov3.
    a) Por otro lado la aplicacion de django vavilov3. Esta es una aplicacion generica para manejar datos de pasaporte y phenotipado via REST API.
    

Ficheros importantes
--------------------
    El el projecto crf hay un fichero settings.py en el directorio crf_web. 
    En este fichero se configura tanto el projecto de django como la aplicaion VAVILOV3
    
    En el projecto crf tambien hay una carpeta deployment con archivos de ejemplo para configurar tanto el apache como el celery.

Pasos a seguir
--------------

1) Instalar las dependencias (debian):

    $ sudo apt install git python3-venv libpq-dev build-essential python3-dev apache2 libapache2-mod-wsgi-py3 rabbitmq-server postgres

2) Crear un entorno virtual de python3

    $ python3 -m venv $VIRTUALENV_DIR

3) Descargar vavilov3 en el virtualenv:

    $ git clone ssh://git@github.com:pziarsolo/vavilov3.git

4) Descargar el projecto crf en el virtual env:
    $ git clone ssh://git@gitlab.comav.upv.es:2203/bioinf/crf


5) Para que cuando nos metamos en el "virtualenv" y tengamos acceso a los modulos vavilo3 y crf, tenemos que añadirlos al PYTHONPATH del virtualenv.
Para ello tenemos que adecuar el fichero activate del virtualenv. De esta forma podremos ejecutar los tests unitarios y ver que todo funciona.

Añadir el PYTHONPATH de las dos librerias que hemos instalado(Añade estas dos lineas al fichero $VIRTUALENV_DIR/bin/activate  adecuando las rutas a tu instalacion):

    PYTHONPATH="$PYTHONPATH:/home/jope/devel/vavilov3:/home/jope/devel/crf"
    export PYTHONPATH


6) Entramos en el entorno virtual e instalamos requisitos para correr vavilov3:
    $ source $VIRTUALENV_DIR/bin/activate
    $ pip install -r vavilov3/requeriments.txt


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

8) cambiar el SECRET_ID en el archivo de configuracion settings.py del projecto del django de CRF.

9) En este momento ya podemos hacer algunos test unitarios para ver si vamos por buen camino.

    $ cd crf/crf_web
    $ source $VIRTUALENV_DIR/bin/activate
    $ ./manage.py test vavilov3

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

11) Configurar apache:
    El la carpeta deployment del projecto crf tenemos La configuracion para un virtualenv con todos los configuraciones necesarias:
    Adecua los path necesarios:
        1) donde guardas los Static files -> sincronizado con settings.py del projecto crf
        2) donde guardas los media files -> sincronizado con settings.py del projecto crf
        3) Configuracion del python path:
           WSGIDaemonProcess URL_ID python-path=/home/jope/devel/crf/crf_web:/home/jope/devel/vavilov3:/home/jope/devel/lib/python3.5/site-packages
          
        4) WSGIProcessGroup URL_ID => el URL_ID es un identificador par el grupo. Puedes poner la url que vas a utilizar.
            
        5) Path al fichero wsgi.py. Es el script que va a inicializar la aplicacion
           En este fichero hay rutas a las librerias y tendremos que actualizarnas a nuestro entorno. 
           WSGIScriptAlias / /home/jope/devel/crf/crf_web/crf_web/wsgi.py

12) Tenemos que echar un ojo a la configuracion del projecto. En el fichero settings.py tambien tenemos algunas configuraciones que tendremos que actualizar, dependiendo de nuestro entorno:
    ALLOWED_HOSTS
    CORS_ORIGIN_WHITELIST

13) Si ya has configurado los directorios static en el projecto puedes recolectar los ficheros de las aplicaciones y ponerlos en el directorio static:
    $ cd crf/crf_web
    $ ./manage.py collectstatic

14) Si todo ha ido bien, puedes cambiar el DEBUG=True de settings.py por DEBUG=False

15) Configurar Celery:
    Hay que poner a correr celery como un daemon. Existen varias formas de hacerlo, pero en todas ellas hay que configurar el worker en conjunto con la configuracion de django.
    
    El el proyecto crf en la carpeta deployment teneis un par de fichero para configurarlo en debian con el sistema de inicio sysvinit.
    
    1) teneis que crear un usuario y grupo celery. Necesita tener una shell activa.
    2) Teneis que adecuar los ficheros de configuracion. Hay rutas que hay que cambiar.
    3) En debian hacer los links en los directorios que toca. Para saber la ruta hay que cambiar los "_" por "/"
    4) Una vez lo tengais todo preparado, iniciais el celery como demonio y todo deberia funcionar 

It requires to have a working postgres database. Configuration