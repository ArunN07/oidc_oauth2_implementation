# OAuth2/OIDC Setup Guide for Beginners

This guide will walk you through setting up OAuth2/OpenID Connect (OIDC) authentication for your application using popular identity providers: GitHub, Azure AD, Google, and Auth0. Each section provides step-by-step instructions for a novice user to get started.

**Note:** These instructions are current as of December 2025. Provider interfaces may change over time, so always refer to the official documentation for the latest steps.

## General Prerequisites

Before starting:
1. Have a valid email address
2. Create accounts with the providers you want to use
3. Understand that OAuth2/OIDC is about delegating authentication to these providers
4. Your application will need a redirect URI (usually `http://localhost:8000/callback` for development)

---

## GitHub OAuth2 Setup

GitHub provides OAuth2 (not full OIDC) authentication. It's great for developer-focused applications.

### 1. Register in GitHub
- Go to [github.com](https://github.com)
- Click "Sign up" and create a free account
- Verify your email address

### 2. Create OAuth Application
1. Go to your GitHub profile → Settings (gear icon)
2. Scroll down to "Developer settings" in the left sidebar
3. Click "OAuth Apps"
4. Click "New OAuth App" (or "Register a new application")
5. Fill in the form:
   - **Application name**: Your app's name (e.g., "My Awesome App")
   - **Homepage URL**: Your app's website (e.g., `http://localhost:8000` for development)
   - **Application description**: Brief description
   - **Authorization callback URL**: `http://localhost:8000/auth/github/callback` (adjust for your app)

### 3. Get Client ID and Client Secret
- After creating the app, you'll see:
  - **Client ID**: A long string (keep this safe!)
  - **Client Secret**: Another string (keep this very secret!)
- These are displayed once - save them securely

### 4. Assign Users
- GitHub OAuth2 doesn't require pre-assigning users
- Any GitHub user can authenticate with your app if they have a GitHub account
- Users authenticate themselves when they click "Login with GitHub"

### 5. Assign Roles/Permissions
- GitHub uses "scopes" instead of roles
- Common scopes: `read:user`, `user:email`, `repo`
- Set scopes in your app's OAuth configuration
- Users grant these permissions during authentication

### Testing Your Setup
- Use your Client ID and Secret in your application's configuration
- Test login flow: Users will be redirected to GitHub, then back to your app

**Documentation:** [GitHub OAuth Apps](https://docs.github.com/en/developers/apps/building-oauth-apps)

---

## Azure AD (Microsoft) OIDC Setup

Azure Active Directory provides full OIDC support with enterprise features.

### 1. Register in Azure
1. Go to [azure.microsoft.com](https://azure.microsoft.com)
2. Click "Free account" or "Start free"
3. Sign up with your email (creates an Azure AD tenant)
4. Verify your email and complete setup

### 2. Create Application
1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Azure Active Directory" and select it
3. In the left menu: "App registrations"
4. Click "New registration"
5. Fill in:
   - **Name**: Your app's name
   - **Supported account types**: Choose based on your needs (single tenant, multi-tenant, etc.)
   - **Redirect URI**: Add `http://localhost:8000/auth/azure/callback` (Web platform)

### 3. Get Client ID and Client Secret
- After registration:
  - **Application (client) ID**: Found in "Overview" tab (this is your Client ID)
- To create Client Secret:
  1. Go to "Certificates & secrets" in the left menu
  2. Click "New client secret"
  3. Add description and expiration
  4. **Value** field is your Client Secret (copy immediately - it disappears!)

### 4. Assign Users
1. In Azure AD: Go to "Users" in left menu
2. Click "New user"
3. Fill in user details (name, email, etc.)
4. Users can be assigned to groups or directly to applications

### 5. Assign Roles
1. In your app registration: Go to "App roles" in left menu
2. Click "Create app role"
3. Define roles (e.g., "Admin", "User", "Viewer")
4. Assign roles to users:
   - Go to "Enterprise applications"
   - Find your app
   - Go to "Users and groups"
   - Add users and assign roles

### 6. Configure API Permissions for Group Access (Important!)

**For OAuth2 Flow:**
To retrieve user group memberships via Microsoft Graph API, you need additional permissions:

1. In your app registration: Go to "API permissions"
2. Click "Add a permission" → "Microsoft Graph" → "Delegated permissions"
3. Add these permissions:
   - `User.Read` (basic user profile - already included)
   - `GroupMember.Read.All` (to read user's group memberships)
4. Click "Grant admin consent" (requires admin privileges)
   - This is **critical** - without admin consent, the app cannot read groups

**For OIDC Flow:**
Groups are automatically included in the ID token if configured:

1. In your app registration: Go to "Token configuration"
2. Click "Add groups claim"
3. Select group types to include (Security groups, Directory roles, etc.)
4. Choose "Group ID" format
5. Save the configuration

**Important Difference:**
- **OAuth2 Flow**: Makes API calls to Microsoft Graph to fetch groups (requires `GroupMember.Read.All` scope with admin consent)
- **OIDC Flow**: Groups are embedded in the ID token (requires token configuration but no additional API permissions)

**Fallback Mechanism:**
If OAuth2 flow cannot fetch groups from Graph API (due to insufficient permissions), the application will attempt to extract directory role IDs from the access token's `wids` claim as a fallback.

### Testing Your Setup
- Use Application ID as Client ID, and Client Secret value
- Test with Azure AD users in your tenant
- Verify group/role claims are present in responses

**Documentation:** 
- [Azure AD App Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Azure AD Group Claims](https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-optional-claims)

---

## Google OIDC Setup

Google provides full OIDC support through Google Cloud Platform.

### 1. Register in Google Cloud
1. Go to [cloud.google.com](https://cloud.google.com)
2. Click "Get started" or "Sign in"
3. Create a Google account if you don't have one
4. Set up a Google Cloud project (free tier available)

### 2. Create OAuth Application
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create one)
3. In the left menu: "APIs & Services" → "Credentials"
4. Click "Create Credentials" → "OAuth 2.0 Client IDs"
5. If prompted, configure OAuth consent screen first:
   - **User Type**: External (for public apps) or Internal (Google Workspace only)
   - Fill in app name, email, etc.
6. Then create OAuth client:
   - **Application type**: Web application
   - **Name**: Your app name
   - **Authorized redirect URIs**: Add `http://localhost:8000/auth/google/callback`

### 3. Get Client ID and Client Secret
- After creation, you'll see:
  - **Client ID**: A long string ending in `.googleusercontent.com`
  - **Client Secret**: Another string
- Download the JSON file or copy these values

### 4. Assign Users
- Google OAuth2/OIDC doesn't require pre-assigning users
- Any Google account holder can authenticate
- For Google Workspace: Users in your organization can authenticate

### 5. Assign Roles/Permissions
- Google uses "scopes" for permissions
- Common scopes: `openid`, `profile`, `email`
- Set scopes in your OAuth configuration
- For Google Workspace: Use admin console to manage user roles

### Testing Your Setup
- Use the Client ID and Client Secret in your app
- Test login: Users authenticate via Google, then return to your app

**Documentation:** [Google OAuth2 Setup](https://developers.google.com/identity/protocols/oauth2)

---

## Auth0 OIDC Setup

Auth0 is a dedicated identity platform providing full OIDC support with advanced features.

### 1. Register in Auth0
1. Go to [auth0.com](https://auth0.com)
2. Click "Sign Up" (free tier available)
3. Create account with email and password
4. Verify your email

### 2. Create Application
1. Log into [Auth0 Dashboard](https://manage.auth0.com)
2. In the left menu: "Applications" → "Applications"
3. Click "Create Application"
4. Choose:
   - **Name**: Your app name
   - **Application Type**: Regular Web Application (or SPA for frontend)
5. Click "Create"

### 3. Get Client ID and Client Secret
- In your application settings:
  - **Client ID**: Displayed at the top (public identifier)
  - **Client Secret**: In the "Basic Information" section (keep secret!)
- Copy these values

### 4. Assign Users
1. In Auth0 Dashboard: "User Management" → "Users"
2. Click "Create User"
3. Fill in email, password, etc.
4. Users can also sign up themselves if you enable it

### 5. Assign Roles
1. Go to "User Management" → "Roles"
2. Click "Create Role"
3. Define role name and description
4. Add permissions if needed
5. Assign roles to users:
   - Go to a user's profile
   - Click "Roles" tab
   - Assign roles

### Testing Your Setup
- Use Domain, Client ID, and Client Secret in your app configuration
- Test login flow through Auth0's hosted login page

**Documentation:** [Auth0 Applications](https://auth0.com/docs/get-started/auth0-overview/create-applications)

---

## Common Configuration in Your Application

After getting your credentials, configure your application (example for a Python FastAPI app):

```python
# Example configuration
OAUTH_PROVIDERS = {
    "github": {
        "client_id": "your_github_client_id",
        "client_secret": "your_github_client_secret",
        "redirect_uri": "http://localhost:8000/auth/github/callback"
    },
    "google": {
        "client_id": "your_google_client_id",
        "client_secret": "your_google_client_secret",
        "redirect_uri": "http://localhost:8000/auth/google/callback"
    },
    "azure": {
        "client_id": "your_azure_client_id",
        "client_secret": "your_azure_client_secret",
        "redirect_uri": "http://localhost:8000/auth/azure/callback",
        "tenant_id": "your_azure_tenant_id"
    },
    "auth0": {
        "domain": "your_auth0_domain.auth0.com",
        "client_id": "your_auth0_client_id",
        "client_secret": "your_auth0_client_secret",
        "redirect_uri": "http://localhost:8000/auth/auth0/callback"
    }
}
```

## Security Best Practices

1. **Never commit secrets to code** - Use environment variables
2. **Use HTTPS in production** - OAuth requires secure redirects
3. **Validate all tokens** - Always verify JWT signatures
4. **Limit scopes** - Request only necessary permissions
5. **Monitor usage** - Check provider dashboards for activity

## Troubleshooting

- **"Invalid redirect URI"**: Make sure the URI matches exactly what you registered
- **"Client secret invalid"**: Double-check you copied the secret correctly
- **"Scope not allowed"**: Ensure scopes are enabled in provider settings
- **"User not found"**: For enterprise providers, ensure user exists in the tenant

## Next Steps

Once set up, you can:
- Implement login/logout flows in your application
- Handle token refresh for long-lived sessions
- Add user profile information to your app
- Implement role-based access control

For more advanced features, check each provider's documentation for features like:
- Social login connections
- Multi-factor authentication
- Custom user databases
- API authorization

---

*This guide is for educational purposes. Always follow each provider's terms of service and security guidelines.*
