import contextlib
import importlib.resources
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Literal
from typing import Optional
from typing import cast

import regex
import requests
import yaml
from jinja2 import Template
from loguru import logger

from dsp_tools.error.exceptions import InputError
from dsp_tools.utils.request_utils import RequestParameters
from dsp_tools.utils.request_utils import log_request
from dsp_tools.utils.request_utils import log_response

MAX_FILE_SIZE = 100_000


@dataclass
class StackConfiguration:
    """
    Groups together configuration information for the StackHandler.

    Args:
        max_file_size: max. multimedia file size allowed for ingest, in MB (max: 100'000)
        enforce_docker_system_prune: if True, prune Docker without asking the user
        suppress_docker_system_prune: if True, don't prune Docker (and don't ask)
        latest_dev_version: if True, start DSP-API from repo's main branch, instead of the latest deployed version
    """

    max_file_size: Optional[int] = None
    enforce_docker_system_prune: bool = False
    suppress_docker_system_prune: bool = False
    latest_dev_version: bool = False
    upload_test_data: bool = False
    custom_host: Optional[str] = None
    container_engine: Literal["docker", "podman"] = "docker"
    environment: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate the input parameters passed by the user.

        Raises:
            InputError: if one of the parameters is invalid
        """
        if self.max_file_size is not None and not 1 <= self.max_file_size <= MAX_FILE_SIZE:
            raise InputError(f"max_file_size must be between 1 and {MAX_FILE_SIZE}")
        if self.enforce_docker_system_prune and self.suppress_docker_system_prune:
            raise InputError('The arguments "--prune" and "--no-prune" are mutually exclusive')
        if self.custom_host is not None and not regex.match(
            r"^(((\d{1,3}\.){3}\d{1,3})|((([-\w_~]+\.)*([a-z]){2,})))$", self.custom_host
        ):
            raise InputError("Invalid format for custom host. Please, enter an IP or a domain name.")
        self._initialise_container_engine()

    def _initialise_container_engine(self) -> None:
        cont_eng = os.environ["CONTAINER_ENGINE"]
        if cont_eng not in ["podman", "docker"]:
            raise InputError(f"Invalid container engine: {cont_eng}. Supported engines are 'podman' and 'docker'.")
        self.container_engine = cast(Literal["podman", "docker"], cont_eng)
        self.environment = os.environ.copy()
        if self.container_engine == "podman":
            self.environment["PODMAN_COMPOSE_PROVIDER"] = "podman-compose"
        else:
            self.environment["DOCKER_COMPOSE_PROVIDER"] = "/usr/local/bin/docker-compose"


class StackHandler:
    """This class contains functions to start and stop the Docker containers of DSP-API and DSP-APP."""

    __stack_configuration: StackConfiguration
    __url_prefix: str
    __docker_path_of_user: Path
    __localhost_url = "http://0.0.0.0"

    def __init__(self, stack_configuration: StackConfiguration) -> None:
        """
        Initialize a StackHandler with a StackConfiguration

        Args:
            stack_configuration: configuration information for the StackHandler
        """
        self.__stack_configuration = stack_configuration
        self.__url_prefix = self._get_url_prefix()
        self.__docker_path_of_user = Path.home() / Path(".dsp-tools/start-stack")
        self.__docker_path_of_user.mkdir(parents=True, exist_ok=True)

    def _get_url_prefix(self) -> str:
        """
        The start-stack command needs some files from the DSP-API repository.
        By default, start-stack starts the latest deployed version of DSP-API.
        Since the last deployment, the DSP-API repository may have been updated.
        For this reason, we need to know the commit hash of the DSP-API version that is currently deployed,
        so that the files can be retrieved from the correct commit.

        This function reads the version tag in the docker-compose.yml file,
        and constructs the URL prefix necessary to retrieve the files from the DSP-API repository.

        If the latest development version of DSP-API is started,
        the URL prefix points to the main branch of the DSP-API repository.

        Returns:
            URL prefix used to retrieve files from the DSP-API repository
        """
        url_prefix_base = "https://raw.githubusercontent.com/dasch-swiss/dsp-api"

        if self.__stack_configuration.latest_dev_version:
            return f"{url_prefix_base}/main/"

        docker_compose_pth = importlib.resources.files("dsp_tools").joinpath("resources/start-stack/docker-compose.yml")
        docker_compose = yaml.safe_load(docker_compose_pth.read_bytes())
        tag = docker_compose["services"]["api"]["image"].split(":")[-1]

        return f"{url_prefix_base}/{tag}/"

    def _copy_resources_to_home_dir(self) -> None:
        """
        On most systems, Docker is not allowed to access files outside of the user's home directory.
        For this reason, copy the contents of the distribution (src/dsp_tools/resources/start-stack)
        to the user's home directory (~/.dsp-tools/start-stack).

        Important: The files of the home directory might have been modified
        by an earlier run of this method.
        So, this method must always be called, at every run of start-stack.
        """
        logger.debug("Copying resources to home directory ...")
        docker_path_of_distribution = importlib.resources.files("dsp_tools").joinpath("resources/start-stack")
        for file in docker_path_of_distribution.iterdir():
            with importlib.resources.as_file(file) as f:
                file_path = Path(f)
            shutil.copy(file_path, self.__docker_path_of_user / file.name)
        if not self.__stack_configuration.latest_dev_version:
            Path(self.__docker_path_of_user / "docker-compose.override.yml").unlink()

    def _set_custom_host(self) -> None:
        """
        To ensure the frontend can communicate with a backend on a different server, the host in the environments
        needs to be changed.
        By design the IRIs match the host of the database.

        This is done by overriding the environment variables in the docker-compose.yml and by replacing the
        configuration for the frontend.
        """
        if self.__stack_configuration.custom_host is not None:
            logger.debug("Setting custom host...")
            self.__localhost_url = f"http://{self.__stack_configuration.custom_host}"

            docker_template_path = importlib.resources.files("dsp_tools").joinpath(
                "resources/start-stack/docker-compose.override-host.j2"
            )
            docker_template = Template(docker_template_path.read_text(encoding="utf-8"))
            docker_template_rendered = docker_template.render(CUSTOM_HOST=self.__stack_configuration.custom_host)
            Path(self.__docker_path_of_user / "docker-compose.override-host.yml").write_text(
                docker_template_rendered, encoding="utf-8"
            )

            dsp_app_config_template_path = importlib.resources.files("dsp_tools").joinpath(
                "resources/start-stack/dsp-app-config.override-host.j2"
            )
            dsp_app_config_template = Template(dsp_app_config_template_path.read_text(encoding="utf-8"))
            dsp_app_config_rendered = dsp_app_config_template.render(CUSTOM_HOST=self.__stack_configuration.custom_host)
            Path(self.__docker_path_of_user / "dsp-app-config.json").unlink()
            Path(self.__docker_path_of_user / "dsp-app-config.json").write_text(
                dsp_app_config_rendered, encoding="utf-8"
            )
        Path(self.__docker_path_of_user / "docker-compose.override-host.j2").unlink()
        Path(self.__docker_path_of_user / "dsp-app-config.override-host.j2").unlink()

    def _get_sipi_docker_config_lua(self) -> None:
        """
        Retrieve the config file sipi.docker-config.lua from the DSP-API repository,
        and set the max_file_size parameter if necessary.

        Raises:
            InputError: if max_file_size is set but cannot be injected into sipi.docker-config.lua
        """
        logger.debug("Retrieving sipi.docker-config.lua...")
        docker_config_lua_response = requests.get(f"{self.__url_prefix}sipi/config/sipi.docker-config.lua", timeout=30)
        docker_config_lua_text = docker_config_lua_response.text
        if self.__stack_configuration.max_file_size:
            max_post_size_regex = r"max_post_size ?= ?[\'\"]?\d+[MG][\'\"]?"
            if not regex.search(max_post_size_regex, docker_config_lua_text):
                raise InputError("Unable to set max_file_size. Please try again without this flag.")
            docker_config_lua_text = regex.sub(
                max_post_size_regex,
                f"max_post_size = '{self.__stack_configuration.max_file_size}M'",
                docker_config_lua_text,
            )
        with open(self.__docker_path_of_user / "sipi.docker-config.lua", "w", encoding="utf-8") as f:
            f.write(docker_config_lua_text)

    def _start_up_fuseki(self) -> None:
        """
        Start up the Docker container of the fuseki database.

        Raises:
            InputError: if the database cannot be started
        """
        logger.debug("Starting up the fuseki container...")
        cmd = f"{self.__stack_configuration.container_engine} compose up -d db".split()
        completed_process = subprocess.run(
            cmd, cwd=self.__docker_path_of_user, check=False, env=self.__stack_configuration.environment
        )
        if not completed_process or completed_process.returncode != 0:
            msg = (
                f"Cannot start the API: Error while executing 'docker compose up -d db'."
                f"\n{completed_process.stderr.decode('utf-8') = }"
            )
            logger.error(f"{msg}. completed_process = '{vars(completed_process)}'")
            raise InputError(msg)

    def _wait_for_fuseki(self) -> None:
        """
        Wait up to 6 minutes, until the fuseki database is up and running.
        This function imitates the behaviour of the script dsp-api/webapi/scripts/wait-for-db.sh.
        """
        logger.debug("Waiting for the fuseki container to be up and running...")
        for _ in range(6 * 60):
            try:
                response = requests.get(f"{self.__localhost_url}:3030/$/server", auth=("admin", "test"), timeout=10)
                if response.ok:
                    logger.debug("Fuseki is now up and running.")
                    break
            except Exception:  # noqa: BLE001 (blind-except)
                time.sleep(1)
            time.sleep(1)

    def _create_knora_test_repo(self) -> None:
        """
        Inside fuseki, create the "knora-test" repository.
        This function imitates the behaviour of the script dsp-api/webapi/scripts/fuseki-init-knora-test.sh.

        Raises:
            InputError: in case of failure
        """
        logger.debug("Creating the 'knora-test' repository...")
        repo_template_response = requests.get(
            f"{self.__url_prefix}webapi/scripts/fuseki-repository-config.ttl.template",
            timeout=30,
        )
        repo_template = repo_template_response.text
        repo_template = repo_template.replace("@REPOSITORY@", "knora-test")
        response = requests.post(
            f"{self.__localhost_url}:3030/$/datasets",
            files={"file": ("file.ttl", repo_template, "text/turtle; charset=utf8")},
            auth=("admin", "test"),
            timeout=30,
        )
        if not response.ok:
            msg = (
                "Cannot start DSP-API: Error when creating the 'knora-test' repository. "
                "Is DSP-API perhaps running already?"
            )
            logger.error(f"{msg}. response = {vars(response)}")
            raise InputError(msg)

    def _load_data_into_repo(self) -> None:
        """
        Load some basic ontologies and data into the repository.
        This function imitates the behaviour of the script
        dsp-api/webapi/target/docker/stage/opt/docker/scripts/fuseki-init-knora-test.sh.

        Raises:
            InputError: if one of the graphs cannot be created
        """
        logger.debug("Loading data into the 'knora-test' repository...")
        graph_prefix = f"{self.__localhost_url}:3030/knora-test/data?graph="
        ttl_files = [
            ("webapi/src/main/resources/knora-ontologies/knora-admin.ttl", "http://www.knora.org/ontology/knora-admin"),
            ("webapi/src/main/resources/knora-ontologies/knora-base.ttl", "http://www.knora.org/ontology/knora-base"),
            ("webapi/src/main/resources/knora-ontologies/standoff-onto.ttl", "http://www.knora.org/ontology/standoff"),
            ("webapi/src/main/resources/knora-ontologies/standoff-data.ttl", "http://www.knora.org/data/standoff"),
            ("webapi/src/main/resources/knora-ontologies/salsah-gui.ttl", "http://www.knora.org/ontology/salsah-gui"),
            ("test_data/project_data/admin-data.ttl", "http://www.knora.org/data/admin"),
            ("test_data/project_data/permissions-data.ttl", "http://www.knora.org/data/permissions"),
            ("test_data/project_ontologies/anything-onto.ttl", "http://www.knora.org/ontology/0001/anything"),
            ("test_data/project_data/anything-data.ttl", "http://www.knora.org/data/0001/anything"),
        ]
        for ttl_file, graph in ttl_files:
            ttl_response = requests.get(self.__url_prefix + ttl_file, timeout=30)
            if not ttl_response.ok:
                msg = f"Cannot start DSP-API: Error when retrieving '{self.__url_prefix + ttl_file}'"
                logger.error(f"{msg}'. response = {vars(ttl_response)}")
                raise InputError(msg)
            ttl_text = ttl_response.text
            response = requests.post(
                graph_prefix + graph,
                files={"file": ("file.ttl", ttl_text, "text/turtle; charset: utf-8")},
                auth=("admin", "test"),
                timeout=30,
            )
            if not response.ok:
                logger.error(f"Cannot start DSP-API: Error when creating graph '{graph}'. response = {vars(response)}")
                raise InputError(f"Cannot start DSP-API: Error when creating graph '{graph}'")

    def _create_admin_user(self) -> None:
        """
        This function adds the default system admin user to the database.
        The password is the hash for "test".

        Raises:
            InputError: If the user cannot be created.
        """
        logger.debug("Creating the default admin user...")
        graph_prefix = f"{self.__localhost_url}:3030/knora-test/data?graph="
        admin_graph = "http://www.knora.org/data/admin"
        admin_user = """
        @prefix xsd:         <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdf:         <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix knora-admin: <http://www.knora.org/ontology/knora-admin#> .

        <http://rdfh.ch/users/root>
        rdf:type                         knora-admin:User ;
        knora-admin:username             "root"^^xsd:string ;
        knora-admin:email                "root@example.com"^^xsd:string ;
        knora-admin:givenName            "System"^^xsd:string ;
        knora-admin:familyName           "Administrator"^^xsd:string ;
        knora-admin:password             "$2a$12$7XEBehimXN1rbhmVgQsyve08.vtDmKK7VMin4AdgCEtE4DWgfQbTK"^^xsd:string ;
        knora-admin:phone                "123456"^^xsd:string ;
        knora-admin:preferredLanguage    "en"^^xsd:string ;
        knora-admin:status               "true"^^xsd:boolean ;
        knora-admin:isInSystemAdminGroup "true"^^xsd:boolean .
        """
        response = requests.post(
            graph_prefix + admin_graph,
            files={"file": ("file.ttl", admin_user, "text/turtle; charset: utf-8")},
            auth=("admin", "test"),
            timeout=30,
        )
        if not response.ok:
            logger.error(f"Cannot start DSP-API: Error when creating the admin user. response = {vars(response)}")
            raise InputError("Cannot start DSP-API: Error when creating the admin user.")

    def _initialize_fuseki(self) -> None:
        """
        Create the "knora-test" repository and load some basic ontologies and data into it.
        """
        self._create_knora_test_repo()
        if self.__stack_configuration.upload_test_data:
            self._load_data_into_repo()
        else:
            self._create_admin_user()

    def _start_remaining_docker_containers(self) -> None:
        """
        Start the other Docker containers that are not running yet.
        (Fuseki is already running at this point.)
        """
        compose_str = f"{self.__stack_configuration.container_engine} compose -f docker-compose.yml"
        if self.__stack_configuration.latest_dev_version:
            logger.debug("In order to get the latest dev version, run 'docker compose pull' ...")
            subprocess.run(
                f"{self.__stack_configuration.container_engine} compose pull".split(),
                cwd=self.__docker_path_of_user,
                check=True,
                env=self.__stack_configuration.environment,
            )
            compose_str += " -f docker-compose.override.yml"
        if self.__stack_configuration.custom_host is not None:
            compose_str += " -f docker-compose.override-host.yml"
        compose_str += " up -d"
        logger.debug(f"Running '{compose_str}' ...")
        subprocess.run(
            compose_str.split(), cwd=self.__docker_path_of_user, check=True, env=self.__stack_configuration.environment
        )

    def _wait_for_api(self) -> None:
        """
        Wait until the API is up and running.
        This mimicks the behaviour of the script webapi/scripts/wait-for-api.sh in the DSP-API repository.
        """
        logger.debug("Waiting for the API to start...")
        for num_secs in range(6 * 60):
            try:
                params = RequestParameters("GET", f"{self.__localhost_url}:3333/health", timeout=1)
                log_request(params)
                response = requests.get(params.url, timeout=params.timeout)
                log_response(response)
                if response.ok:
                    break
            except requests.exceptions.RequestException as e:
                logger.debug(f"RequestException while checking API status: {e}")
            if num_secs > 30 and num_secs % 10 == 0:
                # There is probably an issue, so we need more logs
                with contextlib.suppress():
                    docker_ps_output = subprocess.run(
                        f"{self.__stack_configuration.container_engine} ps -a".split(),
                        cwd=self.__docker_path_of_user,
                        check=True,
                        capture_output=True,
                        env=self.__stack_configuration.environment,
                    ).stdout.decode("utf-8")
                    docker_ps_output = "\n\t".join(docker_ps_output.split("\n"))
                    logger.debug(f"docker ps -a output:\n\t{docker_ps_output}")
                    docker_logs_output = subprocess.run(
                        f"{self.__stack_configuration.container_engine} logs start-stack-api-1".split(),
                        cwd=self.__docker_path_of_user,
                        check=True,
                        capture_output=True,
                        env=self.__stack_configuration.environment,
                    ).stdout.decode("utf-8")
                    docker_logs_output = "\n\t".join(docker_logs_output.split("\n"))
                    logger.debug(f"Logs of DSP-API container:\n\t{docker_logs_output}")
            time.sleep(1)
        msg = f"DSP-API is now running on {self.__localhost_url}:3333/ and DSP-APP on {self.__localhost_url}:4200/"
        logger.debug(msg)
        print(msg)

    def _execute_docker_system_prune(self) -> None:
        """
        Depending on the CLI parameters or the user's input,
        execute "docker system prune" or not.
        """
        if self.__stack_configuration.enforce_docker_system_prune:
            prune_docker = "y"
        elif self.__stack_configuration.suppress_docker_system_prune:
            prune_docker = "n"
        else:
            prune_docker = None
            while prune_docker not in ["y", "n"]:
                prune_docker = input(
                    "Allow dsp-tools to execute 'docker system prune'? \n"
                    "If you press 'y', all unused containers, networks, and images (both dangling and unused) "
                    "in your docker will be deleted.\n"
                    "It is recommended that you do this every once in a while "
                    "to keep your docker clean and running smoothly. [y/n]"
                )
        if prune_docker == "y":
            logger.debug("Running 'docker system prune --volumes -f' ...")
            subprocess.run(
                f"{self.__stack_configuration.container_engine} system prune --volumes -f".split(),
                cwd=self.__docker_path_of_user,
                check=False,
                env=self.__stack_configuration.environment,
            )

    def _start_docker_containers(self) -> None:
        """
        Start the fuseki Docker container,
        wait until it is up and running,
        load some basic ontologies and data into it,
        start the other Docker containers,
        and execute "docker system prune" if necessary.
        """
        self._start_up_fuseki()
        self._wait_for_fuseki()
        self._initialize_fuseki()
        self._start_remaining_docker_containers()
        self._wait_for_api()
        self._execute_docker_system_prune()

    def start_stack(self) -> bool:
        """
        Start the Docker containers of DSP-API and DSP-APP, and load some basic data models and data.
        After startup, ask user if Docker should be pruned or not.

        Raises:
            InputError: if the stack cannot be started with the parameters passed by the user

        Returns:
            True if everything went well, False otherwise
        """
        cmd = f"{self.__stack_configuration.container_engine} stats --no-stream"
        res = subprocess.run(cmd.split(), check=False, capture_output=True, env=self.__stack_configuration.environment)
        if res.returncode != 0:
            raise InputError(
                f"Docker is not running properly. Please start Docker and try again.\n"
                f"{cmd = }\n"
                f"{res.stderr.decode('utf-8') = }"
            )
        self._copy_resources_to_home_dir()
        self._set_custom_host()
        self._get_sipi_docker_config_lua()
        self._start_docker_containers()
        return True

    def stop_stack(self) -> bool:
        """
        Shut down the Docker containers of your local DSP stack and delete all data that is in it.

        Returns:
            True if everything went well, False otherwise
        """
        subprocess.run(
            f"{self.__stack_configuration.container_engine} compose down --volumes".split(),
            cwd=self.__docker_path_of_user,
            check=True,
            env=self.__stack_configuration.environment,
        )
        subprocess.run([self.__stack_configuration.container_engine, "system", "prune", "-f"], check=True)
        subprocess.run([self.__stack_configuration.container_engine, "volume", "prune", "-f"], check=True)
        shutil.rmtree(self.__docker_path_of_user / "sipi", ignore_errors=True)
        return True
