# Branch Protection Guide

This guide explains how to configure branch protection rules on the `main` branch to ensure code quality and prevent merging PRs that fail CI/CD checks.

## Overview

Branch protection rules enforce:
- ✅ All status checks must pass before merge
- ✅ Code reviews required (optional)
- ✅ Up-to-date branch requirement
- ✅ Dismissal of stale reviews (optional)
- ✅ Restrict force pushes

## Step-by-Step Setup

### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository: `https://github.com/your-username/NordInvest`
2. Click **Settings** (top navigation bar)
3. Click **Branches** (left sidebar)
4. Click **Add rule** under "Branch protection rules"

### 2. Configure the Rule

#### Basic Rule Information

1. **Branch name pattern:** Enter `main`
   - This applies the rule to the main branch

#### Required Status Checks

1. ✅ Check: **Require status checks to pass before merging**

2. ✅ Check: **Require branches to be up to date before merging**
   - Ensures PR is based on latest main branch code
   - Prevents merge conflicts after approval

3. In the search box under "Status checks that are required to pass", select:
   - `PR Tests / test` - Main test workflow
   - Optional: `Code Coverage / coverage` - Coverage workflow (if using)

Example configuration:
```
Status checks required to pass:
  ☑ PR Tests / test
  ☑ Code Coverage / coverage (optional)
```

#### Code Review Settings (Recommended)

1. ✅ Check: **Require a pull request before merging**
   - Enforces code review process

2. ✅ Check: **Require approvals**
   - Set to: **1** (one reviewer minimum)

3. ✅ Check: **Dismiss stale pull request approvals when new commits are pushed**
   - Ensures reviews are re-evaluated if code changes

4. ✅ Check: **Require code owners review (optional)**
   - If you have CODEOWNERS file defined

#### Additional Restrictions

1. ✅ Check: **Include administrators**
   - Enforces rules even for admins
   - Recommended for team consistency

2. ✅ Check: **Restrict who can push to matching branches**
   - Optional: Limit push access to specific teams/users
   - Default: Allow all with write access

3. ✅ Check: **Require conversation resolution before merging**
   - Forces resolution of PR review comments

4. ✅ Check: **Require commits to be signed**
   - Optional: Enforce GPG/SSH signed commits
   - Good security practice

### 3. Save the Rule

Click **Create** button to save the branch protection rule.

## Resulting Behavior

### Before Merge is Allowed

✅ All CI/CD workflows must pass:
- Pre-commit checks (formatting, linting)
- All 219 unit tests
- Coverage threshold (50% minimum)

✅ Code review requirements:
- At least 1 approval required
- PR must be up-to-date with main

❌ Merge is blocked if:
- Any CI/CD check fails
- Required reviews not obtained
- Stale reviews after new commits
- Branch is behind main (if up-to-date requirement enabled)

### Merge Button States

| Status | Merge Button | Reason |
|--------|--------------|--------|
| All checks pass, 1 approval | ✅ Green - Enabled | Ready to merge |
| Checks running | 🟡 Yellow - Disabled | Waiting for checks |
| Checks failed | ❌ Red - Disabled | Must fix failures |
| No approvals | ⚪ Gray - Disabled | Need review approval |
| Branch outdated | ⚪ Gray - Disabled | Need to update branch |

## Verifying the Configuration

After creating the rule:

1. Go to **Settings** → **Branches** → **main**
2. Verify the following are checked:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1)
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Include administrators

3. Under "Status checks that are required to pass":
   - ✅ PR Tests / test
   - ✅ Code Coverage / coverage (optional)

## Testing the Rules

### Create a Test PR

1. Create a new branch: `git checkout -b test/branch-protection`
2. Make a small change to a file
3. Commit and push: `git push origin test/branch-protection`
4. Create a Pull Request to `main`

### Verify CI/CD Runs

You should see:
- 🟡 Checks running message
- Workflow progress appears
- Cannot merge until checks complete

### Verify Code Review Requirement

- Try to merge without approval → ❌ Not allowed
- Get approval from another user → Still cannot merge if checks fail
- All checks pass + approval → ✅ Merge allowed

## Troubleshooting

### Merge Button Still Disabled After All Checks Pass

**Cause:** Status checks may need to be re-selected

**Fix:**
1. Go to **Settings** → **Branches** → **main**
2. Scroll to "Status checks that are required to pass"
3. Make sure `PR Tests / test` is selected
4. Save changes

### Can't Find the Workflow in Status Checks List

**Cause:** Workflow hasn't run yet on this branch

**Fix:**
1. The workflow appears in the list after the first run
2. Create a test PR and let it run
3. Then configure the branch protection rule

### Admins Can Still Bypass Rules

**Cause:** "Include administrators" is not checked

**Fix:**
1. Go to **Settings** → **Branches** → **main**
2. ✅ Check: **Include administrators**
3. Save changes

## Best Practices

### For Development Teams

1. **Require Reviews** - Catch bugs early with peer review
2. **Enforce Status Checks** - Prevent broken code in main
3. **Require Up-to-Date Branch** - Avoid merge conflicts
4. **Dismiss Stale Reviews** - Keep reviews current with code
5. **Include Admins** - Consistency across the team

### For Solo Development

Minimum recommended:
1. ✅ Require status checks to pass
2. ✅ Require branches to be up to date
3. Optional: Dismiss stale reviews

No need for code reviews, but keep CI/CD checks enabled.

### For Open Source Projects

Strong protection recommended:
1. ✅ All of the above
2. ✅ Require code reviews (2+ approvals)
3. ✅ Require conversation resolution
4. ✅ Require signed commits
5. ✅ Include administrators

## Status Check Names Reference

When configuring branch protection rules, use these exact names:

```
PR Tests / test          → Main workflow with all checks
Code Coverage / coverage → Optional coverage workflow
```

## Bypassing Rules (Emergency Only)

If you absolutely must bypass branch protection (do this rarely):

### Admin Override (Not Recommended)

1. Uncheck "Include administrators" (temporarily)
2. Merge the PR
3. Re-enable the rule immediately
4. Document why you needed to bypass

**Best Practice:** Never bypass for production code. Fix the failing check instead.

## Monitoring and Adjusting

### Monitor Rule Effectiveness

- Track how many PRs are blocked by checks
- Monitor review time (how long before approval?)
- Check if developers are pushing directly to main (they shouldn't be able to)

### Adjusting Rules Over Time

As your project matures:

| Phase | Review Requirement | Coverage Threshold |
|-------|-------------------|-------------------|
| Phase 7 (now) | 1 approval | 50% |
| Phase 8 | 1 approval | 60% |
| Phase 9 | 2 approvals | 70% |

To adjust:
1. Go to **Settings** → **Branches** → **main**
2. Edit the rule
3. Change requirements
4. Click **Save changes**

## References

- [GitHub Docs - Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [GitHub Docs - Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-pull-requests/about-status-checks)
- [GitHub Docs - Code Reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests)
