# HuntedBackend
Backend for a Hunted-inspired android app for an activity by the Dies Committee of I.C.T.S.V. Inter-Actief

## Use virtual environment

Linux: `venv/bin/activate`

Windows: `venv\Scripts\activate`

## Run application

`python app.py`

## Using Docker
You can build the docker image using `docker build -t inter-actief/hunted .`

After this you can run the container using   
`docker run -v "$(pwd)"/hunted.db:/usr/src/app/hunted.db -p 5000:5000 inter-actief/hunted`