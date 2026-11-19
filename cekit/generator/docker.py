import logging
import os
from typing import List

from cekit.cekit_types import PathType
from cekit.config import Config
from cekit.generator.base import Generator
from cekit.tools import split_image_name_ref

import json
import subprocess
import shutil

logger = logging.getLogger("cekit")
config = Config()

_docker = shutil.which('docker')

_list_manifest_types = [
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
]


def _is_manifest_list(ref):
    out = json.loads(subprocess.run(
        [_skopeo, "inspect", "--raw", f"docker-daemon:{ref}"],
        capture_output=True, text=True, check=True
    ).stdout)

    return out.get("mediaType") in _list_manifest_types or out.get("manifests")


class DockerGenerator(Generator):
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

    def resolve_base_image_digest(self):
        """Update the base image reference with a digest-reference equivalent,
        if one isn't already specified."""
        frm = self.image.base
        logger.debug(f"resolve_base_image_digest: {frm}")

        # If the base image is already a checksum-reference, do nothing
        if frm.find("@") > 0:
            logger.debug("resolve_base_image_digest: base image already checksum-referenced")
            return

        if not _docker:
            logger.warning("couldn't find docker, can't resolve image digest")
            return

        # look up the base image and try to find a digest-reference
        cmd = [_docker , 'image', 'inspect', '--format', '{{json .Descriptor}}', '--', frm]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(cmd)
            logger.error(result.stderr) # XXX: tag?
            return
        js = json.loads(result.stdout)

        if js.get("mediaType","") in _list_manifest_types:
            sha256sum = js.get('digest','')
            (image_no_tag, _) = split_image_name_ref(frm)
            newfrm = f"{image_no_tag}@{sha256sum}"
            logger.debug(f"rewriting FROM to {newfrm}")
            self.image.base = newfrm
