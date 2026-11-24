import logging
import os
from typing import List

from cekit.cekit_types import PathType
from cekit.generator.local import LocalGenerator
from cekit.tools import split_image_name_ref

try:
    import docker
except ModuleNotFoundError:
    docker = None

logger = logging.getLogger("cekit")

_list_manifest_types = [
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
]


class DockerGenerator(LocalGenerator):
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


    def resolve_base_image_digest(self):
        """Update the base image reference with a digest-reference equivalent,
        if one isn't already specified."""
        frm = self.image.base
        logger.debug(f"resolve_base_image_digest: {frm}")

        # If the base image is already a checksum-reference, do nothing
        if frm.find("@") > 0:
            logger.debug("resolve_base_image_digest: base image already checksum-referenced")
            return

        if not docker:
            logger.warning("couldn't import docker python library, skipping resolve_base_image_digest")
            return

        try: # XXX: version 28? timeout default value?
            client = docker.from_env(version="auto")
            info = client.api.inspect_image(frm)
        except docker.errors.DockerException as e:
            logger.error(f"couldn't inspect {frm}: {e}")
            return

        descriptor = info.get("Descriptor", {})
        digest = descriptor.get("digest")
        if digest and descriptor.get("mediaType") in _list_manifest_types:
            (image_no_tag, _) = split_image_name_ref(frm)
            self.image.base = f"{image_no_tag}@{digest}"
