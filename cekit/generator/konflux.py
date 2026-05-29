import logging
import os
import yaml
LOGGER = logging.getLogger("cekit")

from cekit.template_helper import TemplateHelper
from cekit.generator.base import Generator
from cekit.cekit_types import PathType
from typing import TYPE_CHECKING, Callable, Dict, List

class KonfluxGenerator(Generator):
    def prepare_artifacts(self) -> None:
        LOGGER.debug("KonfluxGenerator prepare_artifacts")

        for image in self.images:
            for artifact in image.all_artifacts:
                raise NotImplementedError("Artifacts handling is not implemented")

    def generate(self) -> None:
        super(KonfluxGenerator, self).generate()
        self._render_rpm_lockfile()

    def _render_rpm_lockfile(self) -> None:
        y = self.image.get("konflux",{}).get("rpms.in.yaml", {})
        if not y:
            return

        y['packages'] = self._populate_packages()

        f = os.path.join(self.target, "image", "rpms.in.yaml")
        with open(f, "w") as fh:
            yaml.safe_dump(y, fh, default_flow_style=False)

    def _populate_packages(self) -> None:
        th = TemplateHelper(self._module_registry)
        pkgs = list(set(th.packages_to_install(self.image)))
        pkgs.sort()
        return pkgs
