==============
HTTP Component
==============
A component used in `ahttp_client` are Query, Header, Path, and Body.
In the HTTP request process in `ahttp_client`, a component defines as `typing.Annotated <https://docs.python.org/ko/3.10/library/typing.html#typing.Annotated>`_.

When a `list_repository_activites` method is called, the request is called as shown below.

.. code-block:: python
    :linenos:
    :emphasize-lines: 19, 20

    @Session.single_session("https://api.github.com/")
    @request("GET", "/repos/{owner}/{repo}/activity")
    def list_repository_activites(
        session, 
        owner: Annotated[str, Path],
        repo: Annotated[str, Path],
        activity_type: Annotated[str, Query],
        authorization: Annotated[str, Header]
    ) -> dict[str, Any]:
        return await response.json()

    await list_repository_activites(
        owner="gunyu1019",
        repo="ahttp_client",
        activity_type="push",
        authorization="Bearer <GITHUB TOKEN>"
    )

    # curl https://api.github.com/repos/gunyu1019/ahttp_client/activity?activity_type=push \
    #    -H "authorization: Bearer <GITHUB TOKEN>"

.. note:: An HTTP Component can be defined as `typing.Union <https://docs.python.org/ko/3.10/library/typing.html#typing.Union>`_ instead of `typing.Annotated <https://docs.python.org/ko/3.10/library/typing.html#typing.Annotated>`_.
    
    .. code-block:: python

        @Session.single_session("https://api.github.com/")
        @request("GET", "/repos/{owner}/{repo}/activity")
        def list_repository_activites(
            session, 
            owner:str | Path,
            repo: str | Path,
            activity_type: str | Query,
            authorization: str | Header  # or, authorization: typing.Union[str, Header]
        ) -> dict[str, Any]:
            return await response.json()

    However, using typing.Annotated is recommended to follow correct Python syntax.

Usage by Component
------------------

* **Header** - Configure the header for the HTTP component.
* **Body** - Configure the body for the HTTP component.
* **Form** - Configure the body with `aiohttp.FormData <https://docs.aiohttp.org/en/v3.8.0/client_reference.html#aiohttp.FormData>`_
* **BodyJson** - Configure the body with `Dictionaries <https://docs.python.org/3/tutorial/datastructures.html#dictionaries>`_
* **Query** - Insert a value inside the URL parameter.
* **Path** - Insert the specified value(s) inside the path placeholder. The path placeholder is using curly brackets: `{}`

.. warning:: Defining the Body parameter at HTTP request decoration can only be of one of the following types: Body, BodyJson, or Form.
    If more than one Component is used, a `TypeError <https://docs.python.org/3/library/exceptions.html#TypeError>`_ can be thrown.

Custom Component Name
---------------------
According to PEP 8 rules, the parameter names of method must be lowercase, with words separated by underscores. `(reference) <https://peps.python.org/pep-0008/#function-and-variable-names>`_

The queries or headers in an API can be named in Camel Case, or Pascal Case.

To follow the PEP 8 rules as described, an `ahttp_client` package provides a custom component name.

.. code-block:: python
    :linenos:
    :emphasize-lines: 19, 20

    @Session.single_session("https://api.github.com/")
    @request("GET", "/repos/{owner}/{repo}/activity")
    def list_repository_activites(
        session, 
        owner: Annotated[str, Path],
        repo: Annotated[str, Path],
        activity_type: Annotated[str, Query],
        token: Annotated[str, Header.custom_name("Authorization")]
    ) -> dict[str, Any]:
        return await response.json()

    await list_repository_activites(
        owner="gunyu1019",
        repo="ahttp_client",
        activity_type="push",
        token="Bearer <GITHUB TOKEN>"
    )

    # curl https://api.github.com/repos/gunyu1019/ahttp_client/activity?activity_type=push \
    #    -H "Authorization: Bearer <GITHUB TOKEN>"

As in the example above, insert the `GITHUB API TOKEN` in token argument of `list_repository_activites` method.
During the calling process, the key of Header has been overridden to "Authorization".

.. warning:: The custom component name feature only supports Header, Query, BodyJson, and Form. 
    Using it in other components may cause a `TypeError <https://docs.python.org/3/library/exceptions.html#TypeError>`_.