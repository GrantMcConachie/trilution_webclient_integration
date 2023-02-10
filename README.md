# trilution_webclient 
RESTful API for Gilson's Trilution software.<br>
A flask app API with a dash app and a webpage hosted on it as well.

## Instructions
```shell
#clone
git clone https://github.com/GrantMcConachie/trilution_webclient_integration.git

#cd into directory
cd trilution_webclient_integration

#make virtual environment
python -m venv .venv

#activate virtual environment
source .venv/Scripts/activate

#install libraries
pip install -r requirements.txt

#start app
set FLASK_APP=main.py
flask run
```

## Things to check out
Unforturnately some capabilities of this API requires you to be on a specific NIH wifi, so somethings will not work as expected. However, here are some urls to look at that can give you an idea of what the webclient can do:
<br><br>
http://localhost:5000/gilson_REST/doc - for documentation on the API<br>
http://localhost:5000/gilson_REST/webfront/GILSON_{#} - change {#} to 4, 5, or 6 to see method list for different intstruments<br>
http://localhost:5000/standardapp/GILSON_{#} - change {#} to 4, 5, or 6 to see different standards for each gilson.<br>
