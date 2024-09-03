import logging
import os
import subprocess
from pathlib import Path
from urllib.parse import urlencode

import requests
import typer
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from typing_extensions import Annotated

# TODO: re-think logger format, logs should be greppable by some identifier
logging.basicConfig(
    format="%(asctime)-15s %(name)-5s:%(funcName)-20s %(levelname)-8s %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("fetch")


def write_response(r: requests.Response, out: Path) -> bool:
    """
    Handle the API response.

    If the response is "200 OK", write the contents to the file specified in 'out'.
    If not, return an error.

    Parameters
    ----------
    r : requests.Response
        The API response
    out : pathlib.Path
        Full path to the file to write the successful response to.

    Returns
    -------
    bool
        Whether the response could be written to the file

    Side effects:
    -------------
    - creates the full path to the file given in 'out' if it does not exist
    - writes response to this file
    """
    if r.status_code != 200:
        logger.critical(f"Encountered non-200 status code: {r.text}")
        return False

    if not out.parents[0].exists():
        logger.info(f"Path {out} does not exist, creating it")
        out.parents[0].mkdir(parents=True)

    logger.info(f"Storing response in {out}")
    with open(out, "w") as f:
        f.write(r.text)

    return True


app = typer.Typer(
    help="Commands to fetch required exports from fo_services",
    pretty_exceptions_show_locals=False,
)


@app.command(help="Fetch users from the /db/export_users endpoint")
def users(
    user: Annotated[str, typer.Option(envvar="API_USER", help="API user")],
    password: Annotated[
        str, typer.Option(envvar="API_PASSWORD", help="API password", show_envvar=False)
    ],
    url: Annotated[str, typer.Option(envvar="API_URL", help="API url")],
    out_dir: Annotated[Path, typer.Option(help="Directory to write output to")],
    out_name: Annotated[Path, typer.Option(help="Output file name")] = Path(
        "user_ids.tsv"
    ),
):
    logger.info("Fetching users")
    auth = HTTPBasicAuth(user, password)
    r = requests.post(
        url + "/db/export_users",
        auth=auth,
        verify=False,
    )

    if not write_response(r, out_dir / out_name):
        raise typer.Abort(os.EX_DATAERR)

    logger.info("Done.")
    raise typer.Exit(os.EX_OK)


@app.command(help="Fetch interactions from the /db/export_interactions endpoint")
def interactions(
    user: Annotated[str, typer.Option(envvar="API_USER", help="API user")],
    password: Annotated[
        str, typer.Option(envvar="API_PASSWORD", help="API password", show_envvar=False)
    ],
    url: Annotated[str, typer.Option(envvar="API_URL", help="API url")],
    out_dir: Annotated[Path, typer.Option(help="Directory to write output to")],
    out_name: Annotated[Path, typer.Option(help="Output file name")] = Path(
        "user_interactions.tsv"
    ),
):
    logger.info("Fetching interactions")
    auth = HTTPBasicAuth(user, password)
    r = requests.post(
        url + "/db/export_interactions",
        auth=auth,
        verify=False,
    )

    if not write_response(r, out_dir / out_name):
        raise typer.Abort(os.EX_DATAERR)

    logger.info("Done")
    raise typer.Exit(os.EX_OK)


@app.command(help="Fetch triples from GraphDB")
def statements(
    user: Annotated[str, typer.Option(envvar="GRAPHDB_USER", help="GraphDB user")],
    password: Annotated[
        str,
        typer.Option(
            envvar="GRAPHDB_PASSWORD", help="GraphDB password", show_envvar=False
        ),
    ],
    graphdb_url: Annotated[
        str, typer.Option(envvar="GRAPHDB_URL", help="URL to GraphDB")
    ],
    repository: Annotated[str, typer.Option(help="Name of the repository")],
    out_dir: Annotated[Path, typer.Option(help="Directory to write output to")],
    out_name: Annotated[Path, typer.Option(help="Output file name")] = Path(
        "statements.nt"
    ),
):
    auth = HTTPBasicAuth(user, password)

    # https://graphdb.ontotext.com/documentation/10.7/exporting-data.html#exporting-via-http-with-curl
    # https://sparqlwrapper.readthedocs.io/en/latest/main.html#graphdb
    headers = {
        "Accept": "application/n-triples",
    }

    logger.info("Fetching statements")
    r = requests.get(
        f"{graphdb_url}/repositories/{repository}/statements",
        headers=headers,
        auth=auth,
    )

    if not write_response(r, out_dir / out_name):
        raise typer.Abort(os.EX_DATAERR)

    logger.info("Done")
    raise typer.Exit(os.EX_OK)


@app.command()
def itemlist(
    user: Annotated[str, typer.Option(envvar="GRAPHDB_USER", help="GraphDB user")],
    password: Annotated[
        str,
        typer.Option(
            envvar="GRAPHDB_PASSWORD", help="GraphDB password", show_envvar=False
        ),
    ],
    graphdb_url: Annotated[
        str, typer.Option(envvar="GRAPHDB_URL", help="URL to GraphDB")
    ],
    repository: Annotated[str, typer.Option(help="Name of the repository")],
    out_dir: Annotated[Path, typer.Option(help="Directory to write output to")],
    out_name: Annotated[Path, typer.Option(help="Output file name")] = Path(
        "itemlist.nt"
    ),
):
    auth = HTTPBasicAuth(user, password)

    # https://graphdb.ontotext.com/documentation/10.7/exporting-data.html#exporting-via-http-with-curl
    # https://sparqlwrapper.readthedocs.io/en/latest/main.html#graphdb
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    sparql = """
PREFIX am: <http://www.wisski.uni-bayreuth.de/ontologies/africamultiple/240307/>
PREFIX amdata: <http://www.wisski.uni-bayreuth.de/data/>
PREFIX ecrm: <http://erlangen-crm.org/240307/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?entities WHERE {
    ?entities owl:sameAs ?ic .
    ?ic rdf:type am:information_carrier .
}
"""

    payload = {
        "query": sparql,
    }

    logger.info("Fetching itemlist")
    r = requests.post(
        f"{graphdb_url}/repositories/{repository}",
        data=urlencode(payload),
        headers=headers,
        auth=auth,
    )

    if not write_response(r, out_dir / out_name):
        raise typer.Abort(os.EX_DATAERR)

    logger.info("Done")
    raise typer.Exit(os.EX_OK)


# TODO: this should go in another module, fetch is the wrong place.
@app.command()
def process(
    res_dir: Annotated[Path, typer.Option(help="Directory containing helper scripts")],
    dumps_dir: Annotated[Path, typer.Option(help="Directory containing data dumps")],
    out_dir: Annotated[Path, typer.Option(help="Directory to write output to")],
    out_name: Annotated[Path, typer.Option(help="Output file name")] = Path(
        "kg_final.txt"
    ),
):

    logger.info("Processing data")
    awk_cmd = [
        "awk",
        "-v",
        "OFS= ",
        "-v",
        f"outdir={out_dir}",
        "-v",
        "min_degree_in=1",
        "-v",
        "min_degree_out=1",
        "-f",
        f"{res_dir}/nt_to_knowledge_graph.awk",
        f"{res_dir}/filter_predicates",
        f"{res_dir}/filter_relations",
        f"{dumps_dir}/statements.nt",
        f"{dumps_dir}/itemlist.nt",
        f"{dumps_dir}/statements.nt",
    ]

    res = subprocess.run(awk_cmd, capture_output=True, text=True)
    if res.returncode != os.EX_OK:
        logger.critical(
            f"AWK subprocess returned with error code {res.returncode}: {res.stderr}"
        )
        raise typer.Abort()

    with open(out_dir / out_name, "w") as f:
        f.write(res.stdout)
        logger.info(f"Wrote results to {out_dir/out_name}")

    raise typer.Exit(os.EX_OK)


if __name__ == "__main__":
    # Sourcing from shell builtins doesn't expose variables to the environment,
    # so we do it explicitly here
    load_dotenv("/app/.env")
    app()
