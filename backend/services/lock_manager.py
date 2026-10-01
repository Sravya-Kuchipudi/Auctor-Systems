"""
Auctor Systems — Project Concurrency Protection (Phase 4C Stage 1 Step 3)
Provides project-scoped asynchronous locks to serialize conflicting operations
(rollback, prompt revision creation, initial generation, filesystem reconciliation)
on the same project, while allowing independent projects to run in parallel.
"""

import asyncio
import logging
from typing import Dict, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("auctor.concurrency")


class ConcurrencyConflictError(Exception):
    """Raised when an operation conflicts with an ongoing operation on the same project."""
    def __init__(self, message: str, project_id: Optional[str] = None, active_op: Optional[str] = None):
        super().__init__(message)
        self.project_id = project_id
        self.active_op = active_op


class ReentrantAsyncLock:
    """
    Task-reentrant asynchronous lock.
    Allows the same asyncio Task to enter nested lock blocks without deadlocking,
    while enforcing strict mutual exclusion against different Tasks.
    """
    def __init__(self):
        self._lock = asyncio.Lock()
        self._owner: Optional[asyncio.Task] = None
        self._depth: int = 0

    async def acquire(self):
        current_task = asyncio.current_task()
        if self._owner == current_task:
            self._depth += 1
            return
        await self._lock.acquire()
        self._owner = current_task
        self._depth = 1

    def release(self):
        current_task = asyncio.current_task()
        if self._owner != current_task:
            raise RuntimeError("Cannot release a lock owned by another task")
        self._depth -= 1
        if self._depth == 0:
            self._owner = None
            self._lock.release()

    def locked(self) -> bool:
        return self._lock.locked()

    @property
    def owner(self) -> Optional[asyncio.Task]:
        return self._owner


class ProjectLockManager:
    """
    Project-scoped concurrency manager.
    Guarantees:
    - Operations on the same project are mutually exclusive.
    - Operations on different projects run concurrently without contention.
    - Locks are reliably released on success, exception, or cancellation.
    - Non-blocking acquisition raises ConcurrencyConflictError (mapped to HTTP 409).
    """

    def __init__(self):
        self._locks: Dict[str, ReentrantAsyncLock] = {}
        self._active_ops: Dict[str, str] = {}
        self._meta_lock: Optional[asyncio.Lock] = None

    def _get_meta_lock(self) -> asyncio.Lock:
        if self._meta_lock is None:
            self._meta_lock = asyncio.Lock()
        return self._meta_lock

    async def get_lock(self, project_id: str) -> ReentrantAsyncLock:
        meta = self._get_meta_lock()
        async with meta:
            if project_id not in self._locks:
                self._locks[project_id] = ReentrantAsyncLock()
            return self._locks[project_id]

    def is_locked(self, project_id: str) -> bool:
        lock = self._locks.get(project_id)
        return lock.locked() if lock else False

    def get_active_op(self, project_id: str) -> Optional[str]:
        return self._active_ops.get(project_id)

    def check_conflict(self, project_id: str, op_name: str = "operation") -> None:
        """
        Check if project is currently locked by a different task.
        Raises ConcurrencyConflictError if locked by another task, otherwise returns None.
        """
        lock = self._locks.get(project_id)
        if lock and lock.locked():
            try:
                current_task = asyncio.current_task()
            except RuntimeError:
                current_task = None
            if lock.owner is not None and lock.owner != current_task:
                active_op = self._active_ops.get(project_id, "an ongoing operation")
                msg = (
                    f"Operation conflict on project '{project_id}': cannot execute '{op_name}' "
                    f"because '{active_op}' is currently in progress."
                )
                logger.warning(msg)
                raise ConcurrencyConflictError(msg, project_id=project_id, active_op=active_op)

    @asynccontextmanager
    async def acquire(
        self,
        project_id: str,
        op_name: str = "operation",
        blocking: bool = False,
        timeout: Optional[float] = None,
    ):
        """
        Acquire a project lock.
        If blocking=False and already locked by a different task, immediately raises ConcurrencyConflictError.
        If blocking=True with timeout, waits up to timeout seconds.
        Always releases lock and clears active_op on normal exit, exception, or cancellation.
        """
        lock = await self.get_lock(project_id)
        current_task = asyncio.current_task()

        # If locked by another task and non-blocking requested
        if lock.locked() and lock.owner != current_task:
            if not blocking:
                current_op = self._active_ops.get(project_id, "an ongoing operation")
                msg = (
                    f"Operation conflict on project '{project_id}': cannot execute '{op_name}' "
                    f"because '{current_op}' is currently in progress."
                )
                logger.warning(msg)
                raise ConcurrencyConflictError(msg, project_id=project_id, active_op=current_op)

        if timeout is not None and timeout > 0:
            try:
                await asyncio.wait_for(lock.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                current_op = self._active_ops.get(project_id, "an ongoing operation")
                msg = (
                    f"Timed out waiting to acquire lock on project '{project_id}' for '{op_name}'. "
                    f"Project is busy with '{current_op}'."
                )
                logger.warning(msg)
                raise ConcurrencyConflictError(msg, project_id=project_id, active_op=current_op)
        else:
            await lock.acquire()

        prev_op = self._active_ops.get(project_id)
        self._active_ops[project_id] = op_name
        logger.info(f"Acquired project lock [{project_id}] for op='{op_name}'")
        try:
            yield
        finally:
            if prev_op:
                self._active_ops[project_id] = prev_op
            else:
                self._active_ops.pop(project_id, None)
            lock.release()
            logger.info(f"Released project lock [{project_id}] for op='{op_name}'")


# Singleton instance shared across the application
project_lock_manager = ProjectLockManager()
