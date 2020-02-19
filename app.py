#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
import sys
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://jordanhuus@localhost:5432/fyyur'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='show_venue', cascade='all,delete', lazy=False)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='show_artist', lazy=False)


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.String(), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)

    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"

    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venue_data = []
    unique_location_locations = Venue.query.distinct(Venue.city, Venue.state).all()
    for unique_location in unique_location_locations:

        # Venue location
        venue_location = {
            "city": unique_location.city,
            "state": unique_location.state,
            "venues": []
        }

        # Venues within that location
        for venue in Venue.query.filter(Venue.city==unique_location.city, Venue.state==unique_location.state):
            venue_location["venues"].append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": Show.query.filter(Show.venue_id==venue.id, db.cast(Show.start_time, db.Date) >= datetime.datetime.now()).count()
            })

        venue_data.append(venue_location)

    return render_template('pages/venues.html', areas=venue_data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # Search term
    venue_search_term = request.form.get('search_term', '')

    # Search by name (case insensitive)
    venues_by_name = Venue.query.filter(Venue.name.ilike(f"%{venue_search_term}%")).all()

    # Search by city (case insensitive)
    venues_by_city = Venue.query.filter(Venue.city.ilike(f"%{venue_search_term}%")).all()

    # Search by state (case insensitive)
    venues_by_state = Venue.query.filter(Venue.state.ilike(f"%{venue_search_term}%")).all()

    # Response data
    response = {
        "count": len(venues_by_name) + len(venues_by_city) + len(venues_by_state),
        "data" : []
    }
    for venue in (venues_by_name + venues_by_city + venues_by_state):
        response["data"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": Show.query.filter(Show.venue_id == venue.id, db.cast(Show.start_time, db.Date) >= datetime.datetime.now()).count()
        })


    if response['count'] == 0:
        flash(f"No results found for {venue_search_term}.")
        return redirect(url_for('venues'))
    else:
        return render_template('pages/search_venues.html', results=response, search_term=venue_search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Gather artist data
    venue = Venue.query.get(venue_id)
    if venue == None:
        abort(404)
    venue_data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }

    # Append show data
    past_shows = []
    upcoming_shows = []
    for show in Show.query.filter_by(venue_id=venue_id):

        print()
        print()
        print(show.id)
        print(show.start_time)
        print()
        print()

        # Past vs upcoming shows
        if datetime.datetime.strptime(show.start_time, '%Y-%m-%dT%H:%M:%S.%fZ') < datetime.datetime.now():
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": Artist.query.get(show.artist_id).name,
                "artist_image_link": Artist.query.get(show.artist_id).image_link,
                "start_time": show.start_time
            })
        else:
            upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": Artist.query.get(show.artist_id).name,
                "artist_image_link": Artist.query.get(show.artist_id).image_link,
                "start_time": show.start_time
            })

    venue_data["past_shows"] = past_shows
    venue_data["upcoming_shows"] = upcoming_shows
    venue_data["past_shows_count"] = len(past_shows)
    venue_data["upcoming_shows_count"] = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=venue_data)


