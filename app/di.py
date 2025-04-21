from functools import lru_cache

from dishka import AsyncContainer

container: AsyncContainer | None = None


class ContainerNotSetError(Exception):
    pass


@lru_cache()
def get_container() -> AsyncContainer:
    global container
    if not container:
        raise ContainerNotSetError("Could n't get container")
    return container