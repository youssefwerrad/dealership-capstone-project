# Uncomment the required imports before adding the code
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review
from datetime import datetime


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

# Create a `logout_request` view to handle sign out request


def logout_request(request):
    logout(request)  # Terminate user session
    data = {"userName": ""}  # Return empty username
    return JsonResponse(data)


# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
    # Load JSON data from the request body
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    try:
        # Check if user already exists
        User.objects.get(username=username)
        username_exist = True
    except BaseException:
        # If not, simply log this is a new user
        logger.debug("{} is new user".format(username))

    # If it is a new user
    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email)
        # Login the user and redirect to list page
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(data)
    else:
        data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(data)


def get_cars(request):
    count = CarMake.objects.filter().count()
    print(count)
    if (count == 0):
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({"CarModel": car_model.name,
                     "CarMake": car_model.car_make.name})
    return JsonResponse({"CarModels": cars})

# Update the `get_dealerships` render list of dealerships all by default,
# particular state if state is passed


def get_dealerships(request, state="All"):
    if (state == "All"):
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})

# Create a `get_dealer_reviews` view to render the reviews of a dealer


def get_dealer_reviews(request, dealer_id):
    # if dealer id has been provided
    if (dealer_id):
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        reviews = get_request(endpoint)
        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            print(response)
            review_detail['sentiment'] = response['sentiment']
        return JsonResponse({"status": 200, "reviews": reviews})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})

# Create a `get_dealer_details` view to render the dealer details


def get_dealer_details(request, dealer_id):
    if (dealer_id):
        endpoint = "/fetchDealer/" + str(dealer_id)
        dealership = get_request(endpoint)
        return JsonResponse({"status": 200, "dealer": dealership})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})

# Create a `add_review` view to submit a review

@csrf_exempt
def add_review(request):
    print("=== ADD_REVIEW CALLED ===")

    if not request.user.is_anonymous:
        data = json.loads(request.body)
        print(f"Received data: {data}")

        try:
            # Convert data types
            data["name"] = f"{request.user.first_name} {request.user.last_name}"
            data["dealership"] = int(data["dealership"])
            data["car_year"] = int(data["car_year"])
            data["purchase"] = bool(data["purchase"])

            # CRITICAL: Convert date format from YYYY-MM-DD to MM/DD/YYYY
            if "purchase_date" in data and data["purchase_date"]:
                try:
                    # Parse YYYY-MM-DD format
                    date_obj = datetime.strptime(data["purchase_date"], "%Y-%m-%d")
                    # Convert to MM/DD/YYYY format
                    data["purchase_date"] = date_obj.strftime("%m/%d/%Y")
                    print(f"Converted date: {data['purchase_date']}")
                except Exception as date_error:
                    print(f"Date conversion error: {date_error}")

            print(f"Converted data: {data}")

            # Analyze sentiment (default to neutral if service unavailable)
            data["sentiment"] = "neutral"
            if data.get("review"):
                try:
                    sentiment_response = analyze_review_sentiments(data["review"])
                    if sentiment_response and 'sentiment' in sentiment_response:
                        data["sentiment"] = sentiment_response["sentiment"]
                except:
                    pass

            # Post review to MongoDB
            print(f"Posting review to backend: {data}")
            response = post_review(data)
            print(f"Backend response: {response}")

            if response and 'error' not in response:
                return JsonResponse({
                    "status": 200,
                    "message": "Review posted successfully"
                })
            else:
                error_msg = response.get('error', 'Unknown error') if response else 'No response'
                print(f"ERROR FROM BACKEND: {error_msg}")
                return JsonResponse({
                    "status": 500,
                    "message": f"Failed: {error_msg}"
                })

        except Exception as e:
            print(f"ERROR in add_review: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "status": 401,
                "message": f"Error: {str(e)}"
            })
    else:
        return JsonResponse({
            "status": 403,
            "message": "Unauthorized"
        })
