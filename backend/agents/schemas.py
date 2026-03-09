"""Pydantic schemas shared across all agents."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FileItem(BaseModel):
    """A single generated source file."""

    path: str = Field(
        ...,
        description="Relative file path, e.g. 'src/index.html' or 'backend/app.py'.",
    )
    content: str = Field(..., description="Full source code content.")


class SupervisorPlan(BaseModel):
    """Structured output from the Supervisor agent."""

    project_name: str = Field(..., description="Short project name.")
    stack: dict[str, str] = Field(
        ...,
        description=(
            "Technology stack mapping, e.g. "
            '{"frontend": "html_css_js", "backend": "flask", "database": "sqlite"}'
        ),
    )
    agents_needed: list[str] = Field(
        ...,
        description="List of agent names to activate: 'frontend', 'backend', 'database', 'devops'.",
    )
    shared_context: dict[str, str | int] = Field(
        default_factory=dict,
        description="Shared config like api_base, ports, project structure.",
    )
    tasks: list[AgentTask] = Field(
        ...,
        description="Ordered list of tasks assigned to specific agents.",
    )


class AgentTask(BaseModel):
    """A single task assigned to an agent."""

    agent: str = Field(..., description="Agent name: frontend, backend, database, devops.")
    instructions: str = Field(..., description="Detailed instructions for this agent.")


# Allow SupervisorPlan to reference AgentTask
SupervisorPlan.model_rebuild()


class AgentCodebase(BaseModel):
    """Output from a worker agent — list of files it produced."""

    files: list[FileItem] = Field(default_factory=list, description="Generated files.")
    notes: str = Field(default="", description="Brief notes about what was generated.")


class IntegrationResult(BaseModel):
    """Output from the Integration agent — merged and conflict-resolved codebase."""

    files: list[FileItem] = Field(..., description="Merged file tree.")
    run_command: str = Field(
        ...,
        description="Command to start the project. E.g. 'python3 -m http.server 3000'.",
    )
    notes: str = Field(default="", description="Notes about integration decisions.")


class QAVerdict(BaseModel):
    """Structured verdict from the QA agent."""

    passed: bool = Field(..., description="True if the project works correctly.")
    issues: list[str] = Field(default_factory=list, description="List of issues found.")
    failing_agent: str = Field(
        default="",
        description="Which agent should fix the issue: 'frontend', 'backend', 'database', 'devops', 'integration', or '' if passed.",
    )
    fix_instructions: str = Field(
        default="",
        description="Specific instructions for the failing agent.",
    )
