from collections import defaultdict, deque
from functools import partial
import threading
import uuid

from .utils import eat_but_log_errors


MYPY = False
if MYPY:
    from typing import (
        AbstractSet, Callable, DefaultDict, Deque, Dict, List, Optional, Tuple, TypedDict
    )
    from GitSavvy.core.git_mixins.active_branch import Commit
    from GitSavvy.core.git_mixins.branches import Branch
    from GitSavvy.core.git_mixins.stash import Stash
    from GitSavvy.core.git_mixins.status import HeadState, WorkingDirState
    from GitSavvy.core.git_mixins.tags import TagList

    RepoPath = str
    RepoStore = TypedDict(
        'RepoStore',
        {
            "status": WorkingDirState,
            "head": HeadState,
            "long_status": str,
            "short_status": str,
            "branches": List[Branch],
            "remotes": Dict[str, str],
            "local_tags": TagList,
            "last_branches": Deque[Optional[str]],
            "last_local_branch_for_rebase": Optional[str],
            "last_remote_used": Optional[str],
            "last_remote_used_for_push": Optional[str],
            "last_remote_used_with_option_all": Optional[str],
            "last_reset_mode_used": Optional[str],
            "short_hash_length": int,
            "stashes": List[Stash],
            "recent_commits": List[Commit],
            "descriptions": Dict[str, str],
        },
        total=False
    )
    SubscriberKey = str
    Keys = AbstractSet[str]


def initial_state():
    # type: () -> RepoStore
    return {
        "last_branches": deque([None] * 2, 2),
    }


state = defaultdict(initial_state)  # type: DefaultDict[RepoPath, RepoStore]
subscribers = {}  # type: Dict[SubscriberKey, Tuple[RepoPath, Keys, Callable]]

lock = threading.Lock()


def update_state(repo_path, partial_state):
    # type: (RepoPath, RepoStore) -> None
    with lock:
        state[repo_path].update(partial_state)
    notify_all(repo_path, partial_state.keys(), state[repo_path])


def notify_all(repo_path, updated_keys, current_state):
    # type: (RepoPath, Keys, RepoStore) -> None
    for (subscribed_repo_path, keys, fn) in subscribers.values():
        if (
            subscribed_repo_path in {repo_path, "*"}
            and updated_keys & keys
        ):
            with eat_but_log_errors():
                fn(repo_path, current_state)


def current_state(repo_path):
    # type: (RepoPath) -> RepoStore
    return state[repo_path]


def subscribe(repo_path, keys, fn):
    # type: (RepoPath, Keys, Callable) -> Callable[[], None]
    key = uuid.uuid4().hex
    subscribers[key] = (repo_path, keys, fn)
    return partial(_unsubscribe, key)


def _unsubscribe(key):
    # type: (SubscriberKey) -> None
    subscribers.pop(key, None)
