""" database access
docs:
* http://initd.org/psycopg/docs/
* http://initd.org/psycopg/docs/pool.html
* http://initd.org/psycopg/docs/extras.html#dictionary-like-cursor
"""

from contextlib import contextmanager
import logging
import os

from flask import current_app, g

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor

from collections import Counter
from datetime import datetime, timedelta

pool = None

#db code reference: 5117 lecture Session 07 -- Adding a database

def setup():
    global pool
    DATABASE_URL = os.environ['DATABASE_URL']
    current_app.logger.info(f"creating db connection pool")
    pool = ThreadedConnectionPool(1, 100, dsn=DATABASE_URL, sslmode='require')


@contextmanager
def get_db_connection():
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)
        # connection.close()


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
        cursor = connection.cursor(cursor_factory=DictCursor)
        # cursor = connection.cursor()
        try:
            yield cursor
            if commit:
                connection.commit()
        finally:
            cursor.close()
            connection.close()


def init_table():
  with get_db_cursor(True) as cur:
      cur.execute('DROP TABLE IF EXISTS survey_res;')
      cur.execute('CREATE TABLE survey_res (id serial PRIMARY KEY,'
                  'name varchar (200) NOT NULL,'
                  'email varchar (200) NOT NULL,'
                  'travel_frequency varchar (200),'
                  'booking_website varchar (200),'
                  'payment_method varchar (200),'
                  'other_payment_answer text,'
                  'preferred_hotel varchar (200),'
                  'hotel_like_most text,'
                  'date_time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
                  )


# each column is of format: question : answer
def add_survey_res(response_dict):
    with get_db_cursor(True) as cur:
      name = response_dict["name"]
      email = response_dict["email"]
      travel_freq = response_dict["travel_frequency"]
      booking_website = response_dict["booking_website"]
      payment_method = response_dict["payment_method"]
      other_payment = response_dict["other_payment_answer"]
      prefer_hotel = response_dict["preferred_hotel"]
      hotel_like_most = response_dict["hotel_like_most"]
      cur.execute('INSERT INTO survey_res (name, email, travel_frequency, booking_website, payment_method, other_payment_answer, preferred_hotel, hotel_like_most)'
      'values (%s, %s, %s, %s, %s, %s, %s, %s)',
      (name, email, travel_freq, booking_website, payment_method, other_payment, prefer_hotel, hotel_like_most))


def get_survey_res(reverse=False):
  with get_db_cursor(True) as cur:
    if(not reverse):
      cur.execute('SELECT * FROM survey_res;')
      # res = cur.fetchall()
      res = [dict(row) for row in cur.fetchall()]
    else:
      cur.execute('SELECT * FROM survey_res ORDER BY date_time_added DESC;')
      res = [dict(row) for row in cur.fetchall()]
      # res = cur.fetchall()

    return res


# [
#   {
#     "response_count": 2,
#     "response_date": "Sun, 19 Feb 2023 00:00:00 GMT"
#   }
# ]
def get_date_info():
  with get_db_cursor(True) as cur:
    cur.execute('SELECT DATE(date_time_added) AS response_date, COUNT(*) AS response_count FROM survey_res GROUP BY response_date;')
    res = [dict(row) for row in cur.fetchall()]
  
  return res

def get_time_series_chart():
    responses = get_date_info()
    
    # Count the number of responses per day from the table
    daily_counts = Counter()
    for response in responses:
        date = response["response_date"]
        daily_counts[date] = response["response_count"]
    
    print(daily_counts)
    # Create a list of dates and counts
    labels = []
    data = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    for i in range(7):
        date = start_date + timedelta(days=i)
        count = daily_counts[date]
        labels.append(date.strftime('%Y-%m-%d'))
        data.append(count)
    
    # Create the time series chart
    time_series_chart = {
        'type': 'line',
        'data': {
            'labels': labels,
            'datasets': [{
                'label': 'Responses',
                'data': data,
                'fill': False,
                'borderColor': 'rgb(75, 192, 192)',
                'lineTension': 0.1
            }]
        },
        'options': {
            'scales': {
                'yAxes': [{
                    'ticks': {
                        'beginAtZero': True
                    }
                }]
            }
        }
    }

    return time_series_chart

import re 

def summarize_responses(responses, questionMap):
    # Initialize an empty dictionary to hold the response counts
    response_summary = {}
    
    # Loop over the survey questions and options, initializing counts to zero
    for question, options in questionMap.items():
        response_summary[question] = {option: 0 for option in options}
    
    # Loop over the survey responses and increment the response counts
    for response in responses:
        for question, answer in response.items():
            if question in questionMap:
              # check payment_method: [paypal, other]
              if question == "payment_method":
                answer = answer.split(',')
              
              if isinstance(answer, list):
                if len(answer) == 0:
                  continue
                for option in answer:
                  response_summary[question][option] += 1
              # for radio
              else:
                  response_summary[question][answer] += 1
    
    return response_summary