from typing import List
import os
import firebase_admin
from firebase_admin import credentials, auth

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.oauth2 import id_token
from google.auth.transport import requests
from google.cloud import firestore
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Form
import datetime
from fastapi import Query
from query import get_ev_info_from_data_source, get_ev_info_from_data_source1,update_ev_data, update_ev_data_reviews,get_reviews_for_ev,calculate_average_score
app = FastAPI()
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")

if FIREBASE_CRED_PATH and not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(FIREBASE_CRED_PATH))

firestore_db = firestore.Client(database=os.getenv("FIRESTORE_DATABASE", "(default)"))
fire_base_request_adapter = requests.Request()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Review(BaseModel):
    user_id: str
    rating: int
    comment: str
    timestamp :str

class EVData(BaseModel):
    model: str
    manufacturer: str
    year: int
    battery_size: float
    wltp_range: int
    cost: float
    power: int
    reviews: List[Review]= []

def validate_firebase_token(id_token_str):
    if not id_token_str:
        return None
    try:
        decoded = auth.verify_id_token(id_token_str)
        # keep your existing expectation: user_token['user_id']
        decoded["user_id"] = decoded.get("uid")
        return decoded
    except Exception as err:
        print(str(err))
        return None


def get_user(user_token):
    user = firestore_db.collection('user').document(user_token['user_id'])
    if not user.get().exists:
        user_data = {'name': 'sudhansh', 'age': 20}
        firestore_db.collection('user').document(user_token['user_id']).set(user_data)
    return user

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    error_message = "no error here"
    user_token = validate_firebase_token(id_token)
    

    evs_collection = firestore_db.collection('electric_vehicles')
    evs = evs_collection.stream()
    ev_list = [ev.to_dict() for ev in evs]
    if not user_token:
        return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message': None, 'user_info': None, 'ev_list': ev_list})

    user = get_user(user_token)

    return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message': None, 'user_info': user.get().to_dict(), 'ev_list': ev_list})

@app.get("/add-ev", response_class=HTMLResponse)
async def add_ev(request: Request):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    if not user_token:
       return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message': None, 'user_info': None, 'ev_list': None})

    
    
    return templates.TemplateResponse('add_vehicles.html',  {'request': request, 'user_token': user_token, 'error_message': None, 'user_info': None, 'ev_list': None})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/add-ev")
async def add_ev_post(request: Request, ev_data: EVData):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    ev_ref = firestore_db.collection('electric_vehicles').document()
    
    # Validate the received data using the Pydantic model
    ev_data_dict = ev_data.dict()
    evs_collection = firestore_db.collection('electric_vehicles')
    evs = evs_collection.stream()
    for ev in evs :
        if ev.get('model') == ev_data_dict['model']:
         
         return JSONResponse(status_code=400, content={"error": "Same model name cannot be added"})
    # Check if reviews data is empty, and handle accordingly
    if "reviews" in ev_data_dict and not ev_data_dict["reviews"]:
        del ev_data_dict["reviews"]
    if ev_ref.set(ev_data_dict):
        return JSONResponse(status_code=200, content={"message": "EV added successfully"})
    else:
        return JSONResponse(status_code=500, content={"error": "Failed to add EV"})

@app.get("/query-ev", response_class=HTMLResponse)
async def query_ev_form(request: Request):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    evs_collection = firestore_db.collection('electric_vehicles')
    evs = evs_collection.stream()
    ev_list = [ev.to_dict() for ev in evs]
    
   
    return templates.TemplateResponse('main.html', {'request': request,'user_token': user_token, 'error_message': None, 'ev_list': ev_list})

@app.post("/query-ev")
async def query_ev_post(
    request: Request,
    attribute: str = Form(None),
    value: str = Form(None),
    min_range: int = Form(None),
    max_range: int = Form(None),
):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    evs_collection = firestore_db.collection('electric_vehicles')
    evs = evs_collection.stream()
    ev_list = [ev.to_dict() for ev in evs]
 
    if attribute and (value or (min_range is not None and max_range is not None)):
        if min_range is not None and max_range is not None:
            # Perform query with range for numerical attributes
            query = evs_collection.where(attribute, '>=', min_range).where(attribute, '<=', max_range)
        else:
            # Perform query for string attributes or numerical attributes with a single value
            query = evs_collection.where(attribute, '==', value)

        evs = query.stream()
    else:
        # If no attribute specified, return all EVs
        evs = evs_collection.stream()

    ev_list = [ev.to_dict() for ev in evs]

    return templates.TemplateResponse('main.html', {'request': request, 'user_token': user_token, 'error_message': None, 'ev_list': ev_list})

@app.get("/ev-information/{ev_id}", response_class=HTMLResponse, name="ev_information")
async def ev_information(request: Request, ev_id: str):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    
    ev_info = get_ev_info_from_data_source(ev_id)
    reviews = get_reviews_for_ev(ev_id)
    evs_collection = firestore_db.collection('electric_vehicles')
    evs = evs_collection.stream()
    ev_list = [ev.to_dict() for ev in evs]
    ratings = [review['rating'] for review in reviews]

# Calculate average rating
    average_rating = "{:.2f}".format(sum(ratings) / len(reviews)) if ratings else "0.00"
    return templates.TemplateResponse('ev_information.html', {'request': request, 'ev_info': ev_info,"reviews": reviews, "average_rating": average_rating, "ev_list":ev_list,"user_token":user_token})
