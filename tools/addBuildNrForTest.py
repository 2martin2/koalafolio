# add or remove a buildnumber in setup.py to version for testuploades
# format: version='0.0.0.\d\d'
# add: build number will be addeed or incremented
# remove: build number will be removed
# usage: python tools/addBuildNrForTest.py [add|remove]
import sys
import re
from pathlib import Path
import requests
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETUP_FILE = PROJECT_ROOT / "setup.py"

LOCAL_VERSION_PATTERN = re.compile(r"version\s*=\s*['\"](\d+\.\d+\.\d+)(\.\d{2})?['\"]")
# REMOTE VERSION: \d+\.\d+\.\d+(\.\d+)? - matches version with optional build number
REMOTE_VERSION_PATTERN = re.compile(r"(\d+\.\d+\.\d+)(\.\d+)?")

TESTPYPI_URL = "https://test.pypi.org/pypi/koalafolio/json"

# get version from TestPyPi
def get_current_version():
    response = requests.get(TESTPYPI_URL)
    if response.status_code == 200:
        data = response.json()
        current_version_remote = data["info"]["version"]
        # parse remote version
        match_remote = REMOTE_VERSION_PATTERN.match(current_version_remote)
        if not match_remote:
            raise ValueError("Remote version pattern not found in TestPyPi")
        remote_version = match_remote.group(1)
        remote_build = match_remote.group(2) if match_remote.group(2) else None
        return remote_version, remote_build
    else:
        raise Exception("Failed to fetch version from TestPyPi")

    
def update_version():
    # get current version from TestPyPi
    try:
        remote_version, remote_build = get_current_version()
    except Exception as e:
        print(f"Error fetching current version from TestPyPi: {e}")
        sys.exit(1)

    # read current version from setup.py
    with open(SETUP_FILE, "r") as file:
        content = file.read()
    match_local = LOCAL_VERSION_PATTERN.search(content)
    if not match_local:
        raise ValueError("Version pattern not found in setup.py")
    local_version = match_local.group(1)
    
    # determine next build number based on test pypi version
    # if remote version is equal to current local version and has a dev build number, increment it
    # if remote version has no build number or remote version is older, set build number to 1
    if local_version == remote_version:
        if remote_build:
            # increment build number
            build_number = int(remote_build[1:]) + 1
        else:
            # set build number to 1
            build_number = 1
    else:
        # set build number to 1 if remote version is older or has no build number
        build_number = 1
    # update local version
    new_version = f"version='{local_version}.{build_number}'"
    # write updated version back to setup.py
    with open(SETUP_FILE, "w") as file:
        content = LOCAL_VERSION_PATTERN.sub(new_version, content)
        file.write(content)
    print(f"Updated version in {SETUP_FILE} to {local_version}.{build_number}")
    
    
def remove_version():
    # read current version from setup.py
    with open(SETUP_FILE, "r") as file:
        content = file.read()
    match_local = LOCAL_VERSION_PATTERN.search(content)
    if not match_local:
        raise ValueError("Version pattern not found in setup.py")
    local_version = match_local.group(1)
    local_build = match_local.group(2)

    # wait for 10 seconds to ensure the package is uploaded
    time.sleep(10)
    timeout = 50
    # check current remote version.buildnr and wait until it is updated
    while timeout > 0 :
        try:
            remote_version, remote_build = get_current_version()
        except Exception as e:
            print(f"Error fetching current version from TestPyPi: {e}")
            sys.exit(1)
        # wait for the remote version to be equal to local version
        if remote_build and remote_version == local_version and remote_build == local_build:
            timeout = 0
            print(f"Remote version {remote_version} with build number {remote_build} is ready for download.")
        else:
            print("Waiting for remote version to be updated...")
            time.sleep(5)
            timeout -= 5
    
    # remove build number from local version
    local_version = match_local.group(1)
    new_version = f"version='{local_version}'"
    
    # write updated version back to setup.py
    with open(SETUP_FILE, "w") as file:
        content = LOCAL_VERSION_PATTERN.sub(new_version, content)
        file.write(content)
    
    print(f"Removed build number from version in {SETUP_FILE}")
    

def main(action):
    if action == "add":
        # add or increment build number
        update_version()
    if action == "remove":
        # remove build number
        remove_version()

    
if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["add", "remove"]:
        print("Usage: python tools/addBuildNrForTest.py [add|remove]")
        sys.exit(1)

    action = sys.argv[1]
    main(action)

