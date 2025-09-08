from CTFd.plugins.challenges import BaseChallenge, CHALLENGE_CLASSES
from CTFd.plugins import register_plugin_assets_directory
from CTFd.models import (
    db,
    Solves,
    Fails,
    Flags,
    Challenges,
    ChallengeFiles,
    Tags,
    Hints,
    Submissions,
)
from CTFd.utils import get_config
from CTFd.utils.decorators import admins_only, authed_only
from CTFd.utils.user import get_ip, get_current_user
from CTFd.utils.uploads import delete_file
from CTFd.utils.modes import get_model, USERS_MODE
from CTFd.utils.dates import isoformat
from flask import Blueprint, render_template, request, jsonify
import datetime
import requests


class ManualSubmissionChallenge(BaseChallenge):
    id = "manual_verification"  # Unique identifier used to register challenges
    name = "manual_verification"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/manual_verification/assets/create.html",
        "update": "/plugins/manual_verification/assets/update.html",
        "view": "/plugins/manual_verification/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/manual_verification/assets/create.js",
        "update": "/plugins/manual_verification/assets/update.js",
        "view": "/plugins/manual_verification/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/manual_verification/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "manual_verification",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
        challenge = ManualChallenge(**data)

        db.session.add(challenge)
        db.session.commit()

        return challenge

    @staticmethod
    def read(challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = ManualChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": ManualSubmissionChallenge.id,
                "name": ManualSubmissionChallenge.name,
                "templates": ManualSubmissionChallenge.templates,
                "scripts": ManualSubmissionChallenge.scripts,
            },
        }
        return data

    @staticmethod
    def update(challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()
        for attr, value in data.items():
            setattr(challenge, attr, value)

        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.

        :param challenge:
        :return:
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        ManualChallenge.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()

    @staticmethod
    def attempt(challenge, request):
        """
        This method is not used as manual submissions are not solved with the compare() method.

        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return: (boolean, string)
        """
        return False, "Submission under review"

    @staticmethod
    def solve(user, challenge, request):
        """
        This method is not used as manual submission challenges are not solved with flags.

        :param team: The Team object from the database
        :param chal: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        pass

    @staticmethod
    def fail(user, challenge, request):
        """
        This method is used to insert Pending into the database in order to mark an answer pending.

        :param team: The Team object from the database
        :param chal: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        pending = Pending(
            user_id=user.id,
            challenge_id=challenge.id,
            ip=get_ip(request),
            provided=submission,
        )

        db.session.add(pending)
        db.session.commit()
        db.session.close()


class ManualChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "manual_verification"}
    id = db.Column(None, db.ForeignKey("challenges.id"), primary_key=True)

    def __init__(self, *args, **kwargs):
        super(ManualChallenge, self).__init__(**kwargs)


class Pending(Submissions):
    __mapper_args__ = {"polymorphic_identity": "pending"}


