
# Lab 3: Penguins Classification with XGBoost & FastAPI

This project implements a machine learning pipeline to classify penguin species using the Palmer Penguins dataset. It includes data preprocessing, XGBoost model training, and a FastAPI web API with strict input validation and logging.

---

## Setup & Installation

1. **Clone the repository & set up environment**
   
    Enter ctrl+shift+P
   
    git clone
   
    cd lab03_SarathKumar_Raju
   

    Activate virtual environment
   
    uv venv .venv
   
     **Activate**
    .venv\Scripts\activate
   
    uv pip install -r requirements.txt



---

## Training

2. **Train the XGBoost model**
    Enter 
    python train.py
    
This generates `model.json` and `encoders.json` in `app/data/

---

## Running the API

3. **Start the FastAPI server**
    Enter
   
    uvicorn app.main:app --reload
   
    
    - Visit API docs: http://127.0.0.1:8000/docs


## API Usage Examples

**Valid Prediction :**

   Content-Type: application/json" 
   
  -d "{\"bill_length_mm\":39.1,
  
        \"bill_depth_mm\":18.7,
        
        \"flipper_length_mm\":181,
        
        \"body_mass_g\":3750,
        
        \"year\":2007,
        
        \"sex\":\"male\",
        
        \"island\":\"Torgersen\"}"
