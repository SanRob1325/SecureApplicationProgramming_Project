# SecureApplicationProgramming_Project

# SecurePass: Secure Password Management
SecurePass is a secure credential management web application buil with Flask and rendering HTML templates

## Prequisites
- Python 3.8 >onwards
- pip
- Virtual Environment

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/SanRob1325/SecureApplicationProgramming_Project.git
cd SecureApplicationProgramming_Project

### 2. Create Virtual Environment

python3 -m venv venv
source venv/bin/activate # On Windows it's `venv\Scripts\activate`

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Configure Environment
copy .env.example to .env


### 5. Initialise Database
flask db upgrade

### 6. 
flask run or python run.py

### 7. Run Tests
python -m pytest