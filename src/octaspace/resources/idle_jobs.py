from __future__ import annotations

from ..response import APIResponse
from .base import Resource


class IdleJobsResource(Resource):
    """Jobs that your nodes run while nobody rents them."""

    def find(self, *, node_id: int | str, job_id: int | str) -> APIResponse:
        """Return an idle job.

        ``GET /idle_jobs/{node_id}/{job_id}``.

        Args:
            node_id: The node that runs the job.
            job_id: The job.
        """
        return self.get(f"/idle_jobs/{self.encode(node_id)}/{self.encode(job_id)}")

    def logs(self, *, node_id: int | str, job_id: int | str) -> APIResponse:
        """Return the logs of an idle job.

        ``GET /idle_jobs/{node_id}/{job_id}/logs``.

        Args:
            node_id: The node that runs the job.
            job_id: The job.

        Raises:
            NotFoundError: The job does not exist.
        """
        return self.get(f"/idle_jobs/{self.encode(node_id)}/{self.encode(job_id)}/logs")
