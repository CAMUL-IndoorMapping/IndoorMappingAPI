# IndoorMappingAPI

## Setup environment

1. Install python 3.x

windows:
```bash
https://www.python.org/downloads/
```

linux debian:
```bash
sudo apt-get update
sudo apt-get install python3.10
```

if it doesn't work, try this instead:
```bash
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.8
```

also, for Fedora:
```bash
sudo dnf install python3
```

2. Clone repository
come on, não vou explicar esta parte

3. Create a virtual environment
Virtual environment is important to be created to store all required packages:
```bash
python3 -m venv venv
```

4. Enter virtual environment (this step must be done everytime we need to work in our API)

Note: run this code inside directory

windows:
```bash
venv\Scripts\activate.bat
```

linux/mac:
```bash
source venv/bin/activate
```

5. Install required packages

Note: run this everytime 'requirements.txt' gets updated

```bash
python3 -m pip install -r requirements.txt
```

## Run API server
1. Enter virtual environment

Note: run this code inside directory

windows:
```bash
venv\Scripts\activate.bat
```

linux/mac:
```bash
source venv/bin/activate
```

2. Start server
```bash
python3 app.py
```

3. Connect to server

To test the API you should get installed POSTMAN desktop app, ou just use your browser. POSTMAN has more features, like post parameters and headers definition, which will be mandatory for our project.