# AI-Enhanced Chat Application with Dockerization
This is a chat application integrating with AI features. The Project is of two parts: Backend and Frontend. The project is implemented using the following resources
* `FastAPI` : to build the API endpoints
* JWT token (Auth) : to secure the endpoints
* `OpenAl`: to ensure AI capability 
* Database: `Supabase` for handling user data and chat logs.`psycopg2` adapter for connecting with the database. Raw `SQL` is used python `context manager` to implement transactions in the database 

* `Docker`:  for containerization, leveraging the backend technologies.
* `NextJS` : For frontend

# Authentication
![alt text](<Architecture.png>)

The JWT authorization workflow is as follows:
1. The end user logs in, the client application sends an authentication request to API Gateway  JWT issuer, to obtain a JWT token.
2. If API Gateway is the JWT issuer, then it validates the user or the application. If the user or application credentials are valid, API Gateway generates the JSON token using a private key that was specified in the JWT configuration, and sends the generated token to the client.
If the user credentials are invalid, API Gateway returns a specific error response.
3. Client sends the generated JSON token in the HTTP Authorization request header as a Bearer token to access the protected API in API Gateway.
4. API Gateway first identifies the application based on claims from the JWT, then validates the JWT using the public certificate of the issuer and provides access to the protected resources.
If the validation fails, API Gateway returns a specific error response.

# Database Schema
Two files for creating [user](chatai-fastapi/app/migrations/create_users_table.sql) and 
[conservation](chatai-fastapi/app/migrations/create_conversations_table.sql) tables. 
below is the SQL code (run by [python](chatai-fastapi/app/migrations/apply_migrations.py) script) and their explanation
```python
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);
```
The provided SQL script creates two tables: `users` and `conversations`. Here's a breakdown of each table's schema and a simplified ERD (Entity-Relationship Diagram):

## Table: users
- **Columns**:
  - `id`: Auto-incrementing integer representing the user's unique identifier (primary key).
  - `username`: Variable-length string (up to 50 characters) representing the user's username. It must be unique.
  - `hashed_password`: Text field storing the hashed password of the user.

## Table: conversations
- **Columns**:
  - `id`: Universally Unique Identifier (UUID) representing the conversation's unique identifier (primary key). It's generated using the `gen_random_uuid()` function.
  - `title`: Variable-length string (up to 255 characters) representing the title or name of the conversation.
  - `user_id`: Foreign key referencing the `id` column in the `users` table. It establishes a relationship between users and conversations, where each conversation is associated with a specific user. It's set to cascade on delete, meaning if a user is deleted, all associated conversations are also deleted.
  - `messages`: JSONB (Binary JSON) field storing an array of messages exchanged in the conversation. It's initialized as an empty JSON array.
  - `created_at`: Timestamp indicating the creation date and time of the conversation. It defaults to the current timestamp when a record is inserted.

## Entity-Relationship Diagram (ERD):
```
     +-------------------+
     |      users        |
     +-------------------+
     | id (PK)           |
     | username          |
     | hashed_password   |
     +-------------------+
           |
           |
           |
           |
     +-------------------+
     | conversations     |
     +-------------------+
     | id (PK)           |
     | title             |
     | user_id (FK)      |
     | messages          |
     | created_at        |
     +-------------------+
```
In this ERD:
- The `users` table has a one-to-many relationship with the `conversations` table, as one user can have multiple conversations, but each conversation belongs to only one user.
- The relationship between `users` and `conversations` is established via the `user_id` foreign key in the `conversations` table, referencing the `id` primary key in the `users` table.
- The `messages` field in the `conversations` table stores JSONB data, allowing for flexible storage of message content.

# Deployment:

1. Install Docker Desktop App and Run it 
 
    
2. Create Database	
     https://supabase.com

3.	Setup [.env](chatai-fastapi/.env)file (backend)
```.env
    DB_URL=postgres://postgres.kkvohvuyuhyxtxdeahvz:0C983qzIPL993L35@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
    SECRET_KEY=your_secret_key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    OPENAI_API_KEY=your_openai_api_key
```

