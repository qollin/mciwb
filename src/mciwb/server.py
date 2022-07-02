"""
Functions for launching and controlling a Minecraft server in a Docker container.
"""
import logging
import shutil
from datetime import datetime
from pathlib import Path
from time import sleep

from docker import from_env
from docker.models.containers import Container

from mciwb import Client

HOST = "localhost"

# the locally mapped backup folder for minecraft data
backup_folder = Path.home() / "mciwb_backups"


class MinecraftServer:
    def __init__(
        self,
        name: str,
        rcon: int,
        password: str,
        server_folder: Path,
        world_type: str,
        keep: bool = True,
    ) -> None:
        self.rcon = rcon
        self.port = rcon + 1
        self.name = name
        self.password = password
        self.server_folder = server_folder
        self.world = self.server_folder / "world"
        self.world_type = world_type
        self.container = None
        self.keep = keep

    def wait_server(self):
        """
        Wait until the server is ready to accept rcon connections

        Multiple calls to this with container restarts require passing a count.
        This is how many times the wait code looks for the server to come online
        in the logs.

        This is required because the --since argument to the docker logs command
        fails to return any logs at all.
        """

        start_time: datetime = datetime.now()
        timeout = 100

        assert isinstance(self.container, Container)

        self.container.reload()
        if self.container.status != "running":
            logs = "\n".join(str(self.container.logs()).split(r"\n"))
            raise RuntimeError(f"minecraft server failed to start\n\n{logs}")

        logging.info("waiting for server to come online ...")
        for block in self.container.logs(stream=True):
            logging.debug(block.decode("utf-8").strip())
            if b"RCON running" in block:
                break
            elapsed = datetime.now() - start_time
            if elapsed.total_seconds() > timeout:
                raise RuntimeError("Timeout Starting minecraft")

        # wait until a connection is available
        for _ in range(10):
            try:
                with Client(HOST, self.rcon, passwd=self.password):
                    pass
                break
            except ConnectionRefusedError:
                sleep(2)
        else:
            raise RuntimeError("Timeout Starting minecraft")
        logging.info(f"Server {self.name} is online on port {self.port}")

    def stop(self):
        """
        Stop the minecraft server
        """
        assert isinstance(self.container, Container)
        logging.info(f"Stopping Minecraft Server {self.name} ...")
        self.container.stop()
        self.container.wait()

        logging.info(f"Stopped Minecraft Server {self.name} ...")

    def start(self):
        """
        Start the minecraft server
        """
        assert isinstance(self.container, Container)
        logging.info(f"Starting Minecraft Server {self.name} ...")
        self.container.start()
        self.wait_server()
        logging.info(f"Started Minecraft Server {self.name} ...")

    def minecraft_remove(self):
        """
        Remove a minecraft server container
        """
        # set env var MCIWB_KEEP_SERVER to keep server alive for faster
        # repeated tests and viewing the world with a minecraft client
        if self.container and not self.keep:
            logging.info(f"Removing Minecraft Server {self.name} ...")
            self.stop()
            self.container.remove()

    def create(self, world=None, test=False) -> None:
        """
        Spin up a test minecraft server in a container

        world: a zip file to use as the world data
        """

        # create and launch minecraft container once per session
        docker_client = from_env()

        for container in docker_client.containers.list(all=True):
            assert isinstance(container, Container)
            if container.name == self.name:
                logging.info(f"Creating Minecraft Server '{self.name}' ...")
                self.container = container
                if container.status == "running":
                    logging.info(
                        f"Minecraft Server '{self.name}' "
                        f"already running on port {self.port}"
                    )
                    return
                else:
                    logging.info(f"Minecraft Server '{self.name}' exists. restarting")
                    container.start()
                    self.wait_server()
                    return

        env = {
            "EULA": "TRUE",
            "SERVER_PORT": self.port,
            "RCON_PORT": self.rcon,
            "ENABLE_RCON": "true",
            "RCON_PASSWORD": self.password,
            "SEED": 0,
            "LEVEL_TYPE": self.world_type,
            "OPS": "TransformerScorn",
            "MODE": "creative",
            "SPAWN_PROTECTION": "FALSE",
        }

        if test:
            env.update(
                {
                    "GENERATE_STRUCTURES": "false",
                    "SPAWN_ANIMALS": "false",
                    "SPAWN_MONSTERS": "false",
                    "SPAWN_NPCS": "false",
                    "VIEW_DISTANCE": " 5",
                    "SEED": 0,
                    "LEVEL_TYPE": "FLAT",
                }
            )

            # offline mode disables OPS so dont use it if we are keeping the server
            # for local testing. But normally for running CI we want this option.
            if not self.keep:
                env["ONLINE_MODE"] = "FALSE"

        if world:
            env["WORLD"] = str(world)

        if not self.server_folder.exists():
            self.server_folder.mkdir(parents=True)
        elif test:
            shutil.rmtree(self.server_folder)
            self.server_folder.mkdir(parents=True)

        container = docker_client.containers.run(
            "itzg/minecraft-server",
            detach=True,
            environment=env,
            network_mode="host",
            restart_policy={"Name": "always" if self.keep else "no"},
            volumes={
                str(self.server_folder): {"bind": "/data", "mode": "rw"},
                str(backup_folder): {"bind": str(backup_folder), "mode": "rw"},
            },
            name=self.name,
        )

        self.container = container

        self.wait_server()

    @classmethod
    def stop_named(cls, name: str):
        """
        Stop a minecraft server by name
        """
        docker_client = from_env()
        for container in docker_client.containers.list(all=True):
            assert isinstance(container, Container)
            if container.name == name:
                logging.info(f"Stopping Minecraft Server {name} ...")
                container.stop()
                container.wait()
                container.remove()
                return
        logging.warning(f"Minecraft Server '{name}' not found")
