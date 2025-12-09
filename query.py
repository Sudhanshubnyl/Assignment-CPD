from datetime import datetime
from google.cloud import firestore
from fastapi import HTTPException

firestore_db = firestore.Client()

def get_ev_info_from_data_source(model: str):
   
    ev_ref = firestore_db.collection('electric_vehicles').where('model', '==', model).stream()

    for ev_doc in ev_ref:
        ev_data = ev_doc.to_dict()
        return {'document_id': ev_doc.id, **ev_data}

    raise HTTPException(status_code=404, detail=f"Electric vehicle with model '{model}' not found")

def update_ev_data(document_id: str, ev_data: dict):
    ev_ref = firestore_db.collection('electric_vehicles').document(document_id)
    ev_ref.update(ev_data)

def update_ev_data_reviews(document_id: str, ev_data: dict):
    reviews = ev_data.get('reviews', [])
    
    ev_ref = firestore_db.collection('electric_vehicles').document(document_id)
    
   
    reviews_ref = ev_ref.collection('reviews')
    for review in reviews:
        user_id = review.user_id
        rating = review.rating
        comment = review.comment
        timestamp = review.timestamp
        review_data = {'user_id': user_id, 'rating': rating, 'comment': comment,'timestamp':timestamp}
        reviews_ref.add(review_data)

def get_ev_info_from_data_source1(model: str):
    ev_ref = firestore_db.collection('electric_vehicles').where('model', '==', model).stream()

    for ev_doc in ev_ref:
        ev_data = ev_doc.to_dict()
        reviews = ev_data.get('reviews', []) 
        return {'document_id': ev_doc.id, 'reviews': reviews, **ev_data}

    raise HTTPException(status_code=404, detail=f"Electric vehicle with model '{model}' not found")
def get_reviews_for_ev(model_id: str):
   
    ev_ref = firestore_db.collection('electric_vehicles').where('model', '==', model_id).stream()

  
    ev_documents = list(ev_ref)
    if not ev_documents:
        return None  

   
    ev_document_id = ev_documents[0].id

    
    reviews_collection_path = f"electric_vehicles/{ev_document_id}/reviews"

    
    reviews_ref = firestore_db.collection(reviews_collection_path).stream()

    
    reviews = [review.to_dict() for review in reviews_ref]
    reviews_with_timestamp = [review for review in reviews if 'timestamp' in review]

   
    reviews_with_timestamp.sort(key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ"), reverse=True)

    return reviews_with_timestamp
def calculate_average_score(reviews):
    if not reviews:
        return 0

    ratings = [review['rating'] for review in reviews]
    average_score = sum(ratings) / len(reviews)
    return round(average_score, 2)
