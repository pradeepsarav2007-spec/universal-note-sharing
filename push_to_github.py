#!/usr/bin/env python3
"""
Universal Notes Sharing Platform - GitHub Pusher
Pushes the local Git repository to GitHub using a Personal Access Token (PAT).
"""

import sys
import os
import dulwich.porcelain

REPO_URL = "https://github.com/pradeepsarav2007-spec/universal-note-sharing.git"

def main():
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
    elif 'GITHUB_TOKEN' in os.environ:
        token = os.environ['GITHUB_TOKEN'].strip()
    
    if not token:
        print("="*60)
        print(" GitHub Push Authentication Required")
        print("="*60)
        print("GitHub requires a Personal Access Token (PAT) to push code.")
        print()
        print("How to get your GitHub token (takes 30 seconds):")
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Click 'Generate new token' -> 'Generate new token (classic)'")
        print("3. Check the 'repo' scope checkbox")
        print("4. Copy the generated token (starts with ghp_...)")
        print()
        print("Then run:")
        print("  python push_to_github.py <YOUR_GITHUB_TOKEN>")
        print("="*60)
        token = input("\nEnter your GitHub Personal Access Token (ghp_...): ").strip()
        if not token:
            print("No token provided. Aborting push.")
            sys.exit(1)

    # Format authenticated URL
    auth_url = f"https://{token}@github.com/pradeepsarav2007-spec/universal-note-sharing.git"
    
    print("\nConnecting to GitHub and pushing repository...")
    repo = dulwich.porcelain.open_repo('.')
    
    try:
        # Push to main branch
        dulwich.porcelain.push(repo, auth_url, 'refs/heads/main:refs/heads/main')
        print("\n" + "="*60)
        print(" [SUCCESS] Code successfully pushed to GitHub!")
        print(" Repository URL: https://github.com/pradeepsarav2007-spec/universal-note-sharing")
        print("="*60)
        print("\nNext steps to host on Render:")
        print("1. Go to https://dashboard.render.com/")
        print("2. Click 'New' -> 'Web Service'")
        print("3. Connect your repository 'pradeepsarav2007-spec/universal-note-sharing'")
        print("4. Render will auto-detect render.yaml and Procfile:")
        print("   • Build Command: pip install -r requirements.txt && python init_db.py")
        print("   • Start Command: gunicorn app:app")
        print("5. Click 'Create Web Service' and your site will be live!")
    except Exception as e:
        print(f"\n[ERROR] Push failed: {e}")
        print("Please check that your token has 'repo' write permissions and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()
