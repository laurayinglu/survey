from flask import *
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from init_db import *

app = Flask(__name__)

app.secret_key = env.get("FLASK_SECRET")


# AUTH0
# AUTH0 reference: https://auth0.com/docs/quickstart/webapp/python/01-login

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

@app.route("/login")
def login():
    # return a flask object redirecting a html
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.before_first_request
def initialize():
  setup()
  # init_table only called once at the beginning to create the table
  # init_table()

# all survey questions dict
questions_dict = {"booking_website": "Which website do you use most when buying flight tickets?", 
    "email":"Email:", 
    "name":"Name:", 
    "travel_frequency":"How often do you book travel-related services (flights, hotels, etc.)?", 
    "payment_method": "How do you prefer to pay for your travel bookings? (can choose multiple)",
    "other_payment_answer": "Please specify other payment methods:",
    "preferred_hotel":"What are your preferred Hotel(s)?",
    "hotel_like_most":"What do you like most about the hotel you selected?",
    }

#  the root page describes the survey and asks the user to consent to participate.
# It has two buttons at the bottom: “consent” (go to /survey) and “decline” (go to /decline).
@app.route("/")
def index():
  # if not session.get("user"):
  #   return redirect("/")
  return render_template("index.html")


# /survey
# asks the user a few questions, then a “next” button (go to /thanks). The input types must include:
# text input – this field is “required” and has a minimum length of 3 characters. The user cannot proceed without filling it out – use html5 validation.
# a group of 3 or more radio buttons
# select box with 3 or more options
# checkbox
# finally, there must be one “conditional” field of type textarea that appears or disappears depending on the state of the checkbox input.
@app.route('/survey', methods=['GET', 'POST'])
def survey():
  if request.method == 'POST':
    response_dict = {}
    for question in request.form:
        if question == "submit":
            continue
        # if it's checkbox
        elif question == "payment_method":
          print(request.form.getlist(question)) # this is list ['paypal','credit card']
          pm = ','.join(request.form.getlist(question))
          response_dict[question] = pm
        else:
          response_dict[question] = request.form[question]
    
    add_survey_res(response_dict)
    return redirect(url_for('thanks'))

  return render_template('survey.html')



# /decline - a page that says “thanks anyway” or something like that
@app.route('/decline', methods=['GET'])
def decline():
  return render_template('decline.html')


# /thanks - says thank you to the user for completing the survey
@app.route('/thanks', methods=['GET'])
def thanks():
  return render_template('thanks.html')


@app.route('/api/results', methods=['GET'])
def get_all_survey_responses():
  res = get_survey_res()
  reverse = request.args.get('reverse', False)
  if reverse:
      res = get_survey_res(True)
  else:
      res = get_survey_res()
      
  return render_template('survey_res.html', res=res, questions_dict=questions_dict)


@app.route('/admin/summary', methods=['GET'])
def get_survey_summary():
  res = get_survey_res()
  questionMap = {
      "booking_website": ["Expedia", "Booking.com", "priceline", "Kayak"],
      "travel_frequency": ["Rarely", "Once a year","Twice a year", "More than twice a year"],
      "preferred_hotel": ["Four Seasons Hotel", "Hilton Hotel","Holiday Inn Express", "The Plaza Hotel"],
      "payment_method": ["Credit Card", "Debit Card", "Paypal", "Other"]
  }

  responsesSummary = summarize_responses(res, questionMap)
  
  time_series_chart = get_time_series_chart()
  # return(jsonify(res)) 
  return render_template('survey_summary.html', questionMap=questionMap, responsesSummary=responsesSummary, responses=res, questions_dict=questions_dict, time_series_chart=time_series_chart)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')
