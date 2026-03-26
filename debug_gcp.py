import subprocess
import json
import sys


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return None, str(e)


def diag():
    print("--- Starting Gamuda Intel System Diagnostic ---")

    # 1. Check for Dockerfile
    import os
    if not os.path.exists("Dockerfile"):
        print("[ERROR] No Dockerfile found in current directory!")
    else:
        print("[OK] Dockerfile exists.")

    # 2. Check for requirements.txt
    if not os.path.exists("requirements.txt"):
        print("[WARNING] No requirements.txt found.")
    else:
        print("[OK] requirements.txt exists.")

    # 3. Get the last build error from GCP
    print("\n--- Fetching last build log from Google Cloud ---")
    build_list, err = run_command("gcloud builds list --limit=1 --format=json")

    if err and "not found" in err.lower():
        print("[ERROR] gcloud CLI not authenticated or project not set.")
        return

    try:
        build_data = json.loads(build_list)
        if not build_data:
            print("No builds found in this project.")
            return

        last_build = build_data[0]
        build_id = last_build['id']
        status = last_build['status']

        print(f"Build ID: {build_id}")
        print(f"Status: {status}")

        if status == "FAILURE":
            print("\n--- CAUSE OF FAILURE ---")
            # Get the log tail to find the specific error
            logs, log_err = run_command(f"gcloud builds log {build_id}")
            # Look for common error patterns
            lines = logs.split('\n')
            for line in lines[-20:]:  # Last 20 lines usually contain the error
                if "error" in line.lower() or "failed" in line.lower() or "Step #" in line:
                    print(line)
        else:
            print(
                f"The last build status was {status}. If deployment failed, it might be a service configuration issue, not a build issue.")

    except Exception as e:
        print(f"Error parsing build data: {e}")


if __name__ == "__main__":
    diag()