@app.get("/edit-ev/{ev_model}", response_class=HTMLResponse)
async def edit_ev(request: Request, ev_model: str):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    
    try:
        ev_info = get_ev_info_from_data_source(ev_model)
    except HTTPException as e:
        if e.status_code == 404:
            return templates.TemplateResponse('404.html', {'request': request, 'user_token': user_token})


    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
     
    # Render the template with the electric vehicle information for editing
    return templates.TemplateResponse('edit_vehicles.html', {'request': request, 'ev_info': ev_info, 'user_token': user_token})


@app.post("/edit-ev/{ev_model}")
async def edit_ev_post(request: Request, ev_model: str, ev_data: EVData):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get the document ID from the result of get_ev_info_from_data_source
    ev_info = get_ev_info_from_data_source(ev_model)
    document_id = ev_info['document_id']

    # Update the document using the retrieved document ID
    try:
        update_ev_data(document_id=document_id, ev_data=ev_data.dict())
        success_message = "EV details updated successfully"
        print(success_message)
    except HTTPException as e:
        print(f"Error updating EV details: {e}")
        return JSONResponse(content={"error": f"Error updating EV details: {e}"}, status_code=500)

    return JSONResponse(content={"message": success_message}, status_code=200)

@app.post("/delete-ev/{ev_model}")
async def delete_ev(request: Request, ev_model: str):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ev_info = get_ev_info_from_data_source(ev_model)

    # Check if the document exists
    if not ev_info:
        raise HTTPException(status_code=404, detail=f"Electric vehicle with model '{ev_model}' not found")

    document_id = ev_info.get('document_id')

    if not document_id:
        raise HTTPException(status_code=500, detail="Document ID not found in the electric vehicle data")

    # Delete the document using the retrieved document ID
    try:
        firestore_db.collection('electric_vehicles').document(document_id).delete()
        print("EV details deleted successfully")
    except HTTPException as e:
        print(f"Error deleting EV details: {e}")
        raise 

    return RedirectResponse(url="/", status_code=303)
@app.post("/compare-evs", response_class=HTMLResponse)
async def compare_evs(request: Request, ev1: str = Form(...), ev2: str = Form(...)):
    # Fetch details for the selected EVs (ev1 and ev2)
    ev_info1 = get_ev_info_from_data_source(ev1)
    ev_info2 = get_ev_info_from_data_source(ev2)
    reviews1 = get_reviews_for_ev(ev1)
    reviews2 = get_reviews_for_ev(ev2)

    # Calculate average scores
    average_score1 = calculate_average_score(reviews1)
    average_score2 = calculate_average_score(reviews2)

    # Determine if average_score1 is highest, lowest, or neither
    highest1 = average_score1 > average_score2
    lowest1 = average_score1 < average_score2

    # Determine if average_score2 is highest, lowest, or neither
    highest2 = average_score2 > average_score1
    lowest2 = average_score2 < average_score1

    return templates.TemplateResponse(
        'compare_vehicles.html',
        {
            'request': request,
            'ev_info1': ev_info1,
            'ev_info2': ev_info2,
            'average_score1': average_score1,
            'average_score2': average_score2,
            'highest1': highest1,
            'lowest1': lowest1,
            'highest2': highest2,
            'lowest2': lowest2,
        }
    )

def calculate_average_score(reviews):
    if not reviews:
        return 0

    ratings = [review['rating'] for review in reviews]
    average_score = sum(ratings) / len(ratings)
    return round(average_score, 2)
@app.get("/select-ev", response_class=HTMLResponse)
async def select_ev(request: Request):
    id_token = request.cookies.get("token")
    user_token = validate_firebase_token(id_token)
    
    if not user_token:
        return templates.TemplateResponse(
            'main.html',
            {'request': request, 'user_token': user_token, 'error_message': None, 'user_info': None, 'ev_list': None}
        )

    evs_collection = firestore_db.collection('electric_vehicles')
    evs = evs_collection.stream()
    ev_list = [ev.to_dict() for ev in evs]

    return templates.TemplateResponse(
        'select_vehicles.html',
        {'request': request, 'user_token': user_token, 'error_message': None, 'ev_list': ev_list}
    )
from fastapi import Request

@app.post("/submit-review/{ev_model}")
async def submit_review(request: Request, ev_model: str, review: Review):
    ev_info = get_ev_info_from_data_source1(ev_model)
            
    if not ev_info:
        raise HTTPException(status_code=404, detail=f"Electric vehicle with model '{ev_model}' not found")

    # Initialize the reviews field as an empty list if it doesn't exist
    if 'reviews' not in ev_info:
        ev_info['reviews'] = []
         

    if not hasattr(review, 'timestamp'):
        review.timestamp = get_current_timestamp()
    ev_info['reviews'].append(review)

    # Update the document with the new reviews
    update_ev_data_reviews(document_id=ev_info['document_id'], ev_data=ev_info)

    # Return a JSON response indicating success
    return JSONResponse(content={"message": "Review submitted successfully"}, status_code=200)
def get_current_timestamp():
    return datetime.datetime.utcnow().isoformat() + "Z"