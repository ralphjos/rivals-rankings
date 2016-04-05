Overview
========

Application server for the Rivals of Aether rankings project.

- Simple flask server
- Gulp and package.json for Browsersync

Setup
=======
Create a new virtual environment for your application

```
virtualenv venv
```

Activate the virtual environment

```
source venv/bin/activate
```

Add local environment variables

```
source environment_variables
```

Make sure you have pip, node, and npm installed, then cd into the root directory of this project and run:

```
pip install -r requirements.txt
npm install
```

To run the application with Browsersync
run `gulp`