#Developed by SPC Casey O'Reilly
#Questions or issues can be directed to casey.e.oreilly.mil@usa.army.mil

from flask import render_template, Blueprint, request, url_for

from flask_sqlalchemy import SQLAlchemy
from CTFd.cache import cache
from CTFd.models import (
    Challenges,
    Pages,
    db,
)
from CTFd.utils.user import (
    authed,
    get_current_user,
    get_current_user_attrs,
)
from CTFd.admin import users  # noqa: F401
from CTFd.plugins import register_plugin_assets_directory

# Adds the Reset PE's page to the CTF's nav bar if it doesn't already exist
if not Pages.query.filter_by(title="Reset PE's").all():
    # The route given points to the self_reset() python function
    page_to_add = Pages(title="Reset PE's", route="plugins/self_reset/", content=None, draft=False)
    db.session.add(page_to_add)
    db.session.commit()

def load(app):
    # Register the files that the plugin uses
    register_plugin_assets_directory(app, base_path='/plugins/self_reset/assets/')
    # Establish the URL route for the plugin
    @app.route('/plugins/self_reset/', methods=['GET'])
    def self_reset():
        # Check for the button selection on t
        reset = request.args.get('reset')
        print(reset)
        # Check if a user clicked yes
        if reset == 'y':
            # User Info
            user = get_current_user()

            # Gather list of user submissions
            user_submissions = user.get_solves() + user.get_fails()
            # Iterate through all of the user's submissions
            for submission in user_submissions:
                # Gather the information for the challenge that the submissions correlate to
                challenge_info = Challenges.query.filter(Challenges.id == submission.challenge_id).first()
                # Ignore the unlock challenges
                if challenge_info.category == '.Unlock':
                    continue
                else:
                    # Delete the submission from the database
                    db.session.delete(submission)

            # Commit the database changes, so the submission removals are reflected
            db.session.commit()

            # Clear caches for solves and fails
            cache.delete_memoized(user.get_solves)
            cache.delete_memoized(user.get_fails)
            if user.team:
                cache.delete_memoized(user.team.get_solves)
                cache.delete_memoized(user.team.get_fails)

            # Render the HTML page
            return render_template('plugins/self_reset/assets/success.html')
        else:
            return render_template('plugins/self_reset/assets/self_reset.html')

    @app.route('/plugins/self_reset/solves_only', methods=['GET'])
    def reset_solves_only():
        # Check for the button selection on t
        reset = request.args.get('reset')
        print(reset)
        # Check if a user clicked yes
        if reset == 'y':
            # User Info
            user = get_current_user()

            # Gather list of user solves only
            user_solves = user.get_solves()
            # Iterate through all of the user's solves
            for solve in user_solves:
                # Gather the information for the challenge that the solve correlates to
                challenge_info = Challenges.query.filter(Challenges.id == solve.challenge_id).first()
                # Ignore the unlock challenges
                if challenge_info.category == '.Unlock':
                    continue
                else:
                    # Delete the solve from the database
                    db.session.delete(solve)

            # Commit the database changes, so the solve removals are reflected
            db.session.commit()

            # Clear caches for solves
            cache.delete_memoized(user.get_solves)
            if user.team:
                cache.delete_memoized(user.team.get_solves)

            # Render the HTML page
            return render_template('plugins/self_reset/assets/success.html')
        else:
            return render_template('plugins/self_reset/assets/self_reset.html')

    @app.route('/plugins/self_reset/fails_only', methods=['GET'])
    def reset_fails_only():
        # Check for the button selection on t
        reset = request.args.get('reset')
        print(reset)
        # Check if a user clicked yes
        if reset == 'y':
            # User Info
            user = get_current_user()

            # Gather list of user fails only
            user_fails = user.get_fails()
            # Iterate through all of the user's fails
            for fail in user_fails:
                # Gather the information for the challenge that the fail correlates to
                challenge_info = Challenges.query.filter(Challenges.id == fail.challenge_id).first()
                # Ignore the unlock challenges
                if challenge_info.category == '.Unlock':
                    continue
                else:
                    # Delete the fail from the database
                    db.session.delete(fail)

            # Commit the database changes, so the fail removals are reflected
            db.session.commit()
            # Render the HTML page
            return render_template('plugins/self_reset/assets/success.html')
        else:
            return render_template('plugins/self_reset/assets/self_reset.html')

