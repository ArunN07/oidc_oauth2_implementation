# Azure AD Custom Roles - Complete Setup Guide

## Overview

Azure AD allows you to create **custom App Roles** in your application registration. These roles can then be assigned to users and will appear in the authentication tokens automatically.

---

## Step 1: Create Custom App Roles in Azure Portal

### 1.1 Navigate to App Roles

1. **Go to**: https://portal.azure.com
2. **Navigate to**: Azure Active Directory → App registrations
3. **Find your app**: `oath2_oidc_implementation` (or your app name)
4. **Click**: App registrations → Your app
5. **In the left sidebar, click**: **App roles**

### 1.2 Create Your First Custom Role - "Developer"

1. **Click**: "Create app role"
2. **Fill in the form**:

   | Field | Value |
   |-------|-------|
   | **Display name** | `Developer` |
   | **Allowed member types** | ☑ Users/Groups |
   | **Value** | `developer` |
   | **Description** | `Developer role for application access and code management` |
   | **Do you want to enable this app role?** | ☑ Checked |

3. **Click**: "Apply"

### 1.3 Create More Custom Roles

Repeat the process for additional roles:

#### Moderator Role
```
Display name: Moderator
Allowed member types: Users/Groups
Value: moderator
Description: Moderator role for content management and moderation tasks
✓ Enable this app role
```

#### Manager Role
```
Display name: Manager
Allowed member types: Users/Groups
Value: manager
Description: Manager role for team oversight and management functions
```

#### QA Engineer Role
```
Display name: QA Engineer
Allowed member types: Users/Groups
Value: qa-engineer
Description: Quality assurance and testing role
```

#### Architect Role
```
Display name: Architect
Allowed member types: Users/Groups
Value: architect
Description: Technical architecture and design role
```

**Important Notes:**
- The **Value** field is what appears in the token (use lowercase, hyphens for spaces)
- The **Display name** is what users see in the Azure Portal
- You can create as many roles as you need

---

## Step 2: Assign Roles to Users

### 2.1 Navigate to Enterprise Applications

1. **Go to**: Azure Active Directory → Enterprise applications
2. **Search for**: `oath2_oidc_implementation`
3. **Click** on your application
4. **In the left sidebar, click**: **Users and groups**

### 2.2 Assign a User to a Role

1. **Click**: "Add user/group"
2. **Under Users**:
   - Click "None Selected"
   - Search for user: `Arun Nagaraju` or `arun.srihari@hotmail.com`
   - Select the user
   - Click "Select"

3. **Under Select a role**:
   - Click "None Selected"
   - Choose role: **Developer**
   - Click "Select"

4. **Click**: "Assign"

### 2.3 Assign Multiple Roles to Same User

To assign another role to the same user:

1. **Click**: "Add user/group" again
2. **Select the same user**: `Arun Nagaraju`
3. **Select different role**: **Moderator**
4. **Click**: "Assign"

**Result**: User will have both `developer` and `moderator` roles in the token!

---

## Step 3: Verify Role Assignments

### 3.1 Check User's Assigned Roles

1. **Go to**: Enterprise applications → Your app → Users and groups
2. **Find your user** in the list
3. **Check the "Role" column** - should show assigned role(s)

### 3.2 Visual Verification

You should see something like:

```
Name                Email                           Role
────────────────────────────────────────────────────────────
Arun Nagaraju      arun.srihari@hotmail.com        Developer
Arun Nagaraju      arun.srihari@hotmail.com        Moderator
```

*Note: Each role assignment appears as a separate entry*

---

## Step 4: Test the Integration

### 4.1 Clear Current Session

1. **Clear browser cookies**
2. Or use **Incognito/Private browsing mode**

### 4.2 Login via Your Application

```bash
# OIDC Flow (Recommended - roles in ID token)
http://localhost:8001/api/v1/auth/azure/login

# OAuth2 Flow (roles in access token)
http://localhost:8001/api/v1/auth/oauth2/azure/login
```

### 4.3 Expected Response

```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "Bearer",
  "user": {
    "id": "501b4bea-54ee-42c6-b8b5-df24904dd4fc",
    "provider": "azure",
    "username": "arun.srihari@hotmail.com",
    "email": "arun.srihari@hotmail.com",
    "name": "Arun N",
    "avatar_url": null,
    "roles": [
      "user",        // ← Always present (base role)
      "admin",       // ← From Azure AD admin role or config
      "developer",   // ← From custom App Role assignment! ✅
      "moderator"    // ← From custom App Role assignment! ✅
    ]
  },
  "id_token": "eyJ0eXAi...",
  "refresh_token": "..."
}
```

---

## Step 5: Verify Roles in Token

### 5.1 Decode the ID Token

1. **Copy the `id_token`** from the response
2. **Go to**: https://jwt.io or https://jwt.ms
3. **Paste the token** in the decoder
4. **Look for the `roles` claim**:

```json
{
  "aud": "aa31c194-f925-420a-87e3-81b8d6c82757",
  "iss": "https://login.microsoftonline.com/.../v2.0",
  "email": "arun.srihari@hotmail.com",
  "name": "Arun N",
  "roles": [
    "developer",   // ← Custom App Role
    "moderator"    // ← Custom App Role
  ],
  "groups": [
    "8797ed04-28e6-4e92-850a-2c455a4340e9"
  ]
}
```

### 5.2 Verify Access Token

Similarly, decode the `access_token` and check for roles.

---

## Complete Example: Setting Up Multiple Users with Different Roles

### Scenario

You have a team with different access levels:

| User | Email | Roles |
|------|-------|-------|
| Arun Nagaraju | arun.srihari@hotmail.com | Developer, Moderator |
| John Doe | john.doe@company.com | Developer |
| Jane Smith | jane.smith@company.com | Manager, Moderator |
| Bob Johnson | bob.johnson@company.com | QA Engineer |

