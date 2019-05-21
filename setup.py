from flask import Flask
from flask_pymongo import PyMongo
from flask import request
import json
from bson import ObjectId
from bson.json_util import dumps
import client2
import requests

app = Flask(__name__)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
app.config["MONGO_URI"] = "mongodb://atpos_user:atpos_password@cluster0-shard-00-00-j6ym9.mongodb.net:27017,cluster0-shard-00-01-j6ym9.mongodb.net:27017,cluster0-shard-00-02-j6ym9.mongodb.net:27017/clientes?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true"
mongo = PyMongo(app)
users = mongo.db.users


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


@app.route('/cliente/', methods=['POST', 'DELETE', 'GET'])
def cliente():
    x = requests.post("http://157.230.14.37:8001/api/token-auth/", json={"cc": 1234, "password": 5})
    arr = client2.validate_token(json.loads(x.text)["token"])
    if arr.get("error", False) is True:
        response = json.dumps({'message': 'Token invalido'})
        return response, 400
    if request.method == 'POST':
        if arr["user"]["is_admin"] is True | arr["user"]["rol_administrador"] is True | arr["user"]["rol_cajero"] is True:
            data = request.get_json()
            username = data.get("usuario", "")
            usuario = users.find_one({"usuario": username})
            if usuario is None:
                id_user = users.insert(data)
                return JSONEncoder().encode(users.find_one({"_id": id_user}))
            else:
                response = json.dumps({'message': "Ya existe un cliente con el usuario: %s" % username})
                return response
        else:
            response = json.dumps({'message': "No tiene los permisos suficientes para crear el usuario de un cliente"})
            return response, 403
    elif request.method == 'DELETE':
        if arr["user"]["is_admin"] is True | arr["user"]["rol_administrador"] is True | arr["user"]["rol_cajero"] is True:
            data = request.get_json()
            username = data.get("usuario", "")
            usuario = users.find_one({"usuario": username})
            if usuario is None:
                response = json.dumps({'message': "No existe un cliente con el usuario %s" % username})
                return response, 404
            else:
                users.delete_one({"usuario": username})
                response = json.dumps({'message': "El cliente con el usuario %s fue Eliminado exitosamente" % username})
                return response
        else:
            response = json.dumps({'message': "No tiene los permisos suficientes para eliminar el usuario de un cliente"})
            return response, 403
    elif request.method == 'GET':
        if arr["user"]["is_admin"] is True | arr["user"]["rol_administrador"] is True | arr["user"]["rol_cajero"] is True:
            data = request.get_json()
            puntos = data.get("puntos", 0)
            if type(puntos) is not int:
                data.pop("puntos")
                for key in puntos.keys():
                    if key == "menor":
                        query = {"puntos": {"$lte": puntos.get(key)}}
                    elif key == "mayor":
                        query = {"puntos": {"$gte": puntos.get(key)}}
                    else:
                        vals = puntos.get(key)
                        query = {"puntos": {"$lte": vals[1]}}
                        data.update(query)
                        menores = users.find(data)
                        resp = []
                        for men in menores:
                            if men["puntos"] >= vals[0]:
                                resp.append(men)
                        return JSONEncoder().encode(resp)
                    data.update(query)
            usuarios = users.find(data)
            return dumps(usuarios)
        else:
            response = json.dumps({'message': "No tiene los permisos suficientes para buscar el usuario de un cliente"})
            return response, 403


@app.route('/cliente/editar/<username>', methods=['PUT'])
def modificarCliente(username):
    x = requests.post("http://157.230.14.37:8001/api/token-auth/", json={"cc": 1234, "password": 5})
    arr = client2.validate_token(json.loads(x.text)["token"])
    if request.method == 'PUT':
        if arr["user"]["is_admin"] is True | arr["user"]["rol_administrador"] is True:
            data = request.get_json()
            user = users.find_one({"usuario": username})
            if user is None:
                response = json.dumps({'message': "El cliente con usuario %s no existe" % username})
                return response, 404
            else:
                new_username = ""
                for key in data.keys():
                    if key != "usuario":
                        query = {key: data.get(key)}
                        users.update_one({"usuario": username}, {"$set": query})
                    else:
                        new_username = data.get(key)
                if new_username != "":
                    users.update_one({"usuario": username}, {"$set": {"usuario": new_username}})
                    return JSONEncoder().encode(users.find_one({"usuario": new_username}))
                else:
                    return JSONEncoder().encode(users.find_one({"usuario": username}))
        else:
            response = json.dumps({'message': "No tiene los permisos suficientes para modificar el usuario de un cliente"})
            return response, 403


@app.route('/cliente/agregarPuntos', methods=['PUT'])
def agregarPuntos():
    x = requests.post("http://157.230.14.37:8001/api/token-auth/", json={"cc": 1234, "password": 5})
    arr = client2.validate_token(json.loads(x.text)["token"])
    if request.method == 'PUT':
        if arr["user"]["is_admin"] is True | arr["user"]["rol_administrador"] is True | arr["user"]["rol_cajero"] is True:
            data = request.get_json()
            username = data.get("usuario", "")
            puntos = data.get("puntos", 0)

            user = users.find_one({"usuario": username})
            if user is None:
                response = json.dumps({'message': "El cliente con usuario %s no existe" % username})
                return response, 404
            else:
                puntos_user = user["puntos"]
                total = puntos_user + abs(puntos)
                users.update_one({"usuario": username}, {"$set": {"puntos": total}})
                response = json.dumps({'message': "Se agrego exitosamente %s puntos al cliente con usuario %s" % (abs(puntos), username)})
                return response
        else:
            response = json.dumps({'message': "No tiene los permisos suficientes para agregar puntos al usuario de un cliente"})
            return response, 403

@app.route('/cliente/canjearPuntos', methods=['PUT'])
def canjearPuntos():
    x = requests.post("http://157.230.14.37:8001/api/token-auth/", json={"cc": 1234, "password": 5})
    arr = client2.validate_token(json.loads(x.text)["token"])
    if request.method == 'PUT':
        if arr["user"]["is_admin"] is True | arr["user"]["rol_administrador"] is True | arr["user"]["rol_cajero"] is True:
            data = request.get_json()
            username = data.get("usuario", "")
            puntos = data.get("puntos", 0)

            user = users.find_one({"usuario": username})
            if user is None:
                response = json.dumps({'message': "El cliente con usuario %s no existe" % username})
                return response, 404
            else:
                puntos_user = user["puntos"]
                if puntos_user >= abs(puntos):
                    total = puntos_user - abs(puntos)
                    users.update_one({"usuario": username}, {"$set": {"puntos": total}})
                    response = json.dumps({'message': "Fueron Canjeados %s puntos al cliente con usuario %s" % (abs(puntos), username)})
                    return response
                else:
                    response = json.dumps({'message': "El cliente con usuario %s no tiene la cantidad de puntos suficientes" % username})
                    return response, 502
        else:
            response = json.dumps({'message': "No tiene los permisos suficientes para canjear los puntos de un cliente"})
            return response, 403

