# CBWebReader 

CBWebReader is web-based CBR and CBZ file reader implemented in Django. The application allows a user to host their collection of digital comics (CBR & CBZ formats) as a remotely accessible collect.

![CBWebReader Screenshot](assets/cbwebreader.jpg)

## Core technologies

The following technologies will aid development by ensuring a consistent development environment for all developers:

- [docker](https://www.docker.com/get-started)
- [docker-compose](https://docs.docker.com/compose/gettingstarted/)

The following frameworks and tool's are used within the application:

- [Django 2.0](https://www.djangoproject.com/)
- [python 3.5+](https://www.python.org/)
- [rarfile python library by Marko Kreen](https://github.com/markokr/rarfile) (included)
- [Unrar by winrar](http://rarlabs.com)
- [django-recaptcha by praekelt](https://github.com/praekelt/django-recaptcha)

## Getting started

The CBWebReader is a Django project and follows the standard conventions for a Django application. To get started, clone the project into your workspace:

```bash
git clone https://github.com/ajurna/cbwebreader
```

Configure the environment using the `.env` file or setting each variable within your environment:

```bash
cp .env.example .env
```

Alternatively, set the path to your `COMIC_BOOK_VOLUME` like so:

```bash
export COMIC_BOOK_VOLUME=some_path_to_comics_directory
```

Build and run the project using docker-compose:

```bash
docker-compose build
docker-compose up
```

## Running Tests

To run the entire test suite for CBWebReader, execute the following command:

```bash
docker-compose run app pytest -vvv
```

## Syncing comic books

Once the application has been configured and runs for the first time, an initial import of comics will be made available to browse and view. However, future additions will need to be synced before they will be available. A sync can be performed by running the following command:

```bash
docker-compose run app python manage.py scan_comics
```

It is recommended that you configure a scheduled task to run the sync as frequently as you wish to ensure your collection is up-to-date.

## License

This is a [human-readable summary](https://creativecommons.org/licenses/by-sa/4.0/) of (and not a substitute for) the [Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) License]("https://creativecommons.org/licenses/by-sa/4.0/legalcode").
