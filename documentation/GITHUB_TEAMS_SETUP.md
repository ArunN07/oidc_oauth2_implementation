# GitHub Teams - Complete Setup Guide

## Overview

GitHub allows you to create **Teams** within your organization. Teams help organize members and control access to repositories. In your application, team memberships automatically become roles.

---

## Step 1: Create GitHub Organization (If Not Already Done)

### 1.1 Navigate to Organizations

1. **Go to**: https://github.com/settings/organizations
2. **Click**: "New organization"
3. **Or use existing**: https://github.com/Karnata-Bala

**For this guide, we'll use your existing organization: `Karnata-Bala`**

---

## Step 2: Create Teams in GitHub

### 2.1 Navigate to Teams

1. **Go to**: https://github.com/orgs/Karnata-Bala/teams
2. **Click**: "New team" (green button, top right)

### 2.2 Create Your First Team - "Developers"

1. **Fill in the form**:

   | Field | Value |
   |-------|-------|
   | **Team name** | `developers` |
   | **Description** | `Development team for code development and deployment` |
   | **Team visibility** | ☑ Visible (Recommended - team visible to all org members) |
   | **Parent team** | None (or select if nesting teams) |

2. **Click**: "Create team"

### 2.3 Create More Teams

Repeat the process for additional teams:

#### Moderators Team
```
Team name: moderators
Description: Content moderation and community management team
Team visibility: Visible
Parent team: None
```

#### Managers Team
```
Team name: managers
Description: Team leads and project managers
Team visibility: Visible
Parent team: None
```

#### QA Team
```
Team name: qa-team
Description: Quality assurance and testing team
Team visibility: Visible
Parent team: None
```

#### Backend Team
```
Team name: backend-team
Description: Backend development team
Team visibility: Visible
Parent team: developers (optional - makes this a child team)
```

#### Frontend Team
```
Team name: frontend-team
Description: Frontend development team
Team visibility: Visible
Parent team: developers (optional - makes this a child team)
```

**Important Notes:**
- The **team slug** (lowercase, hyphenated) is what appears as a role in your application
- Team name "Dev Team" → slug "dev-team" → role "dev-team"
- Team name "developers" → slug "developers" → role "developers"
- **Visible teams** can be seen by all organization members
- **Secret teams** are only visible to team members

---

## Step 3: Add Members to Teams

### 3.1 Navigate to Your Team

1. **Go to**: https://github.com/orgs/Karnata-Bala/teams
2. **Click** on the team (e.g., "developers")
3. **You'll see**: Team overview page

### 3.2 Add a Member to the Team

#### Method 1: From Team Page

1. **On the team page**, click: "Add a member"
2. **Search for user**: Type username (e.g., `ArunN07` or `ArunN0007`)
3. **Select the user** from dropdown
4. **Click**: "Add [username] to developers"

#### Method 2: From Organization People Page

1. **Go to**: https://github.com/orgs/Karnata-Bala/people
2. **Find the user** in the members list
3. **Click the dropdown** next to their name
4. **Select**: "Change role" or "Manage"
5. **Select teams**: Check the teams you want to add them to
6. **Click**: "Save"

### 3.3 Add Member to Multiple Teams

To add the same user to multiple teams:

1. **Go to team 1**: https://github.com/orgs/Karnata-Bala/teams/developers
   - Add member: `ArunN07`

2. **Go to team 2**: https://github.com/orgs/Karnata-Bala/teams/moderators
   - Add member: `ArunN07`

3. **Go to team 3**: https://github.com/orgs/Karnata-Bala/teams/managers
   - Add member: `ArunN07`

**Result**: User `ArunN07` is now in 3 teams and will get 3 corresponding roles!

---

## Step 4: Verify Team Membership

### 4.1 Check Team Members

1. **Go to team page**: https://github.com/orgs/Karnata-Bala/teams/developers
2. **Click**: "Members" tab
3. **You should see**: List of all team members

### 4.2 Check User's Teams

1. **Go to**: https://github.com/orgs/Karnata-Bala/people
2. **Find user**: `ArunN07`
3. **Check "Teams" column**: Should show "2 teams" or "3 teams"
4. **Click on the number**: See which teams the user belongs to

### 4.3 Visual Verification

You should see something like:

```
Team: developers
Members (2)
├── ArunN07 (Member)
└── ArunN0007 (Member)

Team: moderators  
Members (1)
└── ArunN07 (Member)
```

---

## Step 5: Configure Your Application

