import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import database
from . import decorators
from . import app
from .database import session, Song, File
from .utils import upload_path

schema = {
    "properties": {
        "file": {
            "filename": {"type": "string"}
        }
    },
    "required": ["file"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def get_songs():
    """ Retrieve a list of all songs in the database """
    
    all_songs = session.query(Song).all()
    list = json.dumps([song.as_dictionary() for song in all_songs])
    
    return Response(list, 200, mimetype="application/json")

@app.route("api/songs/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def get_song(id):
    """ Retrieve one song in the databae using its id """
    
    song = session.query(Song).filter(id == id)
    
    if not song:
        message = "Sorry there is no song with the id {} in our database".format(id)
        message = json.dumps({{"message": message}})
        return Response(message, 404, mimetype="application/json")
    
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def post_song():
    """ Post a new song to the database """
    
    song = request.json
    
    try:
        validate(song, schema)
    except ValidationError as error:
        data={"message": error.message}
        return Response(json.dumps(song), 422, mimetype="application/json")
    
    file = database.File(id=song["file"]["id"], name=song["file"]["name"])
    song = database.Song(id=song["id"], file=file)
    
    session.add(song)
    session.commit()
    
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("get_song", id=song.id)}
    return Response(data, 404, mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["DELETE"])
@decorators.accept("application/json")
def delete_song(id):
    """ Delete a song from the database """
    song = session.query(Song).filter(id==id)
    
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
    
    session.delete(song)
    session.commit()

# write an endpoint for edits

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(name):
    return send_from_directory(upload_path(), name)

@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")

    name = secure_filename(file.name) 
    file = File(name=name)
    
    session.add(file)
    session.commit()
    file.save(upload_path(name))
    
    data = file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")
    
    
    
    