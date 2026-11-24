import logging

from typing import List

from cekit.cekit_types import PathType
from cekit.generator.local import LocalGenerator
from cekit.tools import split_image_name_ref

import json
import subprocess
import shutil

LOGGER = logging.getLogger("cekit")

_podman = shutil.which('podman')
_skopeo = shutil.which('skopeo')

_list_manifest_types = [
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
]

def _is_manifest_list(ref, uriproto="containers-storage:"):
    out = json.loads(subprocess.run(
        [_skopeo, "inspect", "--raw", f"{uriproto}{ref}"],
        capture_output=True, text=True, check=True
    ).stdout)

    return out.get("mediaType") in _list_manifest_types or out.get("manifests")

class PodmanGenerator(LocalGenerator):
    def __init__(
        self,
        descriptor_path: PathType,
        target: PathType,
        container_file: str,
        overrides: List[str],
        no_squash: bool,
    ):
        super(PodmanGenerator, self).__init__(
            descriptor_path, target, container_file, overrides, no_squash
        )

    _uriproto = "containers-storage:"
    _remote_podman = False

    def resolve_base_image_digest(self):
        """Update the base image reference with a digest-reference equivalent,
        if one isn't already specified."""
        frm = self.image.base
        LOGGER.debug(f"resolve_base_image_digest: {frm}")

        # If the base image is already a checksum-reference, do nothing
        if frm.find("@") > 0:
            LOGGER.debug("resolve_base_image_digest: base image already checksum-referenced")
            return

        self._handle_remote_podman()

        if not _podman:
            LOGGER.warning("couldn't find podman, can't resolve image digest")
            return
        if not (self._remote_podman or _skopeo):
            LOGGER.warning("couldn't find skopeo, can't resolve image digest")
            return

        # look up the base image and try to find a digest-reference
        cmd = [_podman , 'image', 'inspect', '--format', 'json', '--', frm]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            LOGGER.error(cmd)
            LOGGER.error(result.stderr) # XXX: tag?
            return
        js = json.loads(result.stdout)[0]
        digests = js.get('RepoDigests', [])

        for digest in digests:
            try:
                if _is_manifest_list(digest, self._uriproto):
                    (image_no_tag, _) = split_image_name_ref(frm)
                    sha256sum    = digest.rpartition("@")[-1]

                    newfrm = f"{image_no_tag}@{sha256sum}"
                    LOGGER.debug(f"rewriting FROM to {newfrm}")
                    self.image['from'] = newfrm
                    return

            except subprocess.SubprocessError as e:
                LOGGER.error(f"error inspecting container metadata for {digest}\n")
                continue

    def _handle_remote_podman(self):
        """Podman may be configured to connect to a remote host, e.g. when
        used with Podman Machine on Mac/Windows. In that scenario, a local
        container storage lookup with skopeo will fail. Instead, attempt to
        connect to a remote docker registry."""

        cmd = [_podman , 'info', '--format', '{{.Host.ServiceIsRemote}}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            LOGGER.error(cmd)
            LOGGER.error(result.stderr)
            return
        self._remote_podman = json.loads(result.stdout)
        if self._remote_podman:
            self._uriproto = "docker://"
            LOGGER.debug("Podman is remote. Switching look-up scheme to docker://")