### 5.1 Verify OAuth Scopes

Your `.env` file **must** include the `read:org` scope:

```bash
# In your .env file
GITHUB_SCOPES=read:user user:email read:org  # ← Must include read:org!
```

**Without `read:org` scope, teams cannot be accessed!**

### 5.2 Update Configuration (Already Done!)

Your application is already configured:

```bash
# .env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_SCOPES=read:user user:email read:org
GITHUB_ADMIN_ORGS=Karnata-Bala  # ← Organization for admin detection
```

**No additional configuration needed for teams!** They're automatically detected.

---

## Step 6: Authorize OAuth App for Organization

**Important**: GitHub requires explicit authorization for organizations.

### 6.1 Revoke Current Authorization

1. **Go to**: https://github.com/settings/applications
2. **Find**: `oath2_oidc_implementation`
3. **Click**: "Revoke" or "Revoke access"

### 6.2 Re-authorize with Organization Access

1. **Login via your app**:
   ```
   http://localhost:8001/api/v1/auth/github/login
   ```

2. **During authorization**, you'll see:
   ```
   Authorize oath2_oidc_implementation?
   
   This application would like to:
   ☑ Read your user profile
   ☑ Read your email addresses
   ☑ Read your organizations and teams
   
   Organization access:
   [x] Grant access to Karnata-Bala  ← CHECK THIS BOX!
   ```

3. **Important**: **Check the box** next to "Karnata-Bala"
4. **Click**: "Authorize"

**If you skip this step, the app won't see your organization or teams!**

---

## Step 7: Test the Integration

### 7.1 Clear Current Session

1. **Clear browser cookies**
2. Or use **Incognito/Private browsing mode**

### 7.2 Login via Your Application

```bash
# Login via GitHub
http://localhost:8001/api/v1/auth/github/login
```

### 7.3 Expected Response

```json
{
  "access_token": "gho_...",
  "token_type": "bearer",
  "user": {
    "id": "12345678",
    "provider": "github",
    "username": "ArunN07",
    "email": "arun@example.com",
    "name": "Arun N",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
    "roles": [
      "user",          // ← Always present (base role)
      "admin",         // ← From GITHUB_ADMIN_ORGS (Karnata-Bala)
      "developers",    // ← From team membership! ✅
      "moderators",    // ← From team membership! ✅
      "managers"       // ← From team membership! ✅
    ]
  },
  "id_token": null,
  "refresh_token": null,
  "expires_in": 28800
}
```

---

## Step 8: Verify with GitHub API

### 8.1 Test Organization Membership

```bash
# Get your access token from login response
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.github.com/user/orgs

# Expected Response:
[
  {
    "login": "Karnata-Bala",
    "id": 123456,
    "url": "https://api.github.com/orgs/Karnata-Bala"
  }
]
```

### 8.2 Test Team Membership

```bash
# Get your teams
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.github.com/user/teams

# Expected Response:
[
  {
    "name": "Developers",
    "slug": "developers",
    "organization": {
      "login": "Karnata-Bala"
    }
  },
  {
    "name": "Moderators",
    "slug": "moderators",
    "organization": {
      "login": "Karnata-Bala"
    }
  }
]
```

---

## Complete Example: Setting Up Multiple Users with Different Teams

### Scenario

You have a team with different access levels:

| User | GitHub Username | Teams |
|------|----------------|-------|
| Arun Nagaraju | ArunN07 | developers, moderators, managers |
| John Doe | johndoe | developers, backend-team |
| Jane Smith | janesmith | developers, frontend-team |
| Bob Johnson | bobjohnson | qa-team |

### Setup Process

#### 1. Create Teams (One-time)

In GitHub: https://github.com/orgs/Karnata-Bala/teams

- Create: `developers`
- Create: `moderators`
- Create: `managers`
- Create: `backend-team`
- Create: `frontend-team`
- Create: `qa-team`

#### 2. Add Users to Teams

**Arun Nagaraju (ArunN07):**
- Add to: developers team
- Add to: moderators team
- Add to: managers team

**John Doe (johndoe):**
- Add to: developers team
- Add to: backend-team

**Jane Smith (janesmith):**
- Add to: developers team
- Add to: frontend-team

**Bob Johnson (bobjohnson):**
- Add to: qa-team

#### 3. Test Each User

Each user logs in and gets their team-based roles:

**Arun's Response:**
```json
{
  "user": {
    "username": "ArunN07",
    "roles": ["user", "admin", "developers", "moderators", "managers"]
  }
}
```

