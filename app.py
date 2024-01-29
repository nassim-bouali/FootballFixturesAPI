from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from datetime import datetime
import traceback
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class MatchDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition = db.Column(db.String(100), nullable=False)
    stadium = db.Column(db.String(100), nullable=False)
    kickOffDatetime = db.Column(db.DateTime, nullable=False)
    creationDate = db.Column(db.DateTime, default=datetime.utcnow())
    teamsMatchStats = db.relationship('TeamMatchStats', backref='matchDetails', lazy=True)

    def __repr__(self):
        return '<Match %r>' % self.id


class TeamMatchStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teamName = db.Column(db.String(100), nullable=False)
    homeTeam = db.Column(db.Boolean, nullable=False)
    goalsScored = db.Column(db.Integer, nullable=False)
    shots = db.Column(db.Integer, nullable=False)
    possession = db.Column(db.Float, nullable=False)
    passes = db.Column(db.Integer, nullable=False)
    dribbles = db.Column(db.Integer, nullable=False)
    tackles = db.Column(db.Integer, nullable=False)
    corners = db.Column(db.Integer, nullable=False)
    matchDetailsId = db.Column(db.Integer, db.ForeignKey('match_details.id'), nullable=False)

    def __repr__(self):
        return '<Team Match Stats %r>' % self.id


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        kick_off_datetime = datetime.strptime(request.form['kickOffDatetime'], '%Y-%m-%dT%H:%M')
        match = MatchDetails(competition=request.form['competition'],
                             stadium=request.form['stadium'],
                             kickOffDatetime=kick_off_datetime)
        home_team = TeamMatchStats(teamName=request.form['homeTeam'],
                              homeTeam=True,
                              goalsScored=request.form['homeGoals'],
                              shots=request.form['homeShots'],
                              possession=request.form['homePossession'],
                              passes=request.form['homePasses'],
                              dribbles=request.form['homeDribbles'],
                              tackles=request.form['homeTackles'],
                              corners=request.form['homeCorners'],
                              matchDetails=match)
        away_team = TeamMatchStats(teamName=request.form['awayTeam'],
                              homeTeam=False,
                              goalsScored=request.form['awayGoals'],
                              shots=request.form['awayShots'],
                              possession=request.form['awayPossession'],
                              passes=request.form['awayPasses'],
                              dribbles=request.form['awayDribbles'],
                              tackles=request.form['awayTackles'],
                              corners=request.form['awayCorners'],
                              matchDetails=match)
        try:
            db.session.add(match)
            db.session.add(home_team)
            db.session.add(away_team)
            db.session.commit()
        except Exception as e:
            print(f"An exception occurred: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return 'Unable to create your match !'
        return redirect('/')
    else:
        matches = MatchDetails.query.order_by(MatchDetails.creationDate).all()
        processed_matches = []
        for match in matches:
            home_team_stats = None
            away_team_stats = None

            for team_stats in match.teamsMatchStats:
                if team_stats.homeTeam:
                    home_team_stats = team_stats
                else:
                    away_team_stats = team_stats

                if home_team_stats and away_team_stats:
                    break

            processed_matches.append({
                'match': match,
                'home_team_stats': home_team_stats,
                'away_team_stats': away_team_stats
            })
        return render_template('index.html', matches=processed_matches)


@app.route('/delete/<id>')
def delete(id):
    match_to_delete = MatchDetails.query.get_or_404(id)
    try:
        for teamStats in match_to_delete.teamsMatchStats:
            db.session.delete(teamStats)
        db.session.delete(match_to_delete)
        db.session.commit()
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return f'Unable to delete match id: {id} !'
    return redirect('/')


@app.route('/update/<id>', methods=['GET', 'POST'])
def update(id):
    match_to_update = MatchDetails.query.get_or_404(id)
    if request.method == 'POST':
        kick_off_datetime = datetime.strptime(request.form['kickOffDatetime'], '%Y-%m-%dT%H:%M')

        match_to_update.competition = request.form['competition']
        match_to_update.stadium = request.form['stadium']
        match_to_update.kickOffDatetime = kick_off_datetime

        for teamMatchStats in match_to_update.teamsMatchStats:
            if teamMatchStats.homeTeam:
                teamMatchStats.teamName = request.form['homeTeam']
                teamMatchStats.goalsScored = request.form['homeGoals']
                teamMatchStats.shots = request.form['homeShots']
                teamMatchStats.possession = request.form['homePossession']
                teamMatchStats.passes = request.form['homePasses']
                teamMatchStats.dribbles = request.form['homeDribbles']
                teamMatchStats.tackles = request.form['homeTackles']
                teamMatchStats.corners = request.form['homeCorners']
                teamMatchStats.matchDetails = match_to_update
            else:
                teamMatchStats.teamName = request.form['awayTeam']
                teamMatchStats.goalsScored = request.form['awayGoals']
                teamMatchStats.shots = request.form['awayShots']
                teamMatchStats.possession = request.form['awayPossession']
                teamMatchStats.passes = request.form['awayPasses']
                teamMatchStats.dribbles = request.form['awayDribbles']
                teamMatchStats.tackles = request.form['awayTackles']
                teamMatchStats.corners = request.form['awayCorners']
                teamMatchStats.matchDetails = match_to_update
        try:
            db.session.commit()
        except Exception as e:
            print(f"An exception occurred: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return f'Unable to update match id: {id} !'
        return redirect('/')

    else:
        home_team_stats = None
        away_team_stats = None
        kick_off_datetime = match_to_update.kickOffDatetime.strftime('%Y-%m-%dT%H:%M')
        with db.session.no_autoflush:
            match_to_update.kickOffDatetime = kick_off_datetime
            for teamStats in match_to_update.teamsMatchStats:
                if teamStats.homeTeam:
                    home_team_stats = teamStats
                else:
                    away_team_stats = teamStats

            match_to_update = {
                'match_details': match_to_update,
                'home_team_stats': home_team_stats,
                'away_team_stats': away_team_stats
            }
            return render_template('update.html', match_to_update=match_to_update)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
