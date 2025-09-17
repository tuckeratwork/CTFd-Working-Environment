import re
import os
from flask import Blueprint, render_template, request, jsonify
from CTFd.plugins import register_plugin_assets_directory
from CTFd.models import db, Challenges, Users
from CTFd.utils.decorators import admins_only
from sqlalchemy import func, distinct

user_progress = Blueprint('user_progress', __name__, template_folder='templates', static_folder='assets')

LOG_FILE_PATH = "/opt/CTFd/.data/CTFd/logs/submissions.log"

def parse_log_file(user_id_map, chal_cat_map):
    """
    Parses the submission log file to gather statistics.
    """
    stats = {} # { (user_id, chal_id): 'correct' or 'incorrect' }

    if not os.path.exists(LOG_FILE_PATH):
        return {}

    log_pattern = re.compile(r"\[.*?\]\s(.*?)\ssubmitted\s\".*?\"\son\s(\d+)\swith\skpm\s\d+\s\[(.*?)\]")

    with open(LOG_FILE_PATH, 'r') as f:
        for line in f:
            match = log_pattern.match(line)
            if match:
                username, chal_id_str, status_str = match.groups()

                user_id = user_id_map.get(username)
                chal_id = int(chal_id_str)

                if not user_id:
                    continue

                # We only care about the first correct submission.
                # For incorrect, any attempt counts.
                key = (user_id, chal_id)

                if key in stats and stats[key] == 'correct':
                    continue # Already solved, ignore further attempts

                if "CORRECT" in status_str:
                    stats[key] = 'correct'
                elif "WRONG" in status_str:
                    stats[key] = 'incorrect'

    return stats

@user_progress.route('/admin/user_progress')
@admins_only
def admin_view():
    return render_template('user_progress.html')

@user_progress.route('/api/v1/user_progress/stats', methods=['GET'])
@admins_only
def get_stats():
    user_id_filter = request.args.get('user_id')
    category_filter = request.args.get('category')

    if not user_id_filter:
        return jsonify({'success': False, 'errors': 'user_id is required'}), 400

    user_id_filter = int(user_id_filter)

    # Create maps for efficient lookups
    users = Users.query.all()
    user_id_map = {user.name: user.id for user in users}

    challenges = Challenges.query.all()
    chal_cat_map = {chal.id: chal.category for chal in challenges}

    # Get total challenges for the selected category
    if category_filter and category_filter != 'all':
        total_challenges = len([c for c in challenges if c.category == category_filter])
    else:
        total_challenges = len(challenges)

    # Parse the log file
    all_stats = parse_log_file(user_id_map, chal_cat_map)

    attempted_chals = set()
    solved_chals = set()

    for (user_id, chal_id), status in all_stats.items():
        if user_id != user_id_filter:
            continue

        category = chal_cat_map.get(chal_id)

        # Apply category filter
        if category_filter and category_filter != 'all' and category != category_filter:
            continue

        attempted_chals.add(chal_id)
        if status == 'correct':
            solved_chals.add(chal_id)

    return jsonify({
        'success': True,
        'data': {
            'total': total_challenges,
            'attempted': len(attempted_chals),
            'solved': len(solved_chals)
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

def load(app):
    app.register_blueprint(user_progress)