**John's Response:**
```json
{
  "user": {
    "username": "johndoe",
    "roles": ["user", "developers", "backend-team"]
  }
}
```

**Jane's Response:**
```json
{
  "user": {
    "username": "janesmith",
    "roles": ["user", "developers", "frontend-team"]
  }
}
```

**Bob's Response:**
```json
{
  "user": {
    "username": "bobjohnson",
    "roles": ["user", "qa-team"]
  }
}
```

---

## Advanced: Nested Teams

You can create hierarchical team structures:

### Create Parent-Child Teams

1. **Create parent team**: "developers"
2. **Create child team**: "backend-team"
   - Set "Parent team" to "developers"
3. **Create child team**: "frontend-team"
   - Set "Parent team" to "developers"

### Benefits

- Members of child teams automatically have access through parent team
- Easier permission management
- Logical organization structure

### Example Structure

```
Karnata-Bala (Organization)
├── developers (Parent Team)
│   ├── backend-team (Child)
│   └── frontend-team (Child)
├── moderators
└── managers
```

**Note**: In your application, each team still appears as a separate role.

---

## Troubleshooting

### Problem: Teams Not Appearing in Response

**Solution 1: Check OAuth Scope**
```bash
# In .env
GITHUB_SCOPES=read:user user:email read:org  # ← Must include read:org!
```

**Solution 2: Re-authorize OAuth App**
- Revoke: https://github.com/settings/applications
- Login again and grant organization access

**Solution 3: Verify Team Membership**
- Go to: https://github.com/orgs/Karnata-Bala/teams/developers
- Verify user is listed as member

**Solution 4: Check Organization Authorization**
- Go to: https://github.com/settings/applications
- Find your app
- Under "Organization access", click "Grant" next to Karnata-Bala

### Problem: Empty Array from `/user/teams`

**Cause**: OAuth app not authorized for organization

**Solution**:
1. Go to: https://github.com/organizations/Karnata-Bala/settings/oauth_application_policy
2. Find your OAuth app
3. Click "Grant access" or "Approve"

### Problem: User Assigned to Team but Not Getting Role

**Cause 1: Team is Secret**
- Secret teams may not be visible via API
- Change team visibility to "Visible"

**Cause 2: OAuth Scope Missing**
- Verify `GITHUB_SCOPES` includes `read:org`
- Users must re-authorize to get new scopes

**Cause 3: Cache Issue**
- Clear browser cookies
- Login in incognito mode

### Problem: Getting All Teams, Not Just User's Teams

**This was fixed!** The code now uses `/user/teams` endpoint which returns only teams the user is a member of.

If you still see all teams:
- Check the code in `github_service.py`
- Should use `/user/teams` not `/orgs/{org}/teams`

---

## Application Code - Already Implemented! ✅

Your application automatically detects GitHub teams:

### File: `github_service.py`

```python
async def get_user_teams(self, access_token: str, organizations: list[str]) -> list[str]:
    """Get only teams the user is a member of."""
    teams_url = "https://api.github.com/user/teams"
    teams_response = await client.get(teams_url, headers=headers)
    
    # Extract team slugs (only user's teams)
    for team in user_teams:
        teams.append(team.get("slug"))
    
    return teams
```

### File: `role_service.py`

```python
def _get_github_roles(self, user_data: dict[str, Any]) -> list[str]:
    roles = []
    teams = user_data.get("teams", [])
    
    # Automatically add ALL teams as roles
    if teams and isinstance(teams, list):
        for team in teams:
            if team and isinstance(team, str):
                roles.append(team)  # ← Direct mapping!
    
    return roles
```

**Your code already supports teams!** Just create teams in GitHub and add members.

---

## Summary Checklist

- [ ] **Step 1**: Verify GitHub organization exists (Karnata-Bala)
- [ ] **Step 2**: Create teams (developers, moderators, managers, etc.)
- [ ] **Step 3**: Add members to teams
- [ ] **Step 4**: Verify team membership in GitHub
- [ ] **Step 5**: Verify `GITHUB_SCOPES` includes `read:org`
- [ ] **Step 6**: Authorize OAuth app for organization
- [ ] **Step 7**: Clear browser cache
- [ ] **Step 8**: Login via your application
- [ ] **Step 9**: Verify teams appear as roles in response

---

## Quick Reference: GitHub Navigation

