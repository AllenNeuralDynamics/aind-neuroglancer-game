# AIND Neuroglancer Game

This folder contains a POC for a Python-based Neuroglancer Game. The game runs as a Streamlit app with the Neuroglancer Python Integration.

When a game is launched, the app creates new Neuroglancer Viewers in the same environment as the Streamlit app.

For the POC, here are some features we would like to implement:
- Loading and saving annotations to S3
- Loading and saving previous game stats from a database
- Single Player Mode: timed mode using 1 pre-configured dataset
- Single Player Mode: with Accuracy calculation
- Leaderboard
- Login and user profiles with history
- Stretch: multiple pre-configured datasets for users to choose from
- Stretch: Multi-Player Mode

## Installation
```sh
pip install -r requirements.txt
```

## Start the streamlit app
```sh
streamlit run streamlit_app.py
```

## Run using Docker

```sh
docker build -t aind-neuroglancer-game .
docker run -p 8501:8501 -p 8080:8080 aind-neuroglancer-game
```