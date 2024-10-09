import flask
from flask import Flask, request, Response
from flask.views import MethodView
from models import Advertisement, Session, User
import json

#использовала json.dumps, так как jsonify возвращал нечитаемые символы 
app = Flask("app")

class HttpError(Exception):
    def __init__(self, status_code: int, error_msg: str | dict | list):
        self.status_code = status_code
        self.error_msg = error_msg

@app.before_request
def before_request():
    session = Session()
    request.session = session

@app.after_request
def after_request(http_response: flask.Response):
    request.session.close()
    return http_response

def get_advertisement(advertisement_id: int):
    advertisement = request.session.get(Advertisement, advertisement_id)
    if advertisement is None:
        raise HttpError(404, "Объявление не найдено")
    return advertisement

def get_user(user_id: int):
    user = request.session.get(User, user_id)
    if user is None:
        raise HttpError(400, "Пользователь не найден")
    return user

@app.route('/create_user', methods=['POST'])
def create_user():
    json_data = request.json
    username = json_data.get('username')

    if not username:
        return Response(json.dumps({"error": "Пропущенное поле"}, ensure_ascii=False), status=400, mimetype='application/json')

    user = User(username=username)
    request.session.add(user)
    request.session.commit()

    return Response(json.dumps({
        "message": "Пользователь создан",
        "user": {
            "id": user.id,
            "username": user.username
        }
    }, ensure_ascii=False), status=201, mimetype='application/json')

@app.route('/')
def index():
    return "Привет!"

class AdvertisementView(MethodView):

    def get(self, advertisement_id: int):
        try:
            advertisement = get_advertisement(advertisement_id)
            return Response(json.dumps(advertisement.json, ensure_ascii=False), status=200, mimetype='application/json') 
        except HttpError as e:
            return Response(json.dumps({"error": e.error_msg}, ensure_ascii=False), status=e.status_code, mimetype='application/json')

    def post(self):
        json_data = request.json
        title = json_data.get('title')
        description = json_data.get('description')
        owner_id = json_data.get('owner_id') 

        if not title or not description or not owner_id:
            return Response(json.dumps({"error": "Пропущенное поле"}, ensure_ascii=False), status=400, mimetype='application/json')

        try:
            user = get_user(owner_id)
        except HttpError as e:
            return Response(json.dumps({"error": e.error_msg}, ensure_ascii=False), status=e.status_code, mimetype='application/json')

        advertisement = Advertisement(
            title=title,
            description=description,
            owner_id=owner_id 
        )

        request.session.add(advertisement)
        request.session.commit()

        return Response(json.dumps({
            "message": "Объявление создано",
            "ad": {
                "id": advertisement.id,
                "title": advertisement.title,
                "description": advertisement.description,
                "owner_id": advertisement.owner_id,
                "created_at": advertisement.created_at.isoformat()
            }
        }, ensure_ascii=False), status=201, mimetype='application/json')

    def patch(self, advertisement_id):
        json_data = request.json
        
        try:
            advertisement = get_advertisement(advertisement_id)
        except HttpError as e:
            return Response(json.dumps({"error": e.error_msg}, ensure_ascii=False), status=e.status_code, mimetype='application/json')

        for field, value in json_data.items():
            if hasattr(advertisement, field):
                setattr(advertisement, field, value)

        request.session.commit()

        return Response(json.dumps({
            "id": advertisement.id,
            "title": advertisement.title,
            "description": advertisement.description,
            "owner_id": advertisement.owner_id,
            "created_at": advertisement.created_at.isoformat()
        }, ensure_ascii=False), status=200, mimetype='application/json')

    def delete(self, advertisement_id):
        advertisement = get_advertisement(advertisement_id)
        request.session.delete(advertisement)
        request.session.commit()
        return Response(json.dumps({"status": "Удалено"}, ensure_ascii=False), status=200, mimetype='application/json')


advertisement_view = AdvertisementView.as_view('advertisement_view')
app.add_url_rule('/ads/', view_func=advertisement_view, methods=['POST'])
app.add_url_rule('/ads/<int:advertisement_id>', view_func=advertisement_view, methods=['GET', 'PATCH', 'DELETE'])

if __name__ == '__main__':
    app.run(debug=True)
