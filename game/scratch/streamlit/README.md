# AIND Neuroglancer Game


This folder is to test the Neuroglancer Python Integration within a streamlit app.

There are 2 ways we are exploring to embed Neuroglancer in our game:
1. Use an iframe to load a dataset from an external deployment of Neuroglancer
2. Use the Neuroglancer Python integration to create new Neuroglancer Viewers in the same environment as the streamlit app.

This folder explores option #2. You can load a state from an external url, or provide the s3 location of a config file, or load an example (from hackathon) state from json.


## Installation
```
pip install -r requirements.txt
```

## Start the streamlit app
```
streamlit run streamlit_app.py
```