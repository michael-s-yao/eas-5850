# Instructions for Reproducing Homework 2

1. Install Docker following the instructions [here](https://docs.docker.com/engine/install/).
2. Run the following commands in the terminal:

```
docker run -p 4242:4242 -p 8042:8042 --rm -v ~/path/to/eas-5850/hw2/orthanc.json jodogne/orthanc:1.12.3
```

3. Navigate to `http://localhost:8042/app/explorer.html` in your browser and upload the imaging studies found [here](https://drive.google.com/drive/folders/1oHJbMwaN3Y0mxPkwEJ1jZpq-wNRhQURE?usp=sharing)
4. In a separate terminal instance, run the following commands:

```
conda env create -f environment.yml
conda activate
cd hw2
python main.py
```