def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES["manual_verification"] = ManualSubmissionChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/manual_verification/assets/"
    )
    manual_verifications = Blueprint(
        "manual_verifications", __name__, template_folder="templates"
    )

    @manual_verifications.route("/submissions/<challenge_id>", methods=["GET"])
    @authed_only
    def submissions_for_challenge(challenge_id):
        user = get_current_user()
        if get_config("user_mode") == USERS_MODE:
            pending = Pending.query.filter_by(
                challenge_id=challenge_id, user_id=user.id
            ).all()
        else:
            pending = Pending.query.filter_by(
                challenge_id=challenge_id, team_id=user.team_id
            ).all()

        if get_config("user_mode") == USERS_MODE:
            correct = Solves.query.filter(
                Solves.user_id == user.id, Solves.challenge_id == challenge_id
            ).all()
        else:
            correct = Solves.query.filter(
                Solves.team_id == user.team_id, Solves.challenge_id == challenge_id
            ).all()

        pending = [{"provided": p.provided, "date": isoformat(p.date)} for p in pending]
        correct = [{"provided": c.provided, "date": isoformat(c.date)} for c in correct]

        resp = {"success": True, "data": {"pending": pending, "correct": correct}}
        return jsonify(resp)

    @manual_verifications.route("/admin/submissions/pending", methods=["GET"])
    @admins_only
    def view_pending_submissions():
        filters = {"type": "pending"}

        curr_page = abs(int(request.args.get("page", 1, type=int)))
        results_per_page = 50
        page_start = results_per_page * (curr_page - 1)
        page_end = results_per_page * (curr_page - 1) + results_per_page
        sub_count = Submissions.query.filter_by(**filters).count()
        page_count = int(sub_count / results_per_page) + (
            sub_count % results_per_page > 0
        )

        Model = get_model()

        submissions = (
            Submissions.query.add_columns(
                Submissions.id,
                Submissions.type,
                Submissions.challenge_id,
                Submissions.provided,
                Submissions.account_id,
                Submissions.date,
                Challenges.name.label("challenge_name"),
                Model.name.label("team_name"),
            )
            .filter_by(**filters)
            .join(Challenges)
            .join(Model)
            .order_by(Submissions.date.desc())
            .slice(page_start, page_end)
            .all()
        )

        return render_template(
            "verify_submissions.html",
            submissions=submissions,
            page_count=page_count,
            curr_page=curr_page,
        )

    @manual_verifications.route(
        "/admin/verify_submissions/<submission_id>/<status>", methods=["POST"]
    )
    @admins_only
    def verify_submissions(submission_id, status):
        submission = Submissions.query.filter_by(id=submission_id).first_or_404()

        if status == "solve":
            solve = Solves(
                user_id=submission.user_id,
                challenge_id=submission.challenge_id,
                ip=submission.ip,
                provided=submission.provided,
                date=submission.date,
            )

            currentDT = datetime.datetime.now()
            cDT = currentDT.strftime("%Y-%m-%d %H:%M:%S")

            k = open("/opt/CTFd/CTFd/config/csat","r")
            ip = k.read()
            k.close()
            ip=ip.replace("\n","")


            l = open('CTFd/config/type','r')
            ctfd_type = l.read()
            l.close()
            ctfd_type=ctfd_type.replace("\r","")
            ctfd_type=ctfd_type.replace("\n","")

            ll = open('CTFd/config/module','r')
            mod_type = ll.read()
            ll.close()
            mod_type = mod_type.replace("\r","")
            mod_type = mod_type.replace("\n","")

            # debug to ensure user id is being used
            #print("USER_ID FROM SOLVE DB ADD")
            #print(solve.user_id)
            d={
                'ctfd_type':ctfd_type,
                'module':mod_type,
                'class':user.team.name,
                'challenge_id':str(challenge.id),
                'username':user.name,
                'type':'correct',
                'date':cDT
            }
            certificate=('certs/client.crt', 'certs/client.key')
            r=requests.post('https://' + ip +':4433/v1/submission',cert=certificate, json=d,verify=False)
            print(str(r.status_code))

            db.session.add(solve)
            # Get rid of pending submissions for the challenge
            Submissions.query.filter(
                Submissions.challenge_id == submission.challenge_id,
                Submissions.user_id == submission.user_id,
                Submissions.type == "pending",
            ).delete()
        elif status == "fail":
            wrong = Fails(
                user_id=submission.user_id,
                challenge_id=submission.challenge_id,
                ip=submission.ip,
                provided=submission.provided,
                date=submission.date,
            )

            currentDT = datetime.datetime.now()
            cDT = currentDT.strftime("%Y-%m-%d %H:%M:%S")

            k = open("/opt/CTFd/CTFd/config/csat","r")
            ip = k.read()
            k.close()
            ip=ip.replace("\n","")


            l = open('CTFd/config/type','r')
            ctfd_type = l.read()
            l.close()
            ctfd_type=ctfd_type.replace("\r","")
            ctfd_type=ctfd_type.replace("\n","")

            ll = open('CTFd/config/module','r')
            mod_type = ll.read()
            ll.close()
            mod_type = mod_type.replace("\r","")
            mod_type = mod_type.replace("\n","")

            # debug to ensure user id is being used
            #print("USER_ID FROM SOLVE DB ADD")
            #print(solve.user_id)
            d={
                'ctfd_type':ctfd_type,
                'module':mod_type,
                'class':user.team.name,
                'challenge_id':str(challenge.id),
                'username':user.name,
                'type':'correct',
                'date':cDT
            }
            certificate=('certs/client.crt', 'certs/client.key')
            r=requests.post('https://' + ip +':4433/v1/submission',cert=certificate, json=d,verify=False)
            print(str(r.status_code))

            db.session.add(wrong)
        else:
            return jsonify({"success": False})
        db.session.delete(submission)
        db.session.commit()
        db.session.close()
        return jsonify({"success": True})

    app.register_blueprint(manual_verifications)