4.	Run migration (if the database is new):

    goto chatai-fastapi/app/migration and run [apply_mirations.py](chatai-fastapi/app/migrations/apply_migrations.py)
    ```
        python apply_migration.py
      
    ```
N.B: steps 3-4 is a one type job. We are using online database. once the database is setup, we don't need to do steps 3-4 while deploying the application in other devices.

5.	Run docker command
```
    docker compose -f "docker-compose.yml" up -d  --build
```
You will find Database, Backend and frontend server is running in Docker Desktop Application


![alt text](image.png)



Open [http://localhost:8000] with your browser to see the backend APIs (use swagger url).

Open [http://localhost:3000] with your browser to see the whole application with frontend.
## API Endpoints and their corresponding function
 The following API endpoints are defined in `chatai-fastapi/app/auth/routes.py` 
 ### /register
```python
    
@router.post("/register", response_model=UserOut)

def register(user: UserCreate):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))
            existing_user = cursor.fetchone()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                )
            hashed_password = get_password_hash(user.password)
            cursor.execute(
                "INSERT INTO users (username, hashed_password) VALUES (%s, %s) RETURNING id, username",
                (user.username, hashed_password),
            )
            new_user = cursor.fetchone()
    return new_user

```
Code Explanation:
* `@router.post("/register", response_model=UserOut)`: This decorator registers the register function as a POST endpoint at the `/register` URL. The `response_model=UserOut` indicates that the response will be validated against the `UserOut` Pydantic model.
* `def register(user: UserCreate)`: The function register takes a single parameter user of type `UserCreate`, which is a Pydantic model representing the user registration data (username and password).
* `with get_db_connection() as conn`: This line opens a database connection using a context manager to ensure the connection is properly closed after use.
* `with conn.cursor() as cursor`: This line opens a database cursor within the context of the database connection to execute SQL queries.
* `cursor.execute`: Executes a (raw) SQL query to check if a user with the given username already exists in the database.
* `if existing_user`: Checks if a user with the given username already exists. If true, an `HTTP 400 error` is raised with a relevant message.
* `hashed_password = get_password_hash(user.password)`: Hashes the user's password using a password hashing function.
* `cursor.execute`: Executes a (raw) SQL query to insert the new user into the users table with the hashed password. The RETURNING clause fetches the id and username of the newly created user.

Summary: 
This FastAPI endpoint handles user registration by:

* Checking if the username already exists in the database.
* Hashing the user's password.
* Inserting the new user into the database.
* Returning the newly created user's ID and username, while  ensuring proper error handling and data validation.
### JWTBearer class
Before jumping to the login endpoint, the following explains how we handle the Jason Web Token
the `JWTBearer` class is defined in `chatai-fastapi/app/auth/auth_bearer.py`, it looks something like this:
```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        payload = decode_access_token(jwtoken)
        return payload is not None

```
This code defines a custom JWT authentication class, `JWTBearer`, that extends the `HTTPBearer` class provided by FastAPI. This class is used to secure endpoints by verifying the JWT token present in the `Authorization` header of incoming requests. Here’s a detailed breakdown of each part of the code:

#### Class Definition and Initialization
```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
```
- **from fastapi import Request, HTTPException**: Imports the necessary FastAPI components.
- **from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials**: Imports the `HTTPBearer` and `HTTPAuthorizationCredentials` classes from FastAPI's security module.
- **class JWTBearer(HTTPBearer)**: Defines the `JWTBearer` class, inheriting from `HTTPBearer`.
- **def __init__(self, auto_error: bool = True)**: Initializes the `JWTBearer` class. The `auto_error` parameter controls whether an automatic error response is generated for invalid tokens.
- **super(JWTBearer, self).__init__(auto_error=auto_error)**: Calls the parent class's initializer.

#### Call Method
```python
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
```
- **async def __call__(self, request: Request)**: This method is called when an incoming request is intercepted. It processes the request to extract and validate the JWT token.
- **credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)**: Calls the parent `__call__` method to extract the `Authorization` header and parse the credentials.
- **if credentials**: Checks if the credentials are present.
  - **if not self.verify_jwt(credentials.credentials)**: Calls the `verify_jwt` method to validate the token.
  - **raise HTTPException(status_code=403, detail="Invalid token or expired token.")**: Raises an HTTP 403 Forbidden error if the token is invalid or expired.
  - **return credentials.credentials**: Returns the token if it is valid.
- **else**: If no credentials are found, raises an HTTP 403 error with a different message.

#### JWT Verification Method
```python
    def verify_jwt(self, jwtoken: str) -> bool:
        payload = decode_access_token(jwtoken)
        return payload is not None
```
- **def verify_jwt(self, jwtoken: str) -> bool**: Defines the `verify_jwt` method, which takes the JWT token as a string argument.
- **payload = decode_access_token(jwtoken)**: Calls the `decode_access_token` function to decode the JWT token and retrieve the payload.
- **return payload is not None**: Returns `True` if the payload is valid (not `None`), indicating the token is valid; otherwise, returns `False`.

#### Integration with FastAPI Endpoint
When this `JWTBearer` class is used as a dependency in FastAPI endpoint, it ensures that the endpoint is protected and accessible only to requests with a valid JWT token (as we will see example in the follwing endpoints comming up next).

#### Example Endpoint
Here’s how you can use the `JWTBearer` dependency in an endpoint:
```python

@router.get("/protected", dependencies=[Depends(JWTBearer())])
def protected_route():
    return {"message": "This is a protected route"}

```
- **@router.get("/protected", dependencies=[Depends(JWTBearer())])**: Secures the `/protected` endpoint using the `JWTBearer` dependency.
- **def protected_route()**: Defines the endpoint logic, which in this case simply returns a message indicating the route is protected.

#### Summary
- **Initialization**: The `JWTBearer` class is initialized to handle JWT authentication.
- **Token Extraction**: The `__call__` method extracts the JWT token from the request’s `Authorization` header.
- **Token Verification**: The `verify_jwt` method validates the token by decoding it and checking the payload.
- **Error Handling**: If the token is invalid or missing, appropriate HTTP exceptions are raised to prevent unauthorized access.

This structure ensures that only requests with a valid JWT token can access the protected endpoint, enhancing the security of your FastAPI application.
 ### /login
This FastAPI endpoint handles user login and generates a JWT token for authentication. Here's a concise explanation of each part of the code:

#### Endpoint Declaration
```python
@router.post("/login")
def login(user: UserCreate):
```
- **@router.post("/login")**: Registers the `login` function as a POST endpoint at the `/login` URL.
- **def login(user: UserCreate)**: The function `login` takes a `user` parameter of type `UserCreate`, which is a Pydantic model containing the user's login data (username and password).

#### Database Query for User Verification
```python
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))
            user_record = cursor.fetchone()
```
- **with get_db_connection() as conn**: Opens a database connection using a context manager.
- **with conn.cursor(cursor_factory=RealDictCursor) as cursor**: Opens a cursor with `RealDictCursor` to get results as dictionaries.
- **cursor.execute**: Executes a SQL query to find a user with the provided username.
- **user_record = cursor.fetchone()**: Fetches the user's record from the database.

#### Password Verification
```python
    if not user_record or not verify_password(
        user.password, user_record["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
```
- **if not user_record or not verify_password**: Checks if the user record exists and if the provided password matches the stored hashed password.
- **verify_password(user.password, user_record["hashed_password"])**: Verifies the password using a password verification function.
- **raise HTTPException**: Raises an HTTP 401 error if the credentials are invalid.

#### JWT Token Creation
```python
    access_token = create_access_token(
        data={"id": user_record["id"], "username": user_record["username"]}
    )
```
- **create_access_token**: Generates a JWT access token with the user's ID and username as payload data.

#### Return the Token and User Info
```python
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user_record["id"], "username": user_record["username"]},
    }
```
- **return {...}**: Returns a dictionary containing the access token, token type, and user information (ID and username).

#### Summary
This FastAPI endpoint performs the following steps:
1. Queries the database to find the user by username.
2. Verifies the provided password against the stored hashed password.
3. If verification is successful, generates a JWT access token.
4. Returns the access token, token type, and user information in the response. If verification fails, it raises an HTTP 401 Unauthorized error.

 ### /protected
 This FastAPI endpoint is designed to protect a route by requiring a valid JWT token for access. Here's a detailed explanation of each part of the code:

#### Endpoint Declaration
```python
@router.get("/protected", dependencies=[Depends(JWTBearer())])
def protected(request: Request):
```
- **@router.get("/protected")**: Registers the `protected` function as a GET endpoint at the `/protected` URL.
- **dependencies=[Depends(JWTBearer())]**: This ensures that the `JWTBearer` dependency is applied to this endpoint. `JWTBearer` is (explained above) a custom dependency class that validates the JWT token before allowing access to the endpoint.
- **def protected(request: Request)**: The `protected` function takes a `request` parameter of type `Request`, which gives access to the request details, including headers.

#### JWT Token Decoding
```python
    return {
        "res": decode_access_token(
            request.headers.get("Authorization", "").split(" ")[1]
        )
    }
```
- **request.headers.get("Authorization", "").split(" ")[1]**: This extracts the JWT token from the `Authorization` header of the request.
  - **request.headers.get("Authorization", "")**: Retrieves the `Authorization` header from the request. If the header is not present, it returns an empty string.
  - **split(" ")[1]**: Splits the `Authorization` header value by spaces and retrieves the second part, which should be the token. The header value is typically in the format `Bearer <token>`.
- **decode_access_token**: This is a function that presumably decodes the JWT token and returns the payload or some other relevant information.
- **return {"res": ...}**: Returns a dictionary with the result of the `decode_access_token` function call.

#### Summary
This FastAPI endpoint does the following:
1. **Dependency Injection**: Uses the `JWTBearer` dependency to ensure that the request includes a valid JWT token. If the token is not valid, `JWTBearer` would likely raise an error, preventing access to the endpoint.
2. **Token Extraction**: Extracts the JWT token from the `Authorization` header.
3. **Token Decoding**: Decodes the JWT token to obtain the payload or other relevant information.
4. **Response**: Returns the decoded information in the response.

By using `dependencies=[Depends(JWTBearer())]` in the endpoint, FastAPI ensures that the token is verified before the request reaches the endpoint logic.

 ### /get-chat
 This FastAPI code snippet defines an endpoint that retrieves a user's chat history from a database. Here's a step-by-step explanation of each part:

#### Endpoint Declaration
```python
@router.get("/get-chat", dependencies=[Depends(JWTBearer())])
def get_user_chat_history(user_id: int, conversation_id: Optional[str] = None):
```
- **@router.get("/get-chat")**: Registers the `get_user_chat_history` function as a GET endpoint at the `/get-chat` URL.
- **dependencies=[Depends(JWTBearer())]**: Uses the `JWTBearer` dependency to ensure that the endpoint is protected and only accessible to requests with a valid JWT token.
- **def get_user_chat_history(user_id: int, conversation_id: Optional[str] = None)**: Defines the endpoint function, which takes two parameters:
  - **user_id: int**: An integer representing the user's ID.
  - **conversation_id: Optional[str] = None**: An optional string representing the conversation ID. If not provided, it defaults to `None`.

#### Database Query for Chat History
```python
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT messages FROM conversations WHERE user_id = %s AND id = %s",
                (user_id, conversation_id),
            )
            result = cursor.fetchone()
```
- **with get_db_connection() as conn**: Opens a database connection using a context manager to ensure the connection is properly closed after use.
- **with conn.cursor(cursor_factory=RealDictCursor) as cursor**: Opens a cursor with `RealDictCursor` to get query results as dictionaries.
- **cursor.execute(...)**: Executes a SQL query to select the `messages` column from the `conversations` table where the `user_id` and `id` (conversation_id) match the provided values.
- **result = cursor.fetchone()**: Fetches the first row of the result. If no matching record is found, `result` will be `None`.

#### Processing the Query Result
```python
            if result:
                messages = result.get("messages", [])
                return messages
            else:
                return []
```
- **if result**: Checks if a result was found.
  - **messages = result.get("messages", [])**: Retrieves the `messages` field from the result. If the `messages` field is not found, it defaults to an empty list.
  - **return messages**: Returns the retrieved messages.
- **else**: If no result was found (i.e., the conversation doesn't exist or doesn't belong to the specified user).
  - **return []**: Returns an empty list.

#### Summary
This FastAPI endpoint performs the following tasks:
1. **Authentication**: Uses `JWTBearer` to ensure the request includes a valid JWT token.
2. **Parameter Handling**: Accepts `user_id` and an optional `conversation_id` as query parameters.
3. **Database Connection**: Opens a connection to the database and sets up a cursor to execute SQL queries.
4. **SQL Query Execution**: Executes a query to fetch the chat messages for the specified user and conversation.
5. **Result Processing**: Checks the query result and returns the chat messages if found, otherwise returns an empty list.

#### Example Request
To call this endpoint, you would send a GET request with the required parameters and a valid JWT token:
```http
GET /get-chat?user_id=2&conversation_id=e5ed53de-40da-4b1a-82ce-f0ffdcd24e3f
Authorization: Bearer <JWT_TOKEN>
```
in swagger UI
![alt text](<Screenshot 2024-05-24 at 8.21.16 PM.png>)

conversational_id is defined as uuid  
### Example Response
- **If the conversation is found**:
  ```json
  [
        {"role":"user","content":"r u asleep?"},
        {"role":"assistant","content":"No, I am an AI and do not sleep. How can I assist you?"},
        {"role":"user","content":"when do you sleep?"},
        {"role":"assistant","content":"I do not require sleep as I am an artificial intelligence program that operates 24/7. I am always here to assist you with any questions or tasks you may have."}
  ]

  ```
  in swagger UI
  ![alt text](<Screenshot 2024-05-24 at 8.22.53 PM.png>)
  `role: user` >> user, `role:assistant` >> OpenAI
  
  in front end
  ![alt text](image-1.png)
  user adam has `user_id = 2`
- **If the conversation would not found**:
  ```json
  []
  ```
 ### /get-conversations-list
 This FastAPI endpoint is designed to retrieve a list of conversations for a user. It ensures that the request is authenticated using a JWT token. Here's a detailed explanation of each part:

#### Endpoint Declaration
```python
@router.get("/get-conversations-list", dependencies=[Depends(JWTBearer())])
def get_conversations_list(request: Request):
```
- **@router.get("/get-conversations-list")**: Registers the `get_conversations_list` function as a GET endpoint at the `/get-conversations-list` URL.
- **dependencies=[Depends(JWTBearer())]**: Uses the `JWTBearer` dependency to enforce JWT token authentication, ensuring that only authenticated users can access this endpoint.
- **def get_conversations_list(request: Request)**: Defines the function for the endpoint. It takes a single parameter:
  - **request: Request**: An instance of FastAPI's `Request` object, which provides access to the request's details, including headers.

#### Extracting User ID from JWT Token
```python
    user_id = decode_access_token(
        request.headers.get("Authorization", "").split(" ")[1]
    )["id"]
```
- **request.headers.get("Authorization", "")**: Retrieves the `Authorization` header from the request. If the header is not present, it returns an empty string.
- **split(" ")[1]**: Splits the `Authorization` header value by spaces and extracts the second part, which should be the JWT token. The header value is typically in the format `Bearer <token>`.
- **decode_access_token(...)**: Calls a function to decode the JWT token and extract the payload.
- **["id"]**: Retrieves the user ID from the decoded JWT payload.

#### Database Query for Conversations List
```python
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, title FROM conversations WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            result = cursor.fetchall()
```
- **with get_db_connection() as conn**: Opens a database connection using a context manager to ensure the connection is properly closed after use.
- **with conn.cursor(cursor_factory=RealDictCursor) as cursor**: Opens a cursor with `RealDictCursor` to get query results as dictionaries.
- **cursor.execute(...)**: Executes a SQL query to select the `id` and `title` columns from the `conversations` table where the `user_id` matches the extracted user ID. The results are ordered by the `created_at` column in descending order.
- **result = cursor.fetchall()**: Fetches all rows from the query result. Each row is a dictionary containing the `id` and `title` of a conversation.

#### Processing and Returning the Result
```python
            if result is not None:
                return result
            else:
                return []
```
- **if result is not None**: Checks if the query returned any results.
  - **return result**: Returns the list of conversations if results were found.
  - **else: return []**: Returns an empty list if no results were found.

#### Summary
This FastAPI endpoint performs the following tasks:
1. **Authentication**: Uses the `JWTBearer` dependency to ensure the request includes a valid JWT token.
2. **Extracting User ID**: Decodes the JWT token to extract the user ID.
3. **Database Connection**: Opens a connection to the database and sets up a cursor to execute SQL queries.
4. **SQL Query Execution**: Executes a query to fetch the list of conversations for the specified user, ordered by creation date in descending order.
5. **Result Processing**: Checks the query result and returns the list of conversations if found, otherwise returns an empty list.

#### Example Request
To call this endpoint, you would send a GET request with the required `Authorization` header containing a valid JWT token:
```http
GET /get-conversations-list
Authorization: Bearer <JWT_TOKEN>
```

#### Example Response
- **If conversations are found**:
  ```json
  [
        {
            "id": "e5ed53de-40da-4b1a-82ce-f0ffdcd24e3f",
            "title": "r u asleep?"
        },
        {
            "id": "c716687c-4a4e-4b65-85fd-c1f1a88a7dd3",
            "title": "hi there"
        }
    ]
  ```

  We have id for each conversation. using id we can retrive all the messages form each conversation.


- **If no conversations are found**:

  ```json
  []
  ```
  In Swagger UI
  ![alt text](image-2.png)
 ### /chat
This FastAPI endpoint allows users to send a chat message and receive a real-time response from an AI (OpenAI's GPT-3.5-turbo). Here's a detailed explanation of each part of the code:

#### Endpoint Declaration
```python
@router.post("/chat", dependencies=[Depends(JWTBearer())])
def chat(request: Request, chat: Chat):
```
- **@router.post("/chat")**: Registers the `chat` function as a POST endpoint at the `/chat` URL.
- **dependencies=[Depends(JWTBearer())]**: Uses the `JWTBearer` dependency to enforce JWT token authentication, ensuring that only authenticated users can access this endpoint.
- **def chat(request: Request, chat: Chat)**: Defines the function for the endpoint. It takes two parameters:
  - **request: Request**: An instance of FastAPI's `Request` object, providing access to the request's details, including headers.
  - **chat: Chat**: A Pydantic model `Chat` containing the chat message and optionally the conversation ID.

#### Extracting User ID from JWT Token
```python
    user_id = decode_access_token(
        request.headers.get("Authorization", "").split(" ")[1]
    )["id"]
```
- **request.headers.get("Authorization", "")**: Retrieves the `Authorization` header from the request. If the header is not present, it returns an empty string.
- **split(" ")[1]**: Splits the `Authorization` header value by spaces and extracts the second part, which should be the JWT token. The header value is typically in the format `Bearer <token>`.
- **decode_access_token(...)**: Calls a function to decode the JWT token and extract the payload.
- **["id"]**: Retrieves the user ID from the decoded JWT payload.

#### Chat Message Handling
```python
    message = chat.message
    conversation_id = chat.conversation_id
    try:
        new_conversation_id = save_chat_to_database(
            user_id=user_id,
            role="user",
            message=chat.message,
            conversation_id=conversation_id,
        )
        if new_conversation_id:
            conversation_id = new_conversation_id
```
- **message = chat.message**: Extracts the message from the `chat` object.
- **conversation_id = chat.conversation_id**: Extracts the conversation ID from the `chat` object.
- **try**: Begins a try block to handle potential errors.
- **save_chat_to_database(...)**: Saves the chat message to the database with the given user ID, role ("user"), message, and conversation ID. This function might return a new conversation ID if a new conversation is created.
- **if new_conversation_id**: If a new conversation ID is returned, it updates the `conversation_id` variable.

#### Streaming AI Response
```python
        return StreamingResponse(
            get_openai_generator(user_id=user_id, conversation_id=conversation_id),
            media_type="text/event-stream",
        )
```
- **StreamingResponse(...)**: Returns a streaming response that streams data in real-time.
- **get_openai_generator(...)**: Calls the `get_openai_generator` function to generate the response from the AI, providing the user ID and conversation ID.
- **media_type="text/event-stream"**: Specifies that the response is an event stream.

#### Error Handling
```python
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
```
- **except Exception as e**: Catches any exceptions that occur during the process.
- **raise HTTPException(...)**: Raises an HTTP 500 Internal Server Error with the exception details.

#### AI Response Generation
```python
def get_openai_generator(user_id: int, conversation_id: str | None):
    chat_history = get_user_chat_history(user_id, conversation_id=conversation_id)
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    openai_stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_history,
        temperature=0.0,
        stream=True,
    )
    assistant_message = ""
    for event in openai_stream:
        if event.choices[0].delta.content is not None:
            assistant_message += event.choices[0].delta.content
            yield f"data: {json.dumps({'message': event.choices[0].delta.content})}\n\n"
    save_chat_to_database(
        user_id, "assistant", assistant_message, conversation_id=conversation_id
    )
```
- **def get_openai_generator(user_id: int, conversation_id: str | None)**: Defines a generator function to interact with the AI and stream the response.
- **chat_history = get_user_chat_history(user_id, conversation_id=conversation_id)**: Retrieves the chat history for the given user and conversation ID.
- **client = OpenAI(api_key=Config.OPENAI_API_KEY)**: Creates an instance of the OpenAI client using the provided API key.
- **openai_stream = client.chat.completions.create(...)**: Calls the OpenAI API to generate a chat completion using the model "gpt-3.5-turbo", the retrieved chat history, and streaming enabled.
- **assistant_message = ""**: Initializes an empty string to accumulate the assistant's message.
- **for event in openai_stream**: Iterates over the events in the OpenAI stream.
  - **if event.choices[0].delta.content is not None**: Checks if the event contains new content.
  - **assistant_message += event.choices[0].delta.content**: Appends the new content to the assistant's message.
  - **yield f"data: {json.dumps({'message': event.choices[0].delta.content})}\n\n"**: Yields the new content as an event in the stream.
- **save_chat_to_database(...)**: Saves the complete assistant message to the database once the streaming is finished.

#### Summary
This FastAPI endpoint performs the following tasks:
1. **Authentication**: Uses the `JWTBearer` dependency to ensure the request includes a valid JWT token.
2. **Extracting User ID**: Decodes the JWT token to extract the user ID.
3. **Chat Message Handling**: Extracts the message and conversation ID from the request and saves the user's chat message to the database.
4. **Streaming AI Response**: Streams the AI's response in real-time using a `StreamingResponse`.
5. **Error Handling**: Catches and handles any exceptions that occur during the process, returning an HTTP 500 error if needed.
6. **AI Response Generation**: Uses the OpenAI API to generate and stream the AI's response, appending to the chat history and saving the final assistant message to the database.

video link demostration all the above endpoints:[link](https://drive.google.com/file/d/1Wl1nFPOMerzdJCFrOLr5uaVnUoTIJ9i1/view?usp=share_link) 



