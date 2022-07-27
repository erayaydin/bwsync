import os
from typing import List, Optional

import typer
from atlassian.bitbucket import Cloud
from git import Repo
from rich.console import Console


def main(
    workspace: str = typer.Argument(
        ..., help="Workspace name"
    ),
    username: str = typer.Option(
        ..., prompt=True
    ),
    password: str = typer.Option(
        ..., prompt=True, confirmation_prompt=True, hide_input=True
    ),
    language: Optional[List[str]] = typer.Option(None, help="Specific programming language for sync repositories"),
    exclude_project: Optional[List[str]] = typer.Option(None, help="Exclude repositories which belongs to the project"),
    clone_method: str = typer.Option("ssh", help="Preferred clone method (https, ssh)"),
    output: str = typer.Option("output", help="Output directory for cloning"),
):
    """
    Download or sync bitbucket workspace repositories
    """
    console = Console()
    console.print("[green]Selected workspace:[/green]", f"[bold cyan]{workspace}[/bold cyan]")
    console.print("[green]Authenticate as:[/green]", f"[bold cyan]{username}[/bold cyan]")
    if exclude_project:
        console.print("[green]Excluded projects:[/green]", f"[bold cyan]{', '.join(exclude_project)}[/bold cyan]")
    if language:
        console.print("[green]Programming languages:[/green]", f"[bold cyan]{', '.join(language)}[/bold cyan]")

    with console.status("[bold green]Initializing...") as status:
        bitbucket = Cloud(
            username=username,
            password=password,
            cloud=True
        )

        clone_urls = {}

        status.update("[bold green]Retrieving repositories...")
        for repository in bitbucket.workspaces.get(workspace).repositories.each():
            if language and repository.data["language"] not in language:
                continue

            if exclude_project and repository.data["project"]["name"] in exclude_project:
                continue

            clone_urls[repository.name] = _get_clone_url(repository.data, clone_method)
            console.log(f"[bold green]{repository.name}[/bold green]")

        status.update("[bold green]Cloning repositories...")
        for repository_name, clone_url in clone_urls.items():
            path = os.path.join(output, repository_name)
            status.update(f"[bold green]"
                          f"Cloning [bold yellow]{repository_name}[/bold yellow] "
                          f"to [bold yellow]{path}[/bold yellow]"
                          f"[/bold green]")
            Repo.clone_from(clone_url, path)


def _get_clone_url(repository, preferred_method=None):
    if 'links' not in repository:
        return None

    if 'clone' not in repository['links']:
        return None

    for method in repository['links']['clone']:
        if method['name'] == preferred_method:
            return method['href']

    return repository['links']['clone'][0]['href']


if __name__ == '__main__':
    typer.run(main)
