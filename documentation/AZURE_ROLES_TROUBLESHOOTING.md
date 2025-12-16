# Azure AD Roles & Groups Troubleshooting Guide

## Issue: Admin Role Not Returned in OAuth2 Flow

### Problem Description

When authenticating with Azure AD, you may notice that:
- **OIDC Flow**: Returns user roles correctly (e.g., `["user", "admin"]`)
- **OAuth2 Flow**: Only returns default role (e.g., `["user"]`)

This happens even when testing with the same user account.

### Root Cause

The difference occurs because of how each flow retrieves user information:

#### OAuth2 Flow
1. Exchanges authorization code for **access token only**
2. Calls Microsoft Graph API (`/v1.0/me`) to get user profile
3. By default, Graph API **does not include group memberships** in the response
4. Without groups, the role service cannot map groups to roles

#### OIDC Flow
1. Exchanges authorization code for **access token + id_token**
2. ID token contains user claims including `groups` array
3. No additional API call needed - groups are already in the token
4. Role service can immediately map groups to roles

### Solution

This implementation includes multiple strategies to handle this:

#### Strategy 1: Configure Group Claims in ID Token (OIDC Only)

For OIDC flow, enable group claims in Azure AD:

1. Go to Azure Portal → App registrations → Your app
2. Navigate to "Token configuration"
3. Click "Add groups claim"
4. Select the group types to include
5. Choose "Group ID" as the format

**Result**: Groups will be included in the ID token automatically.

#### Strategy 2: Request Graph API Permissions (OAuth2)

For OAuth2 flow to fetch groups via API:

1. Go to Azure Portal → App registrations → Your app
2. Navigate to "API permissions"
3. Click "Add a permission" → Microsoft Graph → Delegated permissions
4. Add: `GroupMember.Read.All` or `Directory.Read.All`
5. **Important**: Click "Grant admin consent for [Your Tenant]"

Update your environment configuration:
```env
AZURE_OAUTH2_SCOPES=https://graph.microsoft.com/User.Read https://graph.microsoft.com/GroupMember.Read.All
```

**Result**: The application can call `/me/memberOf` endpoint to retrieve groups.

#### Strategy 3: Fallback to Access Token Claims (Automatic)

The application automatically falls back to extracting role information from the access token itself:

**Access Token Claims Used:**
- `groups`: Array of group IDs (if configured to be included in tokens)
- `wids`: Windows Identity Directory Service role template IDs (built-in Azure AD roles)

**Example `wids` values:**
- `62e90394-69f5-4237-9190-012177145e10`: Global Administrator
- `b79fbf4d-3ef9-4689-8143-76b194e85509`: Security Administrator

This fallback works without any additional configuration or API permissions.

## Comparing Token Contents

### OAuth2 Flow Response

```json
{
  "access_token": "eyJ0eXAi...EXAMPLE_TOKEN_TRUNCATED",
  "token_type": "Bearer",
  "user": {
    "id": "501b4bea-54ee-42c6-b8b5-df24904dd4fc",
    "provider": "azure",
    "username": "arun.srihari@hotmail.com",
    "email": "arun.srihari@hotmail.com",
    "name": "Arun N",
    "roles": ["user"]  // ⚠️ Missing admin role
  },
  "id_token": null,
  "refresh_token": null
}
```

**Why `admin` role is missing:**
- No groups retrieved from Graph API (insufficient permissions)
- Fallback didn't find matching groups in access token
- User is not in `AZURE_ADMIN_GROUPS` environment variable

### OIDC Flow Response

```json
{
  "access_token": "eyJ0eXAi...EXAMPLE_TOKEN_TRUNCATED",
  "token_type": "Bearer",
  "user": {
    "id": "aO0DyTtKANfk5NRvjOPJXFz4Cz61Ybpl6HNxq9GxJzM",
    "provider": "azure",
    "username": "arun.srihari@hotmail.com",
    "email": "arun.srihari@hotmail.com",
    "name": "Arun N",
    "roles": ["user", "admin"]  // ✅ Admin role present
  },
  "id_token": "eyJ0eXAi...EXAMPLE_TOKEN_TRUNCATED",
  "refresh_token": "1.Ab4Ae4...EXAMPLE_TOKEN_TRUNCATED"
}
```

**Why `admin` role is present:**
- ID token contains `groups` claim: `["a2cf1588-...", "8797ed04-..."]`
- One of these groups is configured in `AZURE_ADMIN_GROUPS` environment variable
- Role service successfully mapped group to admin role

## Configuration Steps

### 1. Identify Your Admin Groups

Decode your ID token to find group IDs:
```bash
# The groups claim in ID token looks like:
"groups": [
  "a2cf1588-91c2-4894-a1ae-d1687e2024c7",
  "8797ed04-28e6-4e92-850a-2c455a4340e9"
]
```

### 2. Update Environment Variables

