# Azure AD Admin Role Detection

## Overview

The application now automatically detects Azure AD built-in administrator roles and grants "admin" privileges accordingly.

## How It Works

Azure AD assigns built-in administrator roles using **role template IDs** (also called `wids` - Windows Identity Directory Service IDs). These are included in the access token and can be used to determine if a user has administrative privileges.

### Built-in Azure AD Administrator Roles

Common administrator role IDs that can be detected:

| Role Name | Role Template ID (wid) |
|-----------|------------------------|
| Global Administrator | `62e90394-69f5-4237-9190-012177145e10` |
| Security Administrator | `b79fbf4d-3ef9-4689-8143-76b194e85509` |
| Application Administrator | `9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3` |
| User Administrator | `fe930be7-5e62-47db-91af-98c3a49a38b1` |
| Privileged Role Administrator | `e8611ab8-c189-46e8-94e1-60213ab1f814` |

[Full list of Azure AD built-in roles](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference)

## Configuration

### Environment Variable

This setting is **OPTIONAL**. By default, it's empty - no Azure AD roles automatically grant admin access.

Add the following to your `.env` file **only if** you want certain Azure AD roles to grant admin access:

```bash
# Azure Admin Role IDs (comma-separated) - OPTIONAL
# Leave empty if you don't want to use Azure AD role-based admin assignment
# Example: Global Administrator + Security Administrator
AZURE_ADMIN_ROLE_IDS=62e90394-69f5-4237-9190-012177145e10,b79fbf4d-3ef9-4689-8143-76b194e85509
```

**Important Notes:**
- These role IDs are **Microsoft-defined constants** - they're the same across ALL Azure AD tenants globally
- The Global Administrator role ID will always be `62e90394-69f5-4237-9190-012177145e10` in every Azure AD tenant
- You're not "hardcoding" tenant-specific values - these are universal identifiers
- [Full list from Microsoft documentation](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference)

### Multiple Detection Methods

The application checks for admin privileges in three ways (any match grants admin role):

1. **Email/Username Match**
   ```bash
   AZURE_ADMIN_USERNAMES=admin@company.com,user@company.com
   ```

2. **Azure AD Group Membership**
   ```bash
   AZURE_ADMIN_GROUPS=8797ed04-28e6-4e92-850a-2c455a4340e9
   ```

3. **Built-in Role IDs (wids)** ⭐ NEW!
   ```bash
   AZURE_ADMIN_ROLE_IDS=62e90394-69f5-4237-9190-012177145e10
   ```

## How Role Detection Works

### OAuth2 Flow

1. User authenticates via Azure AD
2. Application receives access token
3. Token contains `wids` claim with role template IDs
4. Application calls Microsoft Graph API `/v1.0/me`
5. Application extracts `wids` from token and adds to `groups` field
6. Role service checks if any `wid` matches configured admin role IDs
7. If match found, user is granted "admin" role

### OIDC Flow

1. User authenticates via Azure AD  
2. Application receives id_token with `groups` claim
3. If groups claim includes role template IDs, they're detected
4. Role service checks if any role ID matches configured admin role IDs
5. If match found, user is granted "admin" role

## Example Token Claims

### Access Token (OAuth2)
```json
{
  "aud": "https://graph.microsoft.com",
  "iss": "https://sts.windows.net/70f5837b-2528-4e36-91d3-b961f3bd3140/",
  "email": "arun.srihari@hotmail.com",
  "name": "Arun N",
  "oid": "501b4bea-54ee-42c6-b8b5-df24904dd4fc",
  "wids": [
    "62e90394-69f5-4237-9190-012177145e10",  // Global Administrator
    "b79fbf4d-3ef9-4689-8143-76b194e85509"   // Security Administrator
  ]
}
```

