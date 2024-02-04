# Import the dependencies.

# import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, text
from sqlalchemy.ext.declarative import declarative_base


from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
Base = declarative_base()


# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")



# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station


# Create a session


session = Session(engine)
last_date = session.query(func.max(Measurement.date)).scalar()
one_year_ago = (pd.to_datetime(last_date) - pd.DateOffset(years=1)).strftime('%Y-%m-%d')

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start/2016-08-24<br/>"
        f"/api/v1.0/start/2016-08-24/end/2016-10-02<br/>"       
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    # session = Session(engine)
    results = session.query(Measurement.date, Measurement.prcp)\
    .filter(Measurement.date >= one_year_ago)\
    .order_by(Measurement.date).all()

    precipitation_dict = {date: prcp for date, prcp in results}
    
    # session.close()

    return jsonify(precipitation_dict)


@app.route("/api/v1.0/stations")
def stations():
    results = session.query(Station.station).all()
    station_list = [station for station, in results]
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():

    results = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == "USC00519281", Measurement.date >= one_year_ago).all()

    tobs_list = [{'date': date, 'tobs': tobs} for date, tobs in results]
    return jsonify(tobs_list)


def calculate_temperature_stats_start(start_date):
    # Convert datetime object to string representation
    start_date_str = start_date.strftime('%Y-%m-%d')

    results = session.query(func.min(Measurement.tobs).label('min_temp'),
                            func.avg(Measurement.tobs).label('avg_temp'),
                            func.max(Measurement.tobs).label('max_temp'))\
        .filter(Measurement.date == start_date_str)\
        .first()

    if results:
        return {
            'min_temp': results.min_temp,
            'avg_temp': results.avg_temp,
            'max_temp': results.max_temp
        }
    else:
        return {'error': f'No data found for the specified date: {start_date_str}'}



@app.route("/api/v1.0/start/<start>")
def temperature_stats_start(start):
    try:
        start_date = pd.to_datetime(start)
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    stats = calculate_temperature_stats_start(start_date)
    return jsonify(stats)


def calculate_temperature_stats_start_end(start_date, end_date):
    # Convert datetime objects to string representations
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    results = session.query(func.min(Measurement.tobs).label('min_temp'),
                            func.avg(Measurement.tobs).label('avg_temp'),
                            func.max(Measurement.tobs).label('max_temp'))\
        .filter(Measurement.date >= start_date_str, Measurement.date <= end_date_str)\
        .first()

    return {
        'min_temp': results.min_temp,
        'avg_temp': results.avg_temp,
        'max_temp': results.max_temp
    } if results else {}


@app.route("/api/v1.0/start/<start>/end/<end>")
def temperature_stats_start_end(start, end):
    try:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    stats = calculate_temperature_stats_start_end(start_date, end_date)
    return jsonify(stats)


if __name__ == '__main__':
    app.run(debug=True)

session.close()