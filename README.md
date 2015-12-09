# Pinax Dashboard

A dashboard to display point-in-time and interval metrics about the Pinax
Project, in addition to other metadata like release histories.

## Getting Started

Make sure you are using a virtual environment of some sort (e.g. `virtualenv` or
`pyenv`).

```
pip install -r requirements.txt
./manage.py migrate
./manage.py loaddata sites
./manage.py runserver
```