### ID Token (OIDC)
```json
{
  "aud": "aa31c194-f925-420a-87e3-81b8d6c82757",
  "iss": "https://login.microsoftonline.com/70f5837b-2528-4e36-91d3-b961f3bd3140/v2.0",
  "email": "arun.srihari@yahoo.com",
  "name": "arun.srihari",
  "groups": [
    "8797ed04-28e6-4e92-850a-2c455a4340e9",  // Custom Azure AD group
    "62e90394-69f5-4237-9190-012177145e10"   // Global Administrator role
  ]
}
```

## Response Example

When a Global Administrator logs in via OAuth2, the response will now include:

```json
{
  "access_token": "eyJ0eXAi...EXAMPLE_TOKEN_TRUNCATED",
  "token_type": "Bearer",
  "user": {
    "id": "501b4bea-54ee-42c6-b8b5-df24904dd4fc",
    "provider": "azure",
    "username": "arun.srihari_hotmail.com#EXT#@arunsriharihotmail.onmicrosoft.com",
    "email": "arun.srihari@hotmail.com",
    "name": "Arun N",
    "roles": [
      "user",
      "admin"  // ⭐ ADMIN ROLE DETECTED!
    ]
  },
  "expires_in": 5060
}
```

## Testing

### 1. Set Environment Variable
```bash
# In your .env file
AZURE_ADMIN_ROLE_IDS=62e90394-69f5-4237-9190-012177145e10
```

### 2. Restart Application
```bash
poetry run python -m src.fastapi.main
```

### 3. Login via OAuth2
Navigate to: `http://localhost:8001/api/v1/auth/oauth2/azure/login`

### 4. Check Response
You should see `"roles": ["user", "admin"]` in the response if you have the Global Administrator role.

## Default Configuration

By default, the application **does NOT** automatically recognize any Azure AD roles for admin access. This is intentional for security - you must explicitly configure which roles should grant admin privileges.

To recognize Global Administrator role:

```bash
AZURE_ADMIN_ROLE_IDS=62e90394-69f5-4237-9190-012177145e10
```

To add multiple roles:

```bash
# Recognize Global Admin, Security Admin, and User Admin
AZURE_ADMIN_ROLE_IDS=62e90394-69f5-4237-9190-012177145e10,b79fbf4d-3ef9-4689-8143-76b194e85509,fe930be7-5e62-47db-91af-98c3a49a38b1
```

### Why These Values Are Not "Hardcoded"

These role template IDs are **Microsoft-defined constants** published in their official documentation:
- They are globally unique identifiers assigned by Microsoft
- The same role ID works across ALL Azure AD tenants worldwide
- They never change (Microsoft guarantees backward compatibility)
- Think of them like HTTP status codes (404, 200, etc.) - standardized values, not hardcoded magic numbers

## Troubleshooting

### Admin role not detected?

1. **Check token claims**: Decode your access_token at [jwt.io](https://jwt.io) and verify the `wids` claim exists
2. **Check configuration**: Ensure `AZURE_ADMIN_ROLE_IDS` in `.env` matches the role IDs in your token
3. **Restart application**: Settings are loaded on startup
4. **Check logs**: Look for role assignment logs during authentication

### Where are `wids` stored?

- **OAuth2 flow**: `wids` are in the access_token and extracted to `user_info["groups"]` by `get_user_info()`
- **OIDC flow**: Role IDs may be in the `groups` claim of the id_token (if configured in Azure AD)

## Security Considerations

⚠️ **Important**: 

- Role template IDs are globally consistent across all Azure AD tenants
- The Global Administrator role ID is always `62e90394-69f5-4237-9190-012177145e10`
- Only grant admin privileges to trusted role IDs
- Regularly audit who has admin roles in your Azure AD tenant
- Consider using Azure AD groups instead for finer-grained control

## See Also

- [Azure AD Built-in Roles Documentation](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference)
- [AZURE_ROLES_TROUBLESHOOTING.md](./AZURE_ROLES_TROUBLESHOOTING.md)
- [OAUTH2_OIDC_SETUP_GUIDE.md](./OAUTH2_OIDC_SETUP_GUIDE.md)

