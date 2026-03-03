import logging
LOGGER = logging.getLogger("cekit")

from cekit.generator.base import Generator

class KonfluxGenerator(Generator):
    def init(self):
        LOGGER.debug("KonfluxGenerator init")
        super(KonfluxGenerator, self).init()

    def prepare_artifacts(self) -> None:
        LOGGER.debug("KonfluxGenerator prepare_artifacts")

        for image in self.images:
            for artifact in image.all_artifacts:
                raise NotImplementedError("Artifacts handling is not implemented")
