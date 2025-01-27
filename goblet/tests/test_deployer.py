from goblet import Goblet
from goblet.resources.http import HTTP
from goblet.test_utils import get_responses, dummy_function, DATA_DIR_MAIN, get_response


class TestDeployer:
    def test_deploy_http_function(self, monkeypatch, requests_mock):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-function-deploy")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        requests_mock.register_uri("PUT", "https://storage.googleapis.com/mock")

        app = Goblet(function_name="goblet_example")
        setattr(app, "entrypoint", "app")

        app.handlers["http"] = HTTP(dummy_function)

        app.deploy(skip_resources=True, skip_infra=True, force=True)

        responses = get_responses("deployer-function-deploy")
        assert len(responses) == 3

    def test_deploy_http_function_v2(self, monkeypatch, requests_mock):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-function-deploy-v2")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        requests_mock.register_uri("PUT", "https://storage.googleapis.com/mock")

        app = Goblet(function_name="goblet-test-http-v2", backend="cloudfunctionv2")
        setattr(app, "entrypoint", "app")

        app.handlers["http"].register_http(dummy_function, {})

        app.deploy(
            skip_resources=True,
            skip_infra=True,
            force=True,
            config={"runtime": "python38"},
        )

        responses = get_responses("deployer-function-deploy-v2")
        assert len(responses) == 3

    def test_deploy_cloudrun(self, monkeypatch, requests_mock):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-cloudrun-deploy")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        requests_mock.register_uri("PUT", "https://storage.googleapis.com/mock")

        app = Goblet(function_name="goblet", backend="cloudrun")
        setattr(app, "entrypoint", "app")

        app.handlers["http"] = HTTP(dummy_function)

        app.deploy(
            skip_resources=True,
            skip_infra=True,
            force=True,
            config={
                "cloudrun_revision": {
                    "serviceAccount": "test-746@goblet.iam.gserviceaccount.com"
                }
            },
        )

        responses = get_responses("deployer-cloudrun-deploy")
        assert len(responses) == 9

    def test_destroy_cloudrun(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-cloudrun-destroy")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        app = Goblet(function_name="goblet", backend="cloudrun")

        app.destroy()

        responses = get_responses("deployer-cloudrun-destroy")
        assert len(responses) == 1
        assert responses[0]["body"]["status"] == "Success"
        assert responses[0]["body"]["details"]["name"] == "goblet"

    def test_destroy_http_function(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-function-destroy")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        app = Goblet(function_name="goblet_test_app")

        app.destroy()

        responses = get_responses("deployer-function-destroy")
        assert len(responses) == 1
        assert responses[0]["body"]["metadata"]["type"] == "DELETE_FUNCTION"
        assert (
            responses[0]["body"]["metadata"]["target"]
            == "projects/goblet/locations/us-central1/functions/goblet_test_app"
        )

    def test_destroy_http_function_all(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-function-destroy-all")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        app = Goblet(function_name="goblet_example")

        app.destroy(all=True)

        responses = get_responses("deployer-function-destroy-all")
        assert len(responses) == 4

    def test_set_iam_bindings(self, monkeypatch, requests_mock):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-function-bindings")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        requests_mock.register_uri("PUT", "https://storage.googleapis.com/mock")

        app = Goblet(function_name="goblet_bindings")
        setattr(app, "entrypoint", "app")

        app.handlers["http"] = HTTP(dummy_function)
        bindings = [{"role": "roles/cloudfunctions.invoker", "members": ["allUsers"]}]
        app.deploy(
            skip_resources=True,
            skip_infra=True,
            config={"bindings": bindings},
            force=True,
        )

        responses = get_responses("deployer-function-bindings")
        assert len(responses) == 4
        assert responses[2]["body"]["bindings"] == bindings

    def test_cloudfunction_delta(self, monkeypatch, requests_mock):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-east1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-cloudfunction-delta")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        requests_mock.register_uri(
            "HEAD",
            "https://storage.googleapis.com/mock",
            headers={"x-goog-hash": "crc32c=+kjoHA==, md5=QcWxCkEOHzBSBgerQcjMEg=="},
        )

        app = Goblet(function_name="goblet_test_app")

        app_backend = app.backend_class(app)

        assert not app_backend.delta(f"{DATA_DIR_MAIN}/test_zip.txt.zip")
        assert app_backend.delta(f"{DATA_DIR_MAIN}/fail_test_zip.txt.zip")

    def test_cloudrun_custom_artifact(self, monkeypatch, requests_mock):
        monkeypatch.setenv("GOOGLE_PROJECT", "goblet")
        monkeypatch.setenv("GOOGLE_LOCATION", "us-central1")
        monkeypatch.setenv("GOBLET_TEST_NAME", "deployer-cloudrun-artifact")
        monkeypatch.setenv("GOBLET_HTTP_TEST", "REPLAY")

        requests_mock.register_uri("PUT", "https://storage.googleapis.com/mock")

        app = Goblet(function_name="goblet", backend="cloudrun")
        setattr(app, "entrypoint", "app")

        app.handlers["http"] = HTTP(dummy_function)

        app.deploy(
            skip_resources=True,
            skip_infra=True,
            force=True,
            config={
                "cloudrun_revision": {
                    "serviceAccount": "test@goblet.iam.gserviceaccount.com"
                },
                "cloudbuild": {
                    "artifact_registry": "us-central1-docker.pkg.dev/newgoblet/cloud-run-source-deploy/goblet",
                    "serviceAccount": "projects/goblet/serviceAccounts/test@goblet.iam.gserviceaccount.com",
                },
            },
        )

        response = get_response(
            "deployer-cloudrun-artifact", "post-v1-projects-goblet-builds_1.json"
        )
        assert (
            "newgoblet"
            in response["body"]["metadata"]["build"]["artifacts"]["images"][0]
        )
