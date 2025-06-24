import asyncio
import logging
from http import HTTPStatus
from typing import (
    Literal,
    Type,
    Union,
    Tuple,
    Any,
    TypedDict,
    Unpack,
    Required,
    NotRequired,
)
from requests.utils import requote_uri
import aiohttp
from pydantic_core import to_json
from bloxlink_lib.models.base import BaseModel
from bloxlink_lib.utils import parse_into

from .exceptions import RobloxAPIError, RobloxDown, RobloxNotFound
from .config import CONFIG

__all__ = ("fetch", "fetch_typed")


def _bytes_to_str_wrapper(data: Any) -> str:
    return to_json(data).decode("utf-8")


class FetchRequestArgs(TypedDict):
    method: Required[str]
    url: Required[str]
    params: NotRequired[dict[str, str]]
    headers: NotRequired[dict]
    body: NotRequired[dict]
    parse_as: NotRequired[Literal["JSON", "BYTES", "TEXT"] | BaseModel | None]
    raise_on_failure: NotRequired[bool]
    timeout: NotRequired[float]
    retries: NotRequired[int]


async def _parse_response[T](
    response: aiohttp.ClientResponse,
    url: str,
    raise_on_failure: bool,
    parse_as: Literal["JSON", "BYTES", "TEXT"] | BaseModel | None = "JSON",
) -> tuple[T | None, aiohttp.ClientResponse]:
    if response.status != HTTPStatus.OK and raise_on_failure:
        if response.status == HTTPStatus.SERVICE_UNAVAILABLE:
            logging.warning(f"{url} is down: {await response.text()}")
            raise RobloxDown("Roblox is down. Please try again later.")

        # Roblox APIs sometimes use 400 as not found
        if response.status in (
            HTTPStatus.BAD_REQUEST,
            HTTPStatus.NOT_FOUND,
        ):
            logging.debug(f"{url} not found: {await response.text()}")
            raise RobloxNotFound("An unexpected error occurred while fetching data. 1")

        logging.warning(
            f"{url} failed with status {response.status} and body {await response.text()}; proxy: {CONFIG.PROXY_URL}, using proxy: {CONFIG.PROXY_URL and 'roblox.com' in url}",
        )
        raise RobloxAPIError("An unexpected error occurred while fetching data. 2")

    if not parse_as:
        return None, response

    match parse_as:
        case "TEXT":
            return await response.text(), response
        case "JSON":
            try:
                json_response = await response.json()
            except aiohttp.client_exceptions.ContentTypeError as exc:
                logging.debug(f"{url} {await response.text()}")

                raise RobloxAPIError(
                    "An unexpected error occurred while fetching data. 3"
                ) from exc

            return json_response, response

        case "BYTES":
            return await response.read(), response

        case _:
            return (
                parse_into(await response.json(), parse_as),
                response,
            )


async def _do_request[T](
    **fetch_args: Unpack[FetchRequestArgs],
) -> tuple[T | None, aiohttp.ClientResponse]:
    try:
        async with aiohttp.ClientSession(
            json_serialize=_bytes_to_str_wrapper
        ) as session:
            async with session.request(
                fetch_args["method"],
                fetch_args["url"],
                json=fetch_args["body"],
                params=fetch_args["params"],
                headers=fetch_args["headers"],
                timeout=(
                    aiohttp.ClientTimeout(total=fetch_args["timeout"])
                    if fetch_args["timeout"]
                    else None
                ),
                proxy=(
                    CONFIG.PROXY_URL
                    if CONFIG.PROXY_URL and "roblox.com" in fetch_args["url"]
                    else None
                ),
            ) as response:
                return await _parse_response(
                    response,
                    fetch_args["url"],
                    fetch_args["raise_on_failure"],
                    fetch_args["parse_as"],
                )

    except asyncio.TimeoutError:
        logging.warning(f"URL {fetch_args['url']} timed out")

        raise RobloxDown(
            "An unexpected error occurred while fetching data. 4"
        ) from None

    except aiohttp.client_exceptions.ClientConnectorError:
        logging.warning(f"URL {fetch_args['url']} failed to connect")

        raise RobloxDown(
            "An unexpected error occurred while fetching data. 5"
        ) from None


async def fetch[T](
    **fetch_args: Unpack[FetchRequestArgs],
) -> Union[
    Tuple[dict, aiohttp.ClientResponse],
    Tuple[str, aiohttp.ClientResponse],
    Tuple[bytes, aiohttp.ClientResponse],
    Tuple[T, aiohttp.ClientResponse],
    aiohttp.ClientResponse,
]:
    """Make a REST request with the ability to proxy.

    Only Roblox URLs are proxied, all other requests to other domains are sent as is.

    Args:
        method (str): The HTTP request method to use for this query.
        url (str): The URL to send the request to.
        params (dict, optional): Query parameters to append to the URL. Defaults to None.
        headers (dict, optional): Headers to use when sending the request. Defaults to None.
        body (dict, optional): Data to pass in the body of the request. Defaults to None.
        parse_as (JSON | BYTES | TEXT | Type[T], optional): Set what the expected type to return should be.
            Defaults to JSON.
        raise_on_failure (bool, optional): Whether an exception be raised if the request fails. Defaults to True.
        timeout (float, optional): How long should we wait for a request to succeed. Defaults to 10 seconds.

    Raises:
        RobloxAPIError:
            For proxied requests, raised when the proxy server returns a data format that is not JSON.
            When a request returns a status code that is NOT 503 or 404, but is over 400 (if raise_on_failure).
            When a non-proxied request does not match the expected data type (typically JSON).
        RobloxDown: Raised if raise_on_failure, and the status code is 503. Also raised on request timeout.
        RobloxNotFound: Raised if raise_on_failure, and the status code is 404.

    Returns:
        Tuple[dict, ClientResponse] | Tuple[str, ClientResponse] | Tuple[bytes, ClientResponse] | ClientResponse:
        The requested data from the request, if any.
    """

    fetch_args["url"] = requote_uri(fetch_args["url"])
    fetch_args["retries"] = fetch_args["retries"] or 3

    for k, v in dict(fetch_args["params"]).items():
        if isinstance(v, bool):
            fetch_args["params"][k] = "true" if v else "false"
        elif v is None:
            del fetch_args["params"][k]

    while fetch_args["retries"] > 0:
        try:
            response_body, response_headers = await _do_request(
                method=fetch_args["method"],
                url=fetch_args["url"],
                params=fetch_args["params"],
                headers=fetch_args["headers"],
                body=fetch_args["body"],
                parse_as=fetch_args["parse_as"],
                raise_on_failure=fetch_args["raise_on_failure"],
                timeout=fetch_args["timeout"],
            )

            if response_headers.status != HTTPStatus.OK:
                raise RobloxAPIError(
                    f"Retrying {fetch_args['url']} {fetch_args['method']} {fetch_args['retries']} times"
                )

            return response_body, response_headers

        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.warning(f"Error fetching {fetch_args['url']}: {e}")

            if fetch_args["retries"] == 0:
                raise e

            fetch_args["retries"] -= 1

            await asyncio.sleep(1)


async def fetch_typed[T](
    parse_as: Type[T],
    url: str,
    method="GET",
    **kwargs: Unpack[FetchRequestArgs],
) -> Tuple[T, aiohttp.ClientResponse]:
    """Fetch data from a URL and parse it as a dataclass.

    Args:
        url (str): The URL to send the request to.
        parse_as (Type[T]): The dataclass to parse the response as.

    Returns:
        T: The dataclass instance of the response.
    """

    return await fetch(
        url=url,
        parse_as=parse_as,
        method=method,
        **kwargs,
    )
