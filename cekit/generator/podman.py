from typing import List

from cekit.cekit_types import PathType
from cekit.generator.docker import DockerGenerator

class PodmanGenerator(DockerGenerator):
    def __init__(
        self,
        descriptor_path: PathType,
        target: PathType,
        container_file: str,
        overrides: List[str],
        no_squash: bool,
    ):
        super(DockerGenerator, self).__init__(
            descriptor_path, target, container_file, overrides, no_squash
        )
