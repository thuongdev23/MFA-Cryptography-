*************
Note : You need Docker Desktop running 
*************
I am using Docker for easy reproduce the program so you just need to run this line in the terminal at the root path of the folder

docker compose up --build


*************
In case docker not working properly then you can run in manually following these steps
*************

How the system work:
1. Register with email + password
2. Scan QR with Authenticator (Using Google Authenticator APP)
3. Login
4. Enter OTP
5. Check biometric
6. Access dashboard


*************
How to run backend:

cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload


*************
How to run frontend:

cd frontend
npm install
npm run dev


************
How to run database 

Go to your project folder where schema.sql is located.
Open terminal
psql -U postgres
CREATE DATABASE mfa_system;
\q
psql -U postgres -d mfa_system -f database_schema.sql
