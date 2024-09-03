import logging

import typer
from dotenv import load_dotenv
from pathlib import Path
from typing import TypedDict, Optional
from typing_extensions import Annotated

from proc_fluidontologies import sample_interactions

logger = logging.getLogger("train")

app = typer.Typer(
    help="Commands to train models",
    pretty_exceptions_show_locals=False,
)


class SharedOptions(TypedDict):
    items_file: Path | None
    entities_file: Path | None
    knowledge_graph_file: Path | None
    user_file: Path | None
    interactions_file: Path | None
    save_dir: Path


@app.callback()
def setup(
    ctx: typer.Context,
    items_file: Annotated[
        Optional[Path], typer.Option("--items_file", help="Path to the items file")
    ] = None,
    entities_file: Annotated[
        Optional[Path],
        typer.Option("--entities_file", help="Path to the entities file"),
    ] = None,
    kg_file: Annotated[
        Optional[Path],
        typer.Option(
            "--knowledge_graph_file", help="File containing the knowledge graph"
        ),
    ] = None,
    user_file: Annotated[
        Optional[Path], typer.Option("--user_file", help="File containing user IDs")
    ] = None,
    interactions_file: Annotated[
        Optional[Path],
        typer.Option(
            "--interactions_file", help="File containing interactions of real users"
        ),
    ] = None,
    save_dir: Annotated[
        Path, typer.Option("--save_dir", help="Save numpy objects to this directory.")
    ] = Path("."),
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            help="Increase verbosity; pass up to three times (-vvv)",
            count=True,
        ),
    ] = 0,
):
    """
    Training routines.
    """
    base_level = logging.ERROR
    verbosity = min(verbose, 2) * 10
    verbosity = base_level - verbosity
    # TODO: re-think logger format, logs should be greppable by some identifier
    logging.basicConfig(
        format="%(asctime)-15s %(name)-5s:%(funcName)-20s %(levelname)-8s %(message)s",
        level=verbosity,
    )

    save_dir.mkdir(parents=True, exist_ok=True)

    ctx.obj = SharedOptions(
        items_file=items_file,
        entities_file=entities_file,
        knowledge_graph_file=kg_file,
        user_file=user_file,
        interactions_file=interactions_file,
        save_dir=save_dir,
    )
    from pprint import pprint

    pprint(SharedOptions)


@app.command()
def interactions(
    ctx: typer.Context,
    n_profiles: Annotated[
        int, typer.Option("--n_profiles", help="Total number of profiles to sample")
    ] = 100,
    perc_within_range: Annotated[
        float,
        typer.Option(
            "--perc_within_range",
            help="""
Percentage of profiles to sample from network proximity of random items. If
--perc-within-range and --perc-along-path do not add up to 100%, the remainder
will be sampled randomly.
            """,
        ),
    ] = 50.0,
    perc_along_path: Annotated[
        float,
        typer.Option(
            "--perc_along_path",
            help="""
Percentage of profiles to sample from network paths of items. If
--perc-within-range and --perc-along-path do not add up to 100%, the remainder
will be sampled randomly.
""",
        ),
    ] = 50.0,
    n_interact_max: Annotated[
        int,
        typer.Option(
            "--n_interact_max", help="Minimum interactions per sampled profile."
        ),
    ] = 200,
    n_interact_min: Annotated[
        int,
        typer.Option(
            "--n_interact_min", help="Maximum interactions per sampled profile."
        ),
    ] = 30,
    n_interact_test_max: Annotated[
        int,
        typer.Option(
            "--n_interact_test_max",
            help="Maximum interactions per sampled profile that go to the test set",
        ),
    ] = 10,
):
    assert isinstance(ctx.obj, dict)
    shared_opts = ctx.obj

    from pprint import pprint

    args = {}
    args.update(shared_opts)
    pprint(args)
    args.update(ctx.params)

    pprint(args)

    from types import SimpleNamespace

    args = SimpleNamespace(**args)

    sample_interactions.main(args)


if __name__ == "__main__":
    # Sourcing from shell builtins doesn't expose variables to the environment,
    # so we do it explicitly here
    load_dotenv("/app/.env")
    app()
