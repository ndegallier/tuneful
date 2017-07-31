import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO, BytesIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session, File, Song

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())
    
    def test_get_songs(self):
        """ Get songs from database """
        
        file1 = File(name="1.mp3")
        file2 = File(name="2.mp3")
        song1 = Song(file=file1)
        song2 = Song(file=file2)
        
        session.add_all([song1, song2])
        session.commit()
        response = self.client.get("/api/songs", headers=[("Accept", "application/json")])
        
        self.assertEqual(response.status_code, 200)
    
    
    def test_get_song(self):
        """ Retrieve a song """
        file1 = File(name="1.mp3")
        file2 = File(name="2.mp3")
        song1 = Song(file=file1)
        song2 = Song(file=file2)
        
        session.add_all([song1, song2])
        session.commit()
        
        response = self.client.get("/api/songs/{}".format(song1.id), headers = [
            ("Accept", "application/json")]
        )
        self.assertEqual(response.status_code, 200)
    
    def test_song_post(self):
        """ Post a song """
        data = {
            "id": 1,
            "file":{
                "id": 1,
                "name": "1.mp3"
            }
        }
        
        response = self.client.post("api/songs",
            data = json.dumps(data),
            content_type = "application/json",
            headers = [("Accept", "application/json")])
        
        self.assertEqual(response.status_code, 201)
    
    def delete_song(self):
        """ Delete a song """
        file1 = File(name="1.mp3")
        song1 = Song(file=file1)
        
        session.add(song1)
        session.commit()
        
        response = self.client.delete("/api/songs/{}".format(song1.id), headers=[("Accept", "application/json")])
        
        self.assertEqual(response.status_code, 200)
    
    def test_get_uploaded_file(self):
        path =  upload_path("test.txt")
        with open(path, "wb") as f:
            f.write(b"File contents")

        response = self.client.get("/uploads/test.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, b"File contents")
        
    def test_file_upload(self):
        data = {
            "file": (BytesIO(b"File contents"), "test.txt")
        }

        response = self.client.post("/api/files",
            data=data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")

        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as f:
            contents = f.read()
        self.assertEqual(contents, b"File contents")