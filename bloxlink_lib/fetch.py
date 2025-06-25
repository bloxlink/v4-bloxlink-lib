import asyncio
import logging
from http import HTTPStatus
from typing import Literal, Type, Union, Tuple, Any, Final
from requests.utils import requote_uri
from aiohttp_retry import RetryClient, ExponentialRetry
import aiohttp
from pydantic_core import to_json
from bloxlink_lib.models.base import BaseModel, BaseResponse
from bloxlink_lib.utils import parse_into

from .exceptions import RobloxAPIError, RobloxDown, RobloxNotFound
from .config import CONFIG

__all__ = ("fetch", "fetch_typed")

MAX_HTTP_RETRIES: Final[int] = 3


def _bytes_to_str_wrapper(data: Any) -> str:
    return to_json(data).decode("utf-8")


async def fetch[T](
    method: str,
    url: str,
    *,
    params: dict[str, str] = None,
    headers: dict = None,
    body: dict = None,
    parse_as: Literal["JSON", "BYTES", "TEXT"] | BaseModel | Type[T] = "JSON",
    raise_on_failure: bool = True,
    timeout: float = 30,
) -> Union[
    Tuple[dict, aiohttp.ClientResponse],
    Tuple[str, aiohttp.ClientResponse],
    Tuple[bytes, aiohttp.ClientResponse],
    Tuple[T, aiohttp.ClientResponse],
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

    params = params or {}
    headers = headers or {}

    url = requote_uri(url)

    for k, v in dict(params).items():
        if isinstance(v, bool):
            params[k] = "true" if v else "false"
        elif v is None:
            del params[k]

    if CONFIG.BOT_API and url.startswith(CONFIG.BOT_API):
        headers["Authorization"] = f"Bearer {CONFIG.BOT_API_AUTH}"

    session = aiohttp.ClientSession(json_serialize=_bytes_to_str_wrapper)
    retry_options = ExponentialRetry(attempts=MAX_HTTP_RETRIES)
    retry_client = RetryClient(
        client_session=session, raise_for_status=False, retry_options=retry_options
    )

    try:
        async with retry_client.request(
            method,
            url,
            json=body,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout) if timeout else None,
            proxy=(
                CONFIG.PROXY_URL if CONFIG.PROXY_URL and "roblox.com" in url else None
            ),
        ) as response:
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
                    raise RobloxNotFound(
                        "An unexpected error occurred while fetching data. 1"
                    )

                logging.warning(
                    f"{url} failed with status {response.status} and body {await response.text()}; proxy: {CONFIG.PROXY_URL}, using proxy: {CONFIG.PROXY_URL and 'roblox.com' in url}",
                )
                raise RobloxAPIError(
                    "An unexpected error occurred while fetching data. 2"
                )

            if parse_as == "TEXT":
                return await response.text(), response

            if parse_as == "JSON":
                try:
                    json_response = await response.json()
                except aiohttp.client_exceptions.ContentTypeError as exc:
                    logging.debug(f"{url} {await response.text()}")

                    raise RobloxAPIError(
                        "An unexpected error occurred while fetching data. 3"
                    ) from exc

                return json_response, response

            if parse_as == "BYTES":
                return await response.read(), response

            return parse_into(await response.json(), parse_as), response

    except asyncio.TimeoutError:
        logging.warning(f"URL {url} timed out")

        raise RobloxDown(
            "An unexpected error occurred while fetching data. 4"
        ) from None
    except aiohttp.client_exceptions.ClientConnectorError:
        logging.warning(f"URL {url} failed to connect")

        raise RobloxDown(
            "An unexpected error occurred while fetching data. 5"
        ) from None

    finally:
        await retry_client.close()


async def fetch_typed[T](
    parse_as: Type[T], url: str, method="GET", **kwargs
) -> Tuple[T, aiohttp.ClientResponse]:
    """Fetch data from a URL and parse it as a dataclass.

    Args:
        url (str): The URL to send the request to.
        parse_as (Type[T]): The dataclass to parse the response as.

    Returns:
        T: The dataclass instance of the response.
    """

    if CONFIG.BOT_API and url.startswith(CONFIG.BOT_API):
        fetch_body, fetch_headers = await fetch(
            url=url, parse_as=BaseResponse, method=method, **kwargs
        )

        return parse_into(fetch_body.data, parse_as), fetch_headers

    fetch_body, fetch_headers = await fetch(
        url=url, parse_as=parse_as, method=method, **kwargs
    )

    return fetch_body, fetch_headers
