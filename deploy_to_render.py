#!/usr/bin/env python3
"""
Universal Notes Sharing Platform - Render API Deployer
Creates and provisions the web service on Render via the official Render REST API.
"""

import sys
import os
import json
import urllib.request
import urllib.error

def deploy_to_render(api_key=None):
    api_key = api_key or os.environ.get('RENDER_API_KEY')
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1].strip()
        
    if not api_key:
        print("="*60)
        print(" Render API Key Required")
        print("="*60)
        print("To deploy automatically via API, Render requires an API key.")
        print()
        print("How to get your free Render API Key (15 seconds):")
        print("1. Go to: https://dashboard.render.com/u/settings#api-keys")
        print("2. Click 'Create API Key'")
        print("3. Enter a label (e.g. 'UniversalNotes') and copy the key (starts with rnd_...)")
        print()
        print("Usage:")
        print("  python deploy_to_render.py <YOUR_RENDER_API_KEY>")
        print("="*60)
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "UniversalNotesPlatform/1.0"
    }

    print("="*60)
    print(" Deploying Universal Notes Sharing Platform to Render...")
    print("="*60)

    # 1. Fetch Owner ID
    print("[1/3] Connecting to Render API & fetching account owner ID...")
    try:
        req_owners = urllib.request.Request("https://api.render.com/v1/owners", headers=headers)
        with urllib.request.urlopen(req_owners) as resp:
            owners_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Authentication failed: {e.code} {e.reason}")
        print("Please verify that your Render API key is correct.")
        return False
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return False

    if not owners_data:
        print("[ERROR] No Render accounts associated with this API key.")
        return False

    owner = owners_data[0]["owner"]
    owner_id = owner["id"]
    owner_name = owner.get("name") or owner.get("email") or "User"
    print(f"      Verified account: {owner_name} ({owner_id})")

    # 2. Check existing services to prevent duplicates
    print("[2/3] Checking existing services...")
    req_services = urllib.request.Request(f"https://api.render.com/v1/services?ownerId={owner_id}&limit=20", headers=headers)
    existing_url = None
    try:
        with urllib.request.urlopen(req_services) as resp:
            services_data = json.loads(resp.read().decode())
            for item in services_data:
                svc = item.get("service", {})
                if svc.get("name") == "universal-notes-sharing" or "universal-note-sharing" in svc.get("repo", ""):
                    existing_url = svc.get("serviceDetails", {}).get("url")
                    print(f"      Service already exists on your account: {existing_url}")
                    # Trigger manual deploy
                    svc_id = svc.get("id")
                    print(f"      Triggering fresh deployment for service {svc_id}...")
                    deploy_req = urllib.request.Request(
                        f"https://api.render.com/v1/services/{svc_id}/deploys",
                        data=b"{}",
                        headers=headers,
                        method="POST"
                    )
                    with urllib.request.urlopen(deploy_req) as dresp:
                        ddata = json.loads(dresp.read().decode())
                        print(f"      Deploy status: {ddata.get('deploy', {}).get('status', 'created')}")
                    break
    except Exception as e:
        print(f"      Notice during service check: {e}")

    # 3. Create service if not exists
    if not existing_url:
        print("[2/3] Creating new web service on Render...")
        payload = {
            "type": "web_service",
            "name": "universal-notes-sharing",
            "ownerId": owner_id,
            "repo": "https://github.com/pradeepsarav2007-spec/universal-note-sharing",
            "autoDeploy": "yes",
            "branch": "main",
            "serviceDetails": {
                "env": "python",
                "region": "oregon",
                "plan": "free",
                "buildCommand": "pip install -r requirements.txt && python init_db.py",
                "startCommand": "gunicorn app:app",
                "envVars": [
                    {
                        "key": "PYTHON_VERSION",
                        "value": "3.11.9"
                    }
                ]
            }
        }
        
        req_create = urllib.request.Request(
            "https://api.render.com/v1/services",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req_create) as resp:
                created_data = json.loads(resp.read().decode())
                service_obj = created_data.get("service", {})
                existing_url = service_obj.get("serviceDetails", {}).get("url")
                print("      Service created successfully!")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"[ERROR] Service creation failed ({e.code}): {error_body}")
            return False

    print("\n" + "="*60)
    print(" [SUCCESS] Render Web Service is actively deploying!")
    print(f" Live Public URL: {existing_url}")
    print("="*60)
    print("Render is now building and deploying your application.")
    print("The URL will be live in 1-2 minutes.")
    return existing_url

if __name__ == '__main__':
    deploy_to_render()
