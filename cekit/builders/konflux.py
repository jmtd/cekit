import logging
import os
import pathlib
from cekit.builder import Builder
from cekit.tools.git import Git
from cekit.errors import CekitError
from cekit.config import Config

LOGGER = logging.getLogger("cekit")
CONFIG = Config()

class KonfluxBuilder(Builder):
    """Class representing Konflux builder."""


    def __init__(self, params):
        super(KonfluxBuilder, self).__init__("konflux", params)
        LOGGER.debug("KonfluxBuilder init")

        self.git: Git
        self.repopath: pathlib.Path

    def run(self) -> None:
        """
        run is a no-op for the Konflux builder.
        """
        LOGGER.debug("KonfluxBuilder run")

    def before_build(self) -> None:
        """
        This is where the magic happens.
        """
        LOGGER.debug("KonfluxBuilder before_build")

        self._prepare_konflux_git()

    def _prepare_konflux_git(self) -> None:
        LOGGER.debug("KonfluxBuilder _prepare_konflux_git")

        repokey: "Repository" = self.generator.image.get("konflux", {}).get("repository",{})
        repo: str = repokey.get("uri")
        ref: str = repokey.get("ref")
        if not (repo and ref):
            raise CekitError("""
                Konflux Builder needs konflux.repository.uri and konflux.repository.ref defined."
            """)

        components = [ x.get('value',None) for x in self.generator.image.get("labels")
            if x.get('name','') == 'com.redhat.component' ]
        if len(components) < 1:
            raise CekitError("""
            Konflux Builder needs images to have the label com.redhat.component.
            """)
        dirname = components[0]
        if not dirname:
            raise CekitError("""
            Konflux Builder needs images to have the label com.redhat.component.
            """)

        self.repopath: PathType = os.path.join(
            os.path.expanduser(CONFIG.get("common", "work_dir")), "konflux", dirname
        )
        LOGGER.debug(f"KonfluxBuilder: Using git repo path of {self.repopath}")
        if not os.path.exists(os.path.dirname(self.repopath)):
            os.makedirs(os.path.dirname(self.repopath))

        self.git = Git(
            self.repopath, # output
            self.target,   # source
            repo,          # repo
            ref,           # branch
            False,         # osbs_extra ?
            True           # noninteractive
        )

        self.git.prepare(
            False, # stageself.params.stage, self.params.user)
            None,  # user (for rhpkg)
        )
        self.git.clean(
            [] # artifacts
        )


