from flask import Flask, request, jsonify
from flask_cors import CORS
import pronotepy
from pronotepy.ent import cas_seinesaintdenis_edu
import datetime

app = Flask(__name__)
CORS(app)  # autorise Ardoise (sur un autre domaine) à appeler ce backend


def _serialize_error(e):
    return jsonify({"error": str(e)}), 400


@app.route("/login", methods=["POST"])
def login():
    """Connexion initiale avec identifiant/mot de passe EduConnect."""
    data = request.get_json(force=True)
    try:
        client = pronotepy.Client(
            data["url"],
            username=data["username"],
            password=data["password"],
            ent=cas_seinesaintdenis_edu,
        )
        if not client.logged_in:
            return jsonify({"error": "login_failed"}), 401

        return jsonify({
            "name": client.info.name,
            "credentials": client.export_credentials(),
        })
    except Exception as e:
        return _serialize_error(e)


def _client_from_credentials(credentials):
    return pronotepy.Client.token_login(**credentials)


@app.route("/timetable", methods=["POST"])
def timetable():
    data = request.get_json(force=True)
    try:
        client = _client_from_credentials(data["credentials"])
        today = datetime.date.today()
        lessons = client.lessons(today)

        result = [{
            "start": l.start.strftime("%H:%M"),
            "end": l.end.strftime("%H:%M"),
            "subject": l.subject.name if l.subject else "Cours",
            "room": l.classroom or "",
        } for l in lessons]

        return jsonify({
            "lessons": result,
            "credentials": client.export_credentials(),  # à ré-enregistrer côté Ardoise
        })
    except Exception as e:
        return _serialize_error(e)


@app.route("/grades", methods=["POST"])
def grades():
    data = request.get_json(force=True)
    try:
        client = _client_from_credentials(data["credentials"])
        period = client.current_period

        result = [{
            "subject": g.subject.name if g.subject else "Matière",
            "value": g.grade,
            "max": g.out_of,
        } for g in period.grades]

        return jsonify({
            "grades": result,
            "credentials": client.export_credentials(),
        })
    except Exception as e:
        return _serialize_error(e)


@app.route("/homework", methods=["POST"])
def homework():
    data = request.get_json(force=True)
    try:
        client = _client_from_credentials(data["credentials"])
        today = datetime.date.today()
        in_two_weeks = today + datetime.timedelta(days=14)
        hw_list = client.homework(today, in_two_weeks)

        result = [{
            "subject": h.subject.name if h.subject else "Matière",
            "description": h.description,
            "dueDate": h.date.strftime("%d/%m/%Y"),
        } for h in hw_list]

        return jsonify({
            "homework": result,
            "credentials": client.export_credentials(),
        })
    except Exception as e:
        return _serialize_error(e)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
