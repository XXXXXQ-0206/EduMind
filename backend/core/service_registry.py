"""Service boundary registry for the current modular monolith.

The backend still runs as a single FastAPI process, but routes are grouped by
the service that should eventually own them. Keeping this registry explicit
lets us move one boundary at a time behind an API gateway without changing the
public API contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fastapi import APIRouter

from api.routes import (
    ai_core,
    auth,
    bilibili,
    chat,
    companion,
    debate,
    exam,
    files,
    flashcards,
    lesson_plan,
    notes,
    paper,
    planner,
    podcast,
    quiz,
    slides,
    speaking,
    tasks,
    teaching_video,
    transcriber,
)


@dataclass(frozen=True)
class RouteMount:
    """A router mounted by the modular monolith."""

    router: APIRouter
    tag: str


@dataclass(frozen=True)
class ServiceBoundary:
    """A future microservice boundary and its currently owned routes."""

    name: str
    description: str
    default_port: int
    mounts: tuple[RouteMount, ...]


SERVICE_BOUNDARIES: tuple[ServiceBoundary, ...] = (
    ServiceBoundary(
        name="identity",
        description="Accounts, sessions, role-neutral authentication, and token validation.",
        default_port=5101,
        mounts=(
            RouteMount(auth.router, "auth"),
        ),
    ),
    ServiceBoundary(
        name="learning-content",
        description="Student-facing learning workflows and shared interactive study tools.",
        default_port=5102,
        mounts=(
            RouteMount(chat.router, "chat"),
            RouteMount(notes.router, "notes"),
            RouteMount(quiz.router, "quiz"),
            RouteMount(flashcards.router, "flashcards"),
            RouteMount(companion.router, "companion"),
            RouteMount(exam.router, "exam"),
            RouteMount(debate.router, "debate"),
            RouteMount(tasks.router, "tasks"),
            RouteMount(planner.router, "planner"),
        ),
    ),
    ServiceBoundary(
        name="asset-library",
        description="Uploaded files, user file metadata, parsing entrypoints, and transcription.",
        default_port=5103,
        mounts=(
            RouteMount(files.router, "files"),
            RouteMount(transcriber.router, "transcriber"),
        ),
    ),
    ServiceBoundary(
        name="ai-core",
        description="Central LLM and embedding provider access for internal services.",
        default_port=5106,
        mounts=(
            RouteMount(ai_core.router, "ai_core"),
        ),
    ),
    ServiceBoundary(
        name="media-generation",
        description="Audio, speech evaluation, external media providers, and Bilibili MCP search.",
        default_port=5104,
        mounts=(
            RouteMount(speaking.router, "speaking"),
            RouteMount(podcast.router, "podcast"),
            RouteMount(bilibili.router, "bilibili"),
        ),
    ),
    ServiceBoundary(
        name="teaching-content",
        description="Teacher-facing lesson plans, slides, papers, and teaching videos.",
        default_port=5105,
        mounts=(
            RouteMount(slides.router, "slides"),
            RouteMount(lesson_plan.router, "lesson_plan"),
            RouteMount(paper.router, "paper"),
            RouteMount(teaching_video.router, "teaching_video"),
        ),
    ),
)


def iter_route_mounts(boundaries: Iterable[ServiceBoundary] = SERVICE_BOUNDARIES) -> Iterable[RouteMount]:
    """Yield all route mounts in stable public API order."""

    for boundary in boundaries:
        yield from boundary.mounts


def get_service_boundary(name: str) -> ServiceBoundary:
    """Return a service boundary by name."""

    normalized = (name or "").strip().lower()
    for boundary in SERVICE_BOUNDARIES:
        if boundary.name == normalized:
            return boundary
    known = ", ".join(boundary.name for boundary in SERVICE_BOUNDARIES)
    raise ValueError(f"Unknown service boundary '{name}'. Expected one of: {known}")
