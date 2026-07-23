=============
Serialization
=============
`@serialize` and `@deserialize` convert a request body or a response to and from a model class.
`ahttp_client` ships codecs for `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ (no extra dependency), `pydantic <https://docs.pydantic.dev/latest/>`_, and `marshmallow <https://marshmallow.readthedocs.io/>`_ out of the box.

.. code-block:: python
    :linenos:
    :caption: Deserializing a Response into a Pydantic Model

    from typing import Annotated

    import aiohttp
    from pydantic import BaseModel, ConfigDict
    from pydantic.alias_generators import to_camel

    from ahttp_client import AsyncSession, Query, get
    from ahttp_client.serializer import deserialize


    class Station(BaseModel):
        id: str
        name: str
        model_config = ConfigDict(alias_generator=to_camel)


    class MetroAPI(AsyncSession):
        def __init__(self) -> None:
            super().__init__("https://api.yhs.kr", aiohttp.ClientSession)

        @get("/metro/station", directly_response=True)
        @deserialize(by_alias=True)
        async def search_stations(
            self, name: Annotated[str, Query]
        ) -> list[Station]:
            raise AssertionError("direct deserialization skips the method body")

`@deserialize` looks at the method's return annotation (`list[Station]`), picks the deserializer registered for `Station`, then reads it off the response through :attr:`Response.model <ahttp_client.response.Response.model>`.
Pair it with `directly_response=True` and the method body never runs at all — the decorated method just hands back the deserialized model.

`@serialize` mirrors this in the other direction: instead of the return annotation, it picks its serializer from whichever parameter is annotated as the complete request `Body` (see :doc:`component`).

Selecting a Model Type
-----------------------
When the model type cannot be inferred from an annotation, pass it explicitly, such as `@serialize(CreateUser)` or `@deserialize(Station)`.
Any other keyword arguments get forwarded to the serializer or deserializer once the model type is known — this is the "late-bind" mechanism at work: :meth:`~ahttp_client.serialization.base.BaseCodec.late_bind` holds onto the options until :meth:`~ahttp_client.serialization.base.BaseSerializer.set_model`/:meth:`~ahttp_client.serialization.base.BaseDeserializer.set_model` can resolve them against the actual annotated type.

Built-in Codecs
---------------

dataclasses
~~~~~~~~~~~
No extra dependency is required. Any `@dataclasses.dataclass`-decorated class is supported automatically, including nested dataclasses, lists, and common field types such as `datetime`, `UUID`, `Decimal`, and `Enum`.

.. code-block:: python

    from dataclasses import dataclass
    from typing import Annotated

    from ahttp_client import AsyncSession, Body, Response, post
    from ahttp_client.serializer import serialize, deserialize


    @dataclass
    class CreateUser:
        name: str
        age: int


    class UserAPI(AsyncSession):
        @post("/users")
        @serialize()
        @deserialize()
        async def create_user(
            self, response: Response, user: Annotated[CreateUser, Body]
        ) -> CreateUser:
            return response.model

pydantic
~~~~~~~~
.. note:: `pydantic` package is required.

    .. code-block:: bash

        pip install pydantic

Any `pydantic.BaseModel` subclass is supported. The serializer/deserializer keyword arguments (`by_alias`, `exclude_none`, `strict`, ...) map directly onto `pydantic.BaseModel.model_dump`/`TypeAdapter.validate_python`; see :class:`~ahttp_client.serialization._types.PydanticSerializeOptions` and :class:`~ahttp_client.serialization._types.PydanticDeserializeOptions` for the full list.

marshmallow
~~~~~~~~~~~
.. note:: `marshmallow` package is required.

    .. code-block:: bash

        pip install marshmallow

A `marshmallow.Schema` **instance** always has to be passed explicitly as the `schema` keyword argument here — unlike the dataclasses and pydantic codecs, a schema isn't itself the data's Python type, so there's nothing for `ahttp_client` to infer it from.
For the same reason, pass the schema *class* explicitly as `model` too, rather than counting on inference from the `Body`/return annotation: a plain `dict` doesn't tell `ahttp_client` which schema to use, the way a dataclass or pydantic model would.

.. code-block:: python

    from typing import Annotated

    from marshmallow import Schema, fields

    from ahttp_client import AsyncSession, Body, Response, post
    from ahttp_client.serializer import serialize, deserialize


    class UserSchema(Schema):
        name = fields.Str()
        age = fields.Int()


    class UserAPI(AsyncSession):
        @post("/users")
        @serialize(model=UserSchema, schema=UserSchema())
        @deserialize(model=UserSchema, schema=UserSchema())
        async def create_user(
            self, response: Response, user: Annotated[dict, Body]
        ) -> dict:
            return response.model

Reference
---------

.. autoclass:: ahttp_client.serialization.base.BaseCodec()
    :members:

.. autoclass:: ahttp_client.serialization.base.BaseSerializer()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.serialization.base.BaseDeserializer()
    :members:
    :show-inheritance:

.. autofunction:: ahttp_client.serializer.serialize

.. autofunction:: ahttp_client.serializer.deserialize
