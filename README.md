# Django Authentication Project

This project is a Django-based web application that implements multiple authentication mechanisms, including session and token-based authentication. The project supports both web and mobile clients, with rate-limited login functionality to protect against brute-force attacks.

## Key Features

- **Django-based Authentication**: Provides both session-based authentication for traditional web applications and token-based authentication for APIs.
- **React Frontend Integration**: Implements React for the frontend, supporting session authentication and token authentication.
- **Mobile Authentication with React Native**: Offers token-based authentication specifically for mobile clients using React Native.
- **Rate-Limiting on Login**: Prevents brute-force login attempts by limiting users to 3 failed login attempts per minute using the `django-ratelimit` package.
- **WebSocket Support for Messaging**: Uses Django Channels to enable real-time messaging through WebSockets.
- **Serverless PostgreSQL Database**: Leverages a serverless PostgreSQL instance for cloud-based database management.
- **Django Templates for UI**: Supports traditional Django template rendering for pages that don’t require a SPA (Single Page Application) setup.

## Technologies Used

- **Backend**:
  - Django (authentication, views, forms)
  - Django REST Framework (token authentication for APIs)
  - Django Channels (WebSocket integration)
  - django-ratelimit (rate limiting)
  - Celery & Redis (background tasks)
  - Serverless PostgreSQL (cloud-based database)

- **Frontend**:
  - React (single-page application with authentication)
  - React Native (mobile app authentication)
  
- **WebSockets**: Real-time messaging system using WebSockets.
  
- **Security**: Brute-force attack prevention via rate limiting on login attempts.

## Project Setup

### Requirements

- Python 3.x
- Django 4.x
- PostgreSQL (serverless option preferred)
- Redis (for background tasks and WebSockets)
- Node.js and npm/yarn (for React)
- Django Channels (for WebSocket support)

### Installation

1. **Clone the repository**:

   ```bash
   git clone this_project
   cd django-auth-project
   ```

2. **Install dependencies**:

   Set up a virtual environment and install the required Python packages:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Node dependencies for React**:

   If you are using React as a frontend, you will need to install the Node.js dependencies:

   ```bash
   cd frontend
   npm install  # or yarn install
   ```

4. **Environment Variables**:

   Create a `.env` file for environment variables (e.g., secret keys, database connection strings, etc.). Add the following:

   ```bash
   SECRET_KEY=your-secret-key
   DEBUG=True
   DATABASE_URL=your-database-url
   ```

5. **Run Database Migrations**:

   Apply the database migrations to set up the required tables:

   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser**:

   Create an admin account for managing the Django admin interface:

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**:

   Run the Django development server:

   ```bash
   python manage.py runserver
   ```

8. **Run WebSocket Server**:

   If you're using WebSockets, run Django Channels with Redis:

   ```bash
   daphne -u /tmp/daphne.sock project.asgi:application
   ```

9. **Run React Development Server** (Optional):

   If you're using React, start the development server:

   ```bash
   cd frontend
   npm start  # or yarn start
   ```

### Token Authentication for Mobile

The project includes support for token-based authentication to integrate with mobile clients using React Native. You can retrieve a token by sending a POST request to the `/api-token-auth/` endpoint with valid credentials.

### Rate Limiting Login Attempts

The login view is protected from brute-force attacks using `django-ratelimit`. Users are allowed 3 attempts per minute before their IP is temporarily blocked.

**Code Example (Login View)**:

```python
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

class LoginView(FormView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    success_url = reverse_lazy("home")

    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
```

### Real-Time Messaging with WebSockets

WebSocket functionality is implemented using Django Channels. Users can send and receive messages in real-time through WebSocket connections.

### Serverless PostgreSQL Integration

The project leverages a serverless PostgreSQL database for scalability and cost-effectiveness. Ensure that your database URL is correctly set in the `.env` file.

## Testing

To run the tests for the project, use github workflows

## Deployment

For production deployment, it is recommended to:

- Use a cloud-based service for Django (e.g., Heroku, DigitalOcean).
- Configure Django Channels and Redis for WebSocket support.
- Secure the application with HTTPS, proper security settings, and rate-limiting.
- Set up a production PostgreSQL database instance (serverless or managed).

### Deployment with Gunicorn and Daphne

1. **Install Gunicorn**:

   ```bash
   pip install gunicorn
   ```

2. **Run the Production Server**:

   ```bash
   gunicorn --workers 3 project.wsgi
   ```

   For WebSockets, use Daphne with Django Channels:

   ```bash
   daphne -b 0.0.0.0 -p 8001 project.asgi:application
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.