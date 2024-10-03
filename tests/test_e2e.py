import asyncio
import os
import shutil
import subprocess
import sys
import tempfile

import aiounittest
import requests
import yaml


class TestE2E(aiounittest.AsyncTestCase):
    async def test_e2e(self) -> None:
        # Create a temporary directory for the Synapse server
        temp_dir = tempfile.mkdtemp()

        try:
            # Generate Synapse config with server name 'my.domain.name'
            config_path = os.path.join(temp_dir, "homeserver.yaml")
            generate_config_cmd = [
                sys.executable,
                "-m",
                "synapse.app.homeserver",
                "--server-name",
                "my.domain.name",
                "--config-path",
                config_path,
                "--generate-config",
                "--report-stats=no",
            ]
            subprocess.check_call(generate_config_cmd)

            # Modify the config to include the module
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            config["modules"] = [{"module": "synapse_whoami.WhoAmI", "config": {}}]

            with open(config_path, "w") as f:
                yaml.dump(config, f)

            # Run the Synapse server
            run_server_cmd = [
                sys.executable,
                "-m",
                "synapse.app.homeserver",
                "--config-path",
                config_path,
            ]
            server_process = subprocess.Popen(
                run_server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
                text=True,
            )

            # Wait for the server to start by polling the root URL
            server_url = "http://localhost:8008"
            max_wait_time = 60  # Maximum wait time in seconds
            wait_interval = 0.25  # Interval between checks in seconds
            total_wait_time = 0

            while True:
                try:
                    response = requests.get(server_url)
                    if response.status_code == 200:
                        print("Synapse server started successfully")
                        break
                except requests.exceptions.ConnectionError:
                    print("Synapse server not yet up, retrying...")
                    # Server not yet up

                await asyncio.sleep(wait_interval)
                total_wait_time += wait_interval
                if total_wait_time >= max_wait_time:
                    self.fail(
                        f"Synapse server did not start within {max_wait_time} seconds"
                    )

            # Register a new user using the command-line utility
            register_user_cmd = [
                "register_new_matrix_user",
                "-c",
                config_path,
                "--user=test",
                "--password=123123123",
                "--admin",
            ]
            subprocess.check_call(register_user_cmd, cwd=temp_dir)

            # Login to obtain access token of the user
            login_url = "http://localhost:8008/_matrix/client/r0/login"
            login_data = {
                "type": "m.login.password",
                "user": "test",
                "password": "123123123",
            }
            response = requests.post(login_url, json=login_data)
            self.assertEqual(response.status_code, 200)
            access_token = response.json()["access_token"]

            # Call /_synapse/client/whoami with the access token
            whoami_url = "http://localhost:8008/_synapse/client/whoami"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(whoami_url, headers=headers)
            self.assertEqual(response.status_code, 200)
            expected_result = {"user_id": "@test:my.domain.name"}
            self.assertEqual(response.json(), expected_result)
        finally:
            # Terminate the server process
            server_process.terminate()
            server_process.wait()

            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
