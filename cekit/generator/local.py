import logging
import os
from typing import List

from cekit.cekit_types import PathType
from cekit.generator.base import Generator

logger = logging.getLogger("cekit")

class LocalGenerator(Generator):
    """
    An abstract generator for 'local'-style builders, which fetch artifacts
    locally during the build.
    """
    def __init__(
        self,
        descriptor_path: PathType,
        target: PathType,
        container_file: str,
        overrides: List[str],
        no_squash: bool,
    ):
        super(LocalGenerator, self).__init__(
            descriptor_path, target, container_file, overrides, no_squash
        )
        self._fetch_repos = True

    def prepare_artifacts(self):
        """Goes through artifacts section of image descriptor
        and fetches all of them
        """

        logger.info("Handling artifacts for docker...")
        target_dir = os.path.join(self.target, "image")

        for image in self.images:
            for artifact in image.all_artifacts:
                artifact.copy(target_dir)

        logger.debug("Artifacts handled")
