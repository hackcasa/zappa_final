# pim-web

New PIM web and RESTful interface

## Activate the virtual environment in the ec2 instance

Run ansible to find out which ec2 instances are active

```
ansible "*" -m ping -l tag_Stack_pim_web
```

(or in the aws web console)

ssh to the host (with the key as ec2-user)

```
ssh ec2-user@<host>
```

In the host, activate the env and cd into the root of the project

```
source /venvs/pim/bin/activate && cd /var/www/pim

```

## Run the django shell

complete steps above, then

```
./manage.py shell
```

The django shell prompt is presented

```
>>> from web.models import
```

Now you can do all of the DB stuff from the shell, for example count how many articles there are.

```
Article.objects.count()
```

## Local development config

Create pim/local_settings.py, it should contain `from pim.settings import *` and any settings you want to override.
Then start the server with:

```
export DJANGO_SETTINGS_MODULE=pim.local_settings
python3 manage.py runserver
```
