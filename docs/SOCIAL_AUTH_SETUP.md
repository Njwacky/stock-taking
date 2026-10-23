# Social Authentication Setup Guide

This guide will help you configure social authentication for your Django application using django-allauth.

## Prerequisites

The social authentication has been installed and configured with the following providers:
- Google
- Facebook
- Twitter
- GitHub
- LinkedIn
- Microsoft

## Step 1: Environment Variables

Copy the required environment variables from `.env.example` to your `.env` file:

```bash
# Social Authentication Settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-google-client-id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-google-client-secret

SOCIAL_AUTH_FACEBOOK_KEY=your-facebook-app-id
SOCIAL_AUTH_FACEBOOK_SECRET=your-facebook-app-secret

SOCIAL_AUTH_TWITTER_KEY=your-twitter-api-key
SOCIAL_AUTH_TWITTER_SECRET=your-twitter-api-secret

SOCIAL_AUTH_GITHUB_KEY=your-github-client-id
SOCIAL_AUTH_GITHUB_SECRET=your-github-client-secret

SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY=your-linkedin-client-id
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET=your-linkedin-client-secret

SOCIAL_AUTH_MICROSOFT_GRAPH_KEY=your-microsoft-client-id
SOCIAL_AUTH_MICROSOFT_GRAPH_SECRET=your-microsoft-client-secret

# Site Configuration
SITE_DOMAIN=localhost:8000
SITE_NAME=Stock Management System
```

## Step 2: Provider Setup Instructions

### Google OAuth 2.0

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Select "Web application" as the application type
6. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/` (development)
   - `https://yourdomain.com/accounts/google/login/callback/` (production)
7. Copy the Client ID and Client Secret to your `.env` file

### Facebook Login

1. Go to the [Facebook Developers Portal](https://developers.facebook.com/)
2. Create a new app or select an existing one
3. Add "Facebook Login" product
4. In the Facebook Login settings, add valid OAuth redirect URIs:
   - `http://localhost:8000/accounts/facebook/login/callback/` (development)
   - `https://yourdomain.com/accounts/facebook/login/callback/` (production)
5. Copy the App ID and App Secret to your `.env` file

### Twitter OAuth 2.0

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new project and app
3. Set up OAuth 2.0 with the following settings:
   - Callback URLs:
     - `http://localhost:8000/accounts/twitter/login/callback/` (development)
     - `https://yourdomain.com/accounts/twitter/login/callback/` (production)
4. Copy the API Key and API Secret to your `.env` file

### GitHub OAuth

1. Go to GitHub Developer Settings > [OAuth Apps](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the application details:
   - Homepage URL: `http://localhost:8000` (development) or `https://yourdomain.com` (production)
   - Authorization callback URL:
     - `http://localhost:8000/accounts/github/login/callback/` (development)
     - `https://yourdomain.com/accounts/github/login/callback/` (production)
4. Copy the Client ID and Client Secret to your `.env` file

### LinkedIn OAuth 2.0

1. Go to the [LinkedIn Developer Portal](https://developer.linkedin.com/)
2. Create a new app
3. In the OAuth 2.0 settings, add authorized redirect URLs:
   - `http://localhost:8000/accounts/linkedin_oauth2/login/callback/` (development)
   - `https://yourdomain.com/accounts/linkedin_oauth2/login/callback/` (production)
4. Copy the Client ID and Client Secret to your `.env` file

### Microsoft Identity Platform

1. Go to the [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Fill in the application details:
   - Redirect URI:
     - `http://localhost:8000/accounts/microsoft/login/callback/` (development)
     - `https://yourdomain.com/accounts/microsoft/login/callback/` (production)
5. Copy the Application (client) ID and client secret to your `.env` file

## Step 3: Django Admin Configuration

1. Run the development server:
   ```bash
   python manage.py runserver
   ```

2. Access the Django admin at `http://localhost:8000/admin/`

3. Configure the Site:
   - Go to "Sites" > "example.com"
   - Update the domain name to match your `SITE_DOMAIN` environment variable
   - Set the display name to match your `SITE_NAME` environment variable

4. Configure Social Applications (optional - can also be done via environment variables):
   - Go to "Social accounts" > "Social applications"
   - Add applications for each provider with their respective client IDs and secrets

## Step 4: Testing the Integration

1. Restart your Django development server after making changes:
   ```bash
   python manage.py runserver
   ```

2. Navigate to your login page at `http://localhost:8000/login/`

3. Click on any of the social login buttons to test the authentication flow

4. For new users, the system will:
   - Create a new user account
   - Associate the social account with the user
   - Redirect to the dashboard

5. For existing users, the system will:
   - Authenticate the user
   - Link the social account if not already linked
   - Redirect to the dashboard

## Step 5: Production Deployment

For production deployment, ensure you:

1. Update all redirect URIs to use HTTPS
2. Set `DEBUG = False` in your settings
3. Configure proper `ALLOWED_HOSTS`
4. Set up proper email backend for verification emails
5. Use environment variables for all sensitive data
6. Ensure your domain name is properly configured in the Django admin Sites section

## Troubleshooting

### Common Issues

1. **Invalid redirect_uri error**: 
   - Check that the redirect URI in your provider console matches exactly with your Django settings
   - Ensure you're using the correct protocol (http vs https)

2. **Authentication backend not found**:
   - Verify that `AUTHENTICATION_BACKENDS` in settings includes `allauth.account.auth_backends.AuthenticationBackend`

3. **Social login buttons not working**:
   - Check that all required environment variables are set
   - Verify that the social provider apps are properly configured
   - Check browser console for JavaScript errors

4. **Email verification issues**:
   - Ensure your email backend is properly configured
   - Check that email verification settings match your requirements

### Debug Mode

Enable debug logging for django-allauth by adding to your settings:

```python
LOGGING = {
    'loggers': {
        'allauth': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Customization

### Custom User Fields

The social authentication will work with your existing User model. If you need to populate additional fields during social authentication, you can create a custom adapter:

```python
# stockT/adapter.py
from allauth.account.adapter import DefaultAccountAdapter
from .models import User

class CustomAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        # Custom username generation logic
        return super().populate_username(request, user)
```

Then update your settings:

```python
ACCOUNT_ADAPTER = 'stockT.adapter.CustomAccountAdapter'
```

### Custom Redirects

You can customize post-login redirects by setting:

```python
LOGIN_REDIRECT_URL = '/dashboard/'
SOCIALACCOUNT_LOGIN_ON_GET = True
```

## Security Considerations

1. Always use HTTPS in production
2. Keep your client secrets secure and never commit them to version control
3. Regularly rotate your client secrets
4. Monitor your authentication logs for suspicious activity
5. Implement rate limiting for authentication endpoints
6. Use proper session management settings

## Support

For more information, refer to:
- [django-allauth documentation](https://django-allauth.readthedocs.io/)
- [Provider-specific documentation](https://django-allauth.readthedocs.io/en/latest/providers.html)
- [Django authentication documentation](https://docs.djangoproject.com/en/5.2/topics/auth/)
