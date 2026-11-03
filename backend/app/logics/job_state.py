from app.models import JobStatus, UserRole

VALID_TRANSITIONS = {
    JobStatus.REQUESTED: {JobStatus.QUOTED, JobStatus.CANCELLED},
    JobStatus.QUOTED: {JobStatus.ACCEPTED, JobStatus.CANCELLED},
    JobStatus.ACCEPTED: {JobStatus.EN_ROUTE, JobStatus.CANCELLED},
    JobStatus.EN_ROUTE: {JobStatus.IN_PROGRESS, JobStatus.CANCELLED},
    JobStatus.IN_PROGRESS: {JobStatus.COMPLETED},
    JobStatus.COMPLETED: set(),
    JobStatus.CANCELLED: set(),
}

STATUS_OWNER_ROLE = {
    JobStatus.QUOTED: UserRole.PROVIDER,
    JobStatus.ACCEPTED: UserRole.CUSTOMER,
    JobStatus.EN_ROUTE: UserRole.PROVIDER,
    JobStatus.IN_PROGRESS: UserRole.PROVIDER,
    JobStatus.COMPLETED: UserRole.PROVIDER,
}


class InvalidTransitionError(Exception):
    pass


def validate_transition(current: JobStatus, new: JobStatus, actor_role: UserRole) -> None:
    if new not in VALID_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(f"Cannot move job from {current.value} to {new.value}")

    if new == JobStatus.CANCELLED:
        if actor_role not in (UserRole.CUSTOMER, UserRole.PROVIDER, UserRole.ADMIN):
            raise InvalidTransitionError("Only the customer or provider can cancel a job")
        return

    expected_role = STATUS_OWNER_ROLE.get(new)
    if expected_role and actor_role not in (expected_role, UserRole.ADMIN):
        raise InvalidTransitionError(f"Only a {expected_role.value} (or admin) can set status to {new.value}")