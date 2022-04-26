import streamlit as st
from typing import List
from specklepy.objects import Base
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.api.models import Stream, Commit, Branch

from devtools import debug


def format_commit(commit: Commit) -> str:
    """String format commit object"""
    return (
        f"{commit.message} | {commit.createdAt.strftime('%d/%m/%Y, %H:%M:%S')} ({commit.id})"
        if commit
        else None
    )


def format_branch(branch: Branch) -> str:
    """String format branch object"""
    return (
        f"{branch.name} | {branch.description or 'no description'} ({branch.id})"
        if branch
        else None
    )


def format_glulam(glulam: Base) -> str:
    """String format glulam object"""
    return f"{glulam.id} | {getattr(glulam, 'tag', 'no tag')}" if glulam else None


def simplify_glulam(glulam: Base) -> dict:
    """Simplify glulam objects for cleaner data preview"""
    return {
        "id": glulam.id,
        "tag": glulam.tag,
        "units": glulam.units,
        "width": glulam["@glulam"].dataValue.width,
        "height": glulam["@glulam"].dataValue.height,
    }


def list_to_md(list_items, column):
    """Format an iterable as a mardown list"""
    if not list_items:
        return ""
    list_str = "".join(f"- {item}\n" for item in list_items)
    return column.markdown(list_str)


def preview_from_commit(wrapper: StreamWrapper, commit, height=400) -> str:
    """Create an iframe embed from a commit"""
    embed_src = f"{wrapper.server_url}/embed?stream={wrapper.stream_id}&commit={commit.id if commit else ''}"

    return st.components.v1.iframe(src=embed_src, height=height)


def preview_from_object(wrapper: StreamWrapper, object_id, height=400):
    """Create an iframe embed from an object"""
    embed_src = (
        f"{wrapper.server_url}/embed?stream={wrapper.stream_id}&object={object_id}"
    )

    return st.components.v1.iframe(src=embed_src, height=height)


def send_notes(wrapper: StreamWrapper, glulams: List[Base], branch_name="main") -> str:
    """Send updated glulam notes to Speckle"""
    commit_obj = Base()
    commit_obj["@glulams"] = glulams

    obj_id = operations.send(commit_obj, [wrapper.get_transport()])
    client = wrapper.get_client()
    return client.commit.create(
        wrapper.stream_id,
        obj_id,
        branch_name,
        message="updated notes from glulam dashboard",
    )