#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    # TODO(jordanhuus): Add UI support for venue image link
    image_link = 'https://images.unsplash.com/photo-1549044940-cbc22f936f6f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=2608&q=80'
    genres = request.form.getlist('genres')
    website = request.form.get('website')
    facebook_link = request.form.get('facebook_link')
    new_venue = Venue(
        name=name,
        city=city,
        state=state,
        address=address,
        phone=phone,
        image_link=image_link,
        website=website,
        facebook_link=facebook_link,
        seeking_talent=True,
        seeking_description='Seeking awesome talent.',
        genres=genres
    )

    error = False
    try:
        db.session.add(new_venue)
        db.session.commit()
        flash(f'Venue {request.form["name"]} was successfully listed!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash(f'Venue {request.form["name"]} failed to be listed. Please Refresh and try again.')
        abort(500)
    else:
        return render_template('pages/home.html')


@app.route('/venues/delete/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    error = False
    venue = None
    venue_name = ""
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue {venue_name} was successfully removed.')
        print(f'Venue {venue_name} was successfully removed.')
    except:
        error = True
        db.session.rollback()
        print(f"There was an error deleting venue with ID={venue_id}.")
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

    data = []
    for artist in Artist.query.all():
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # Form artist search term
    artist_search_term = request.form.get('search_term', '')

    # Query artist objects that contain (case insensitive) the specified search term
    artists = Artist.query.filter(Artist.name.ilike(f"%{artist_search_term}%")).all()

    # Response data
    response = {
        "count": len(artists),
        "data" : []
    }
    for artist in artists:
        response["data"].append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": Show.query.filter(Show.artist_id == artist.id, db.cast(Show.start_time, db.Date) >= datetime.datetime.now()).count()
        })

    return render_template('pages/search_artists.html', results=response, search_term=artist_search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    # Gather artist data
    artist = Artist.query.get(artist_id)
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": "https://www.google.com",
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }

    # Append show data
    past_shows = []
    upcoming_shows = []
    for show in Show.query.filter_by(artist_id=artist.id):
        # Past vs upcoming shows
        if datetime.datetime.strptime(show.start_time, '%Y-%m-%dT%H:%M:%S.%fZ') < datetime.datetime.now():
            past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": Venue.query.get(show.venue_id).name,
                "venue_image_link": Venue.query.get(show.venue_id).image_link,
                "start_time": show.start_time
            })
        else:
            upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": Venue.query.get(show.venue_id).name,
                "venue_image_link": Venue.query.get(show.venue_id).image_link,
                "start_time": show.start_time
            })

    artist_data["past_shows"] = past_shows
    artist_data["upcoming_shows"] = upcoming_shows
    artist_data["past_shows_count"] = len(past_shows)
    artist_data["upcoming_shows_count"] = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=artist_data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    if artist == None:
        abort(404)
    else:
        return render_template('forms/edit_artist.html', form=form, artist=artist)



@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # Form data
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')

    error = False
    try:
        # Update artist
        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.genres = genres
        artist.facebook_link = facebook_link

        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for('show_artist', artist_id=artist_id))



@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # Form data
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.get('genres')
    facebook_link = request.form.get('facebook_link')

    error = False
    try:
        # Update venue
        venue = Venue.query.get(venue_id)
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.genres = genres
        venue.facebook_link = facebook_link

        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # Form data
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    image_link = 'fjksdlj' #TODO(jordanhuus): implement from edit feature?
    seeking_venue = True
    seeking_description = 'jfkdsj' #TODO(jordanhuus): implement from edit feature?
    new_artist = Artist(
        name=name,
        city=city,
        state=state,
        phone=phone,
        genres=genres,
        facebook_link=facebook_link,
        image_link=image_link,
        seeking_venue=seeking_venue,
        seeking_description=seeking_description
    )

    error = False
    try:
        db.session.add(new_artist)
        db.session.commit()
        flash(f'Artist {request.form["name"]} was successfully listed!')
    except:
        error = True
        flash(f'There was an error adding {request.form["name"]} artist.')
        db.session.rollback()
        print('There was an error adding a new Artist')
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    return render_template('pages/shows.html', shows=Show.query.all())


@app.route('/shows/create')
def create_shows():
    form = ShowForm()

    # Artist data
    artists = Artist.query.all()

    # Venue data
    venues = Venue.query.all()

    return render_template('forms/new_show.html', form=form, artists=artists, venues=venues)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # Retrieve form data
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')+':00.00Z'

    # Add data to database
    new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    error = False
    try:
        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
        flash('Uh oh! There was an error adding your show. Refresh and try again.')
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#
# Default port:
if __name__ == '__main__':
    app.run(debug=True)

    # Or specify port manually:
    '''
    if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    '''
