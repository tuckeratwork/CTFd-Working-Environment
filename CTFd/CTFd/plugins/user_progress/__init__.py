from CTFd.models import db
from sqlalchemy.sql import func

class UserProgressLog(db.Model):
    __tablename__ = 'user_progress_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'))
    category = db.Column(db.String(80))
    status = db.Column(db.String(32)) # 'correct' or 'incorrect'
    date = db.Column(db.DateTime, default=func.now())

    user = db.relationship('Users', foreign_keys='UserProgressLog.user_id', lazy='select')
    challenge = db.relationship('Challenges', foreign_keys='UserProgressLog.challenge_id', lazy='select')

    def __init__(self, user_id, challenge_id, category, status):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.category = category
        self.status = status

from flask import Blueprint, render_template, request, jsonify
from CTFd.plugins import migrations, register_plugin_assets_directory
from CTFd.plugins.challenges import BaseChallenge
from CTFd.utils.decorators import admins_only
from sqlalchemy import func, distinct

user_progress = Blueprint('user_progress', __name__, template_folder='templates')

@user_progress.route('/admin/user_progress')
@admins_only
def admin_view():
    return render_template('user_progress.html')

@user_progress.route('/api/v1/user_progress/stats', methods=['GET'])
@admins_only
def get_stats():
    user_id = request.args.get('user_id')
    category = request.args.get('category')

    if not user_id:
        return jsonify({'success': False, 'errors': 'user_id is required'}), 400

    # Get total challenges
    if category and category != 'all':
        total_challenges_query = Challenges.query.filter(Challenges.category == category)
    else:
        total_challenges_query = Challenges.query
    total_challenges = total_challenges_query.count()

    # Get attempted challenges
    attempted_query = UserProgressLog.query.filter(UserProgressLog.user_id == user_id)
    if category and category != 'all':
        attempted_query = attempted_query.filter(UserProgressLog.category == category)
    attempted_challenges = attempted_query.with_entities(func.count(distinct(UserProgressLog.challenge_id))).scalar()

    # Get solved challenges
    solved_query = UserProgressLog.query.filter(UserProgressLog.user_id == user_id, UserProgressLog.status == 'correct')
    if category and category != 'all':
        solved_query = solved_query.filter(UserProgressLog.category == category)
    solved_challenges = solved_query.with_entities(func.count(distinct(UserProgressLog.challenge_id))).scalar()

    return jsonify({
        'success': True,
        'data': {
            'total': total_challenges,
            'attempted': attempted_challenges,
            'solved': solved_challenges
        }
    })

@user_progress.route('/api/v1/user_progress/users', methods=['GET'])
@admins_only
def get_users():
    users = Users.query.all()
    user_list = [{'id': user.id, 'name': user.name} for user in users]
    return jsonify({'success': True, 'data': user_list})

@user_progress.route('/api/v1/user_progress/categories', methods=['GET'])
@admins_only
def get_categories():
    categories = db.session.query(Challenges.category).distinct().all()
    category_list = [category[0] for category in categories]
    return jsonify({'success': True, 'data': category_list})

# Plugin entry point
def load(app):
    app.register_blueprint(user_progress)
    register_plugin_assets_directory(app, base_path="/plugins/user_progress/assets/")
main
    migrations.upgrade()

    original_solve = BaseChallenge.solve
    original_fail = BaseChallenge.fail

    def new_solve(cls, user, team, challenge, request):
        # Log the solve attempt
        log_entry = UserProgressLog(
            user_id=user.id,
            challenge_id=challenge.id,
            category=challenge.category,
            status='correct'
        )
        db.session.add(log_entry)
        db.session.commit()

        # Call the original solve function
        return original_solve(cls, user, team, challenge, request)

    def new_fail(cls, user, team, challenge, request):
        # Log the fail attempt
        log_entry = UserProgressLog(
            user_id=user.id,
            challenge_id=challenge.id,
            category=challenge.category,
            status='incorrect'
        )
        db.session.add(log_entry)
        db.session.commit()

        # Call the original fail function
        return original_fail(cls, user, team, challenge, request)

    # Monkey patch the methods
    BaseChallenge.solve = new_solve
    BaseChallenge.fail = new_fail