```
GitHub.com
├── Your Organizations
│   └── Karnata-Bala
│       ├── Teams ← CREATE TEAMS HERE
│       │   ├── developers
│       │   ├── moderators
│       │   └── managers
│       └── People ← VIEW MEMBERS & TEAMS
│           └── ArunN07 (2 teams)
├── Settings
│   └── Applications ← AUTHORIZE OAUTH APP
│       └── oath2_oidc_implementation
│           └── Organization access
│               └── [x] Karnata-Bala ← GRANT ACCESS
```

---

## Best Practices

### 1. Team Naming Convention

✅ **Good:**
- `developers` (lowercase, simple)
- `backend-team` (lowercase, hyphen-separated)
- `content-moderators` (descriptive)

❌ **Bad:**
- `Dev Team` (spaces become hyphens in slug)
- `Team_1` (underscores less common)
- `grp-a` (not descriptive)

### 2. Team Descriptions

Be specific and clear:
```
✅ Good: "Backend development team for API and database work"
❌ Bad: "Backend team"
```

### 3. Team Visibility

- **Visible**: Recommended for most teams (all org members can see)
- **Secret**: Use only for sensitive teams (only members can see)

**Note**: Secret teams may have API limitations.

### 4. Team Structure

Organize logically:
```
Good Structure:
├── engineering (parent)
│   ├── backend-team
│   ├── frontend-team
│   └── devops-team
├── product-team
└── design-team
```

---

## Comparison: GitHub Teams vs Azure AD Roles

| Feature | GitHub Teams | Azure AD App Roles |
|---------|--------------|-------------------|
| **Creation** | Organization → Teams | App registrations → App roles |
| **Assignment** | Add to team | Assign user to role |
| **In Token** | ❌ No (need API call) | ✅ Yes (`roles` claim) |
| **Auto-sync** | ✅ Yes (via API) | ✅ Yes (in token) |
| **Permission Model** | Repository-based | Application-based |
| **Best For** | Dev teams, repos | Enterprise apps |
| **Setup Difficulty** | Easy | Medium |

---

## Next Steps

1. ✅ Create your teams in GitHub organization
2. ✅ Add yourself to test teams
3. ✅ Authorize OAuth app for organization
4. ✅ Login and verify teams appear as roles
5. ✅ Add other users as needed
6. ✅ Implement role-based access control in your API

**Your application is ready to use GitHub teams immediately!** No code changes needed - just create teams in GitHub and they'll work automatically. 🎉

---

## Related Documentation

- [CUSTOM_ROLES_IN_PORTALS.md](./CUSTOM_ROLES_IN_PORTALS.md) - Compare Azure vs GitHub roles
- [GITHUB_CUSTOM_ROLES_GUIDE.md](./GITHUB_CUSTOM_ROLES_GUIDE.md) - Why GitHub uses teams
- [GITHUB_TEAMS_BUG_FIX.md](./GITHUB_TEAMS_BUG_FIX.md) - Bug fix for team detection
- [GITHUB_ORG_SETUP_KARNATA_BALA.md](./GITHUB_ORG_SETUP_KARNATA_BALA.md) - Organization setup
- [AZURE_CUSTOM_ROLES_SETUP.md](./AZURE_CUSTOM_ROLES_SETUP.md) - Azure AD roles setup

---

## Screenshots Reference

### Creating a Team

```
https://github.com/orgs/Karnata-Bala/teams
    ↓
[New team] button (top right)
    ↓
┌─────────────────────────────────────┐
│ Create new team                      │
├─────────────────────────────────────┤
│ Team name: [developers           ]  │
│ Description: [Development team   ]  │
│                                      │
│ Team visibility:                     │
│ ○ Visible                            │
│   Anyone in the organization can     │
│   see this team                      │
│ ○ Secret                             │
│   Only visible to members            │
│                                      │
│ Parent team: [None ▼]                │
│                                      │
│            [Create team]             │
└─────────────────────────────────────┘
```

### Adding a Member

```
Team: developers
    ↓
[Add a member] button
    ↓
┌─────────────────────────────────────┐
│ Add members to developers            │
├─────────────────────────────────────┤
│ Search: [ArunN07_______________]     │
│                                      │
│ Suggestions:                         │
│ ○ ArunN07                            │
│   Arun Nagaraju                      │
│                                      │
│         [Add ArunN07 to team]        │
└─────────────────────────────────────┘
```

---

**You're all set!** Follow this guide to create teams in GitHub and assign users. Your application will automatically detect team memberships and add them as roles. 🚀