Add the group IDs to your `.env` file:

```env
# Azure Admin Configuration
AZURE_ADMIN_GROUPS=a2cf1588-91c2-4894-a1ae-d1687e2024c7,8797ed04-28e6-4e92-850a-2c455a4340e9
AZURE_ADMIN_USERNAMES=arun.srihari@hotmail.com,another.admin@domain.com

# For OAuth2 flow to fetch groups
AZURE_OAUTH2_SCOPES=https://graph.microsoft.com/User.Read https://graph.microsoft.com/GroupMember.Read.All
```

### 3. Grant Admin Consent (For OAuth2)

If using OAuth2 flow and want to fetch groups via Graph API:

1. Azure Portal → App registrations → Your app → API permissions
2. Ensure `GroupMember.Read.All` is listed
3. Click "Grant admin consent for [Your Tenant]"
4. Confirm the consent

**Note**: This requires Azure AD admin privileges.

### 4. Test Both Flows

Test OAuth2:
```bash
curl http://localhost:8001/api/v1/auth/oauth2/azure/login
```

Test OIDC:
```bash
curl http://localhost:8001/api/v1/auth/oidc/azure/login
```

## Implementation Details

### Code Flow for OAuth2

```python
# In azure_service.py - get_user_info() method

async def get_user_info(self, access_token: str) -> dict[str, Any]:
    # 1. Fetch basic user profile
    user_info = await graph_api.get("/v1.0/me")
    
    # 2. Try to fetch groups from Graph API
    try:
        groups = await graph_api.get("/v1.0/me/memberOf")
        user_info["groups"] = [g["id"] for g in groups["value"]]
    except Exception:
        # 3. Fallback: Extract from access token claims
        token_claims = decode_jwt(access_token)
        user_info["groups"] = token_claims.get("groups", []) or token_claims.get("wids", [])
    
    return user_info
```

### Role Assignment Logic

```python
# In role_service.py - _get_azure_roles() method

def _get_azure_roles(self, user_data: dict[str, Any]) -> list[str]:
    roles = []
    
    # Check if user email is in admin list
    if user_data.get("email") in AZURE_ADMIN_USERNAMES:
        roles.append("admin")
    
    # Check if user is in any admin group
    user_groups = user_data.get("groups", [])
    admin_groups = AZURE_ADMIN_GROUPS.split(",")
    
    if any(group in admin_groups for group in user_groups):
        roles.append("admin")
    
    return roles
```

## Recommended Approach

For **production environments**, we recommend:

1. **Use OIDC flow** for applications that need role/group information
   - More efficient (no additional API calls)
   - More reliable (groups embedded in token)
   - Better user experience (faster authentication)

2. **Configure token claims** in Azure AD
   - Enable group claims in token configuration
   - Reduces API dependencies
   - Works offline once token is issued

3. **Use OAuth2 flow** only when:
   - You don't need role/group information
   - You need maximum compatibility
   - You're building a pure resource access application

## Debugging Tips

### 1. Decode Your Tokens

Use [jwt.io](https://jwt.io) or [jwt.ms](https://jwt.ms) to decode and inspect tokens:

```bash
# Copy the access_token or id_token from response
# Paste into jwt.io decoder
# Check for these claims:
# - groups: Array of group GUIDs
# - wids: Array of directory role IDs
# - roles: Array of app role values
```

### 2. Check Graph API Response

Test Graph API manually:
```bash
# Replace <YOUR_ACCESS_TOKEN> with your actual token from the auth response
curl -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  https://graph.microsoft.com/v1.0/me/memberOf
```

**Expected response:**
```json
{
  "value": [
    {
      "@odata.type": "#microsoft.graph.group",
      "id": "8797ed04-28e6-4e92-850a-2c455a4340e9",
      "displayName": "Administrators"
    }
  ]
}
```

**Error response (insufficient permissions):**
```json
{
  "error": {
    "code": "Authorization_RequestDenied",
    "message": "Insufficient privileges to complete the operation."
  }
}
```

### 3. Enable Debug Logging

Set environment variable:
```env
LOG_LEVEL=DEBUG
```

Check logs for:
```
INFO: OAuth2 auth successful: arun.srihari@hotmail.com
DEBUG: User groups: ['8797ed04-...', 'a2cf1588-...']
DEBUG: Assigned roles: ['user', 'admin']
```

## Summary

| Flow | Groups Source | Requires Admin Consent | API Calls | Recommended |
|------|--------------|----------------------|-----------|-------------|
| **OIDC** | ID token claims | No | 0 | ✅ Yes |
| **OAuth2** | Graph API | Yes | 1-2 | ⚠️ Only if needed |
| **OAuth2 Fallback** | Access token claims | No | 1 | ✅ Acceptable |

**Key Takeaway**: For role-based access control with Azure AD, prefer OIDC flow with configured group claims for best performance and reliability.