### Setup Process

#### 1. Create App Roles (One-time)

In Azure Portal → App roles:
- Create: `developer`
- Create: `moderator`
- Create: `manager`
- Create: `qa-engineer`

#### 2. Assign Users to Roles

In Enterprise applications → Users and groups:

**Arun Nagaraju:**
- Add user/group → Select Arun → Select role: Developer → Assign
- Add user/group → Select Arun → Select role: Moderator → Assign

**John Doe:**
- Add user/group → Select John → Select role: Developer → Assign

**Jane Smith:**
- Add user/group → Select Jane → Select role: Manager → Assign
- Add user/group → Select Jane → Select role: Moderator → Assign

**Bob Johnson:**
- Add user/group → Select Bob → Select role: QA Engineer → Assign

#### 3. Test Each User

Each user logs in and gets their assigned roles:

**Arun's Response:**
```json
{
  "user": {
    "email": "arun.srihari@hotmail.com",
    "roles": ["user", "admin", "developer", "moderator"]
  }
}
```

**John's Response:**
```json
{
  "user": {
    "email": "john.doe@company.com",
    "roles": ["user", "developer"]
  }
}
```

---

## Advanced: Assign Roles to Groups

Instead of assigning roles to individual users, you can assign to Azure AD groups.

### 1. Create Azure AD Groups

1. **Go to**: Azure Active Directory → Groups
2. **Click**: "New group"
3. **Fill in**:
   ```
   Group type: Security
   Group name: Developers Team
   Group description: All developers
   ```
4. **Add members** to the group

### 2. Assign Group to App Role

1. **Go to**: Enterprise applications → Your app → Users and groups
2. **Click**: "Add user/group"
3. **Under Groups**:
   - Click "None Selected"
   - Search for: `Developers Team`
   - Select the group
   - Click "Select"
4. **Select role**: Developer
5. **Click**: "Assign"

**Result**: All members of "Developers Team" automatically get the `developer` role!

---

## Troubleshooting

### Problem: Roles Not Appearing in Token

**Solution 1: Clear Cache and Re-login**
- Clear browser cookies
- Use incognito mode
- Login again

**Solution 2: Verify Role Assignment**
- Go to: Enterprise applications → Users and groups
- Verify user is listed with role assigned

**Solution 3: Check Token Configuration**
- Go to: App registrations → Token configuration
- Verify "Emit roles claim" is not disabled

### Problem: Can't Assign Roles to Users

**Solution: Insufficient Permissions**
- You need to be an **Owner** or **Application Administrator**
- Contact your Azure AD administrator

### Problem: Roles Claim Not in Token

**Solution: Optional Claims Configuration**

1. **Go to**: App registrations → Token configuration
2. **Click**: "Add optional claim"
3. **Token type**: ID, Access
4. **Select**: `roles`
5. **Click**: "Add"

---

## Application Code - Already Implemented! ✅

Your application automatically detects Azure AD App Roles:

### File: `role_service.py`

```python
def _get_azure_roles(self, user_data: dict[str, Any]) -> list[str]:
    roles = []
    
    # ... admin detection logic ...
    
    # Check Azure AD App Roles (from token)
    token_roles = user_data.get("roles", []) or user_data.get("claims", {}).get("roles", [])
    
    if isinstance(token_roles, list):
        for token_role in token_roles:
            if token_role and isinstance(token_role, str):
                role_lower = token_role.lower()
                if role_lower == "admin":
                    roles.append(Role.ADMIN.value)
                else:
                    # Automatically add any custom role!
                    roles.append(role_lower)
    
    return roles
```

**Your code already supports custom roles!** Just create them in Azure Portal and assign users.

---

## Summary Checklist

- [ ] **Step 1**: Create custom App Roles in Azure Portal (App roles section)
- [ ] **Step 2**: Assign users to roles (Enterprise applications → Users and groups)
- [ ] **Step 3**: Clear browser cache
- [ ] **Step 4**: Login via your application
- [ ] **Step 5**: Verify roles appear in token (jwt.io)
- [ ] **Step 6**: Check application response includes custom roles

---

## Quick Reference: Azure Portal Navigation

```
Azure Portal (portal.azure.com)
├── Azure Active Directory
│   ├── App registrations
│   │   └── oath2_oidc_implementation
│   │       ├── App roles ← CREATE ROLES HERE
│   │       └── Token configuration
│   ├── Enterprise applications
│   │   └── oath2_oidc_implementation
│   │       └── Users and groups ← ASSIGN ROLES HERE
│   └── Groups
│       └── [Your Groups] ← OPTIONAL: Assign groups to roles
```

---

## Best Practices

### 1. Role Naming Convention

✅ **Good:**
- `developer` (lowercase, simple)
- `qa-engineer` (lowercase, hyphen-separated)
- `content-moderator` (descriptive)

❌ **Bad:**
- `Developer` (uppercase - inconsistent)
- `dev_role` (underscores less common)
- `role1` (not descriptive)

### 2. Role Descriptions

Be specific and clear:
```
✅ Good: "Developer role for code development and deployment"
❌ Bad: "Developer"
```

### 3. Security

- **Principle of Least Privilege**: Only assign roles users actually need
- **Regular Audits**: Review role assignments quarterly
- **Group-Based**: Use Azure AD groups for easier management

---

## Next Steps

1. ✅ Create your custom roles in Azure Portal
2. ✅ Assign yourself to test roles
3. ✅ Login and verify roles appear
4. ✅ Assign other users as needed
5. ✅ Implement role-based access control in your API endpoints

**Your application is ready to use custom roles immediately!** No code changes needed - just create roles in Azure Portal and they'll work automatically. 🎉

---

