from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SlackMessage:
    author: str
    body: str


@dataclass(frozen=True)
class Ticket:
    reporter: str
    body: str
    slack_thread: list[SlackMessage] = field(default_factory=list)


@dataclass(frozen=True)
class Hint:
    cost_xp: int
    text: str


@dataclass(frozen=True)
class ReviewCriteria:
    must_fix_case_sensitivity: bool = False
    must_add_regression_test: bool = False
    must_not_swallow_exception: bool = False
    explanation_required: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    company: str
    severity: str
    difficulty: str
    language: str
    skills: list[str]
    learning_objectives: list[str]
    ticket: Ticket
    repo_path: str
    entry_service: str
    visible_test_command: str
    root_cause: str
    hidden_tests: str
    hints: list[Hint]
    review_criteria: ReviewCriteria
    scenario_dir: Path

    @property
    def repo_dir(self) -> Path:
        return self.scenario_dir / self.repo_path

    @property
    def hidden_tests_path(self) -> Path:
        return self.scenario_dir / self.hidden_tests
