from flask import Flask
from flask_pymongo import PyMongo
from flask import request
import json
from bson import ObjectId
from bson.json_util import dumps
import client2

app = Flask(__name__)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
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
    print(request.headers)
    if request.method == 'POST':
        data = request.get_json()
        username = data.get("usuario", "")
        usuario = users.find_one({"usuario": username})
        if usuario is None:
            id_user = users.insert(data)
            return JSONEncoder().encode(users.find_one({"_id": id_user}))
        else:
            return "Ya existe un cliente con el usuario: %s" % username
    elif request.method == 'DELETE':
        data = request.get_json()
        username = data.get("usuario", "")
        usuario = users.find_one({"usuario": username})
        if usuario is None:
            return "No existe un cliente con el usuario %s" % username
        else:
            users.delete_one({"usuario": username})
            return "El cliente con el usuario %s fue Eliminado exitosamente" % username
    elif request.method == 'GET':
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


@app.route('/cliente/agregarPuntos', methods=['PUT'])
def agregarPuntos():
    if request.method == 'PUT':
        data = request.get_json()
        print(request.headers)
        username = data.get("usuario", "")
        puntos = data.get("puntos", 0)

        user = users.find_one({"usuario": username})
        if user is None:
            return "El cliente con usuario %s no existe" % username
        else:
            puntos_user = user["puntos"]
            total = puntos_user + abs(puntos)
            users.update_one({"usuario": username}, {"$set": {"puntos": total}})
            return "Se agrego exitosamente %s puntos al cliente con usuario %s" % (abs(puntos), username)


@app.route('/cliente/canjearPuntos', methods=['PUT'])
def canjearPuntos():
    if request.method == 'PUT':
        data = request.get_json()
        print(request.headers)
        username = data.get("usuario", "")
        puntos = data.get("puntos", 0)

        user = users.find_one({"usuario": username})
        if user is None:
            return "El cliente con usuario %s no existe" % username
        else:
            puntos_user = user["puntos"]
            if puntos_user >= abs(puntos):
                total = puntos_user - abs(puntos)
                users.update_one({"usuario": username}, {"$set": {"puntos": total}})
                return "Fueron Canjeados %s puntos al cliente con usuario %s" % (abs(puntos), username)
            else:
                return "El cliente con usuario %s no tiene la cantidad de puntos suficientes" % username


