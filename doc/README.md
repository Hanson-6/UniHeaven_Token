# UniHaven Project - Prerequisites

This document lists the necessary tools and environments required to set up and run the UniHaven Django project.

**_Product Backlog in [link](https://connecthkuhk-my.sharepoint.com/:x:/r/personal/u3614020_connect_hku_hk/Documents/COMP3297_group_H/UniHavenProductBacklog.xlsx?d=wd19a06ffc0514ee78adab6678f45ef03&csf=1&web=1&e=R25qEb)_**

## Table of Contents
- [Software Version](#software-version)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Installation Instructions](#installation-instructions)
- [Git Management guideline](#git-management-guideline)
  - [Pipfile vs requirements.txt](#pipfile-vs-requirementstxt)

# Software Version

- Python 3.13.2
- Django 5.1.7

# Project Structure
```bash
unihaven/
├── core/              # Main Django app (models, views, templates, static, etc.)
│   ├── admin.py
│   ├── apps.py
│   ├── authentication.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── signals.py
│   ├── test_api.py
│   ├── test_models.py
│   ├── urls.py
│   ├── utils.py
│   ├── views.py
│   ├── templates/
│   │   └── core/      # html files
│   │       └── home.html
│   ├── static/
│   │   └── core/
│   │       ├── css/   # css files
│   │       │   └── home.css
│   │       └── js/    # js files
│   │           └── home.js
├── project/              # Project configuration (settings, URLs)
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py          # Django project management tool
├── requirements.txt   # Dependency list for pip
└── schma.yaml
```

# Installation Instructions
Follow the steps below to set up the project on your machine:

### 1. Clone the Repository
```bash
git clone <github-repo-url>
cd unihaven
```

### 2. Create a Virtual Environment
Use `venv` to isolate dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # For macOS/Linux
venv\Scripts\activate     # For Windows
```

### 3. Install Dependencies
Install all required Python packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Apply Migrations
Set up the database schema:
```bash
python manage.py makemigrations # run the commonds after every modifications to the model
python manage.py migrate
```

### 5. Run the Development Server
```bash
python manage.py runserver
```

# Documentation

a folder (doc) for putting the non-code info inside the project

- Markdown files
  - `README`

# Git Management guideline

## General Rules of `Branch`

1. `Fetch` (check for updates) and `pull` (update local) before working
2. **_NEVER_** directly committ to `main`, unless 100% complete
3. Create and Work on the `branch` based on Epic in the Project Backlog
4. Before commit
    1. Update dependencies

## Installing Dependencies After Pulling from Git
If you're using `requirements.txt`
```bash
# Set up / activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```
If you're using `Pipfile`
```bash
pipenv install -r requirements.txt
pipenv shell            
```
## Updating Dependencies Before Pushing to Git
Make sure to update `requirements.txt`
With `pip`
```bash
pip freeze > requirements.txt
```
With `pipenv`
```bash
pipenv requirements > requirements.txt
```

## Running the testcoverage for API endpoints
```bash
coverage run --source='core' --branch manage.py test core
coverage report -m
coverage html
```

# Detailed List of Additions Made After the April 30 Review
## Authentication
+ The API uses token-based authentication for universities:
    
  - Each university has a unique token that must be included in the Authorization header.  
  Format: `Authorization: Token <university_token>`
  - The token will generate randomly each time when creating a university.


## Email Backends
+ When a student reserves a accommodation, cancels a reservation and signs a contract, UniHeaven will automatically send an email to the specialist group of the university where the student is located.

  + For development and testing purposes, this project implements Django's Console Email Backend to elegantly simulate email delivery. 


## Rating
+ Change the rating range from 1 to 5 to 0 to 5.

## Testcase
+ Added token-based authentication for university entities
+ Added extensive test coverage for AvailabilitySlot objects

## Domain Model
+ Remove unnecessary attributes which already shown by relation