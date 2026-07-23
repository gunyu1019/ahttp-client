=============
Serialization
=============
A request body or a response can be converted to and from a model class using `@serialize` and `@deserialize`.
`ahttp_client` ships with codecs for `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ (no extra dependency), `pydantic <https://docs.pydantic.dev/latest/>`_, and `marshmallow <https://marshmallow.readthedocs.io/>`_.

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

`@deserialize` inspects the method's return annotation (`list[Station]`) to select a registered deserializer for `Station`, then reads it from the response through :attr:`Response.model <ahttp_client.response.Response.model>`.
Combined with `directly_response=True`, the method body itself is never executed; the decorated method directly returns the deserialized model instead.

`@serialize` works the same way in the opposite direction, selecting a serializer from the parameter annotated as the complete request `Body` (see :doc:`component`) instead of the return annotation.

Selecting a Model Type
-----------------------
`model` can be passed explicitly, such as `@serialize(CreateUser)` or `@deserialize(Station)`, when the model type cannot be inferred from an annotation.
Any keyword arguments besides `model` are forwarded to the underlying serializer or deserializer once the model type is resolved (this is the "late-bind" mechanism: :meth:`~ahttp_client.serialization.base.BaseCodec.late_bind` stores the options, and :meth:`~ahttp_client.serialization.base.BaseSerializer.set_model`/:meth:`~ahttp_client.serialization.base.BaseDeserializer.set_model` resolve them once the annotated type is known).

Built-in Codecs
---------------

dataclasses
~~~~~~~~~~~
No extra dependency is required. Any `@dataclasses.dataclass`-decorated class, including nested dataclasses, lists, and common field types (`datetime`, `UUID`, `Decimal`, `Enum`), is supported automatically.

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

Any `pydantic.BaseModel` subclass is supported; serializer/deserializer keyword arguments (`by_alias`, `exclude_none`, `strict`, ...) map directly to `pydantic.BaseModel.model_dump`/`TypeAdapter.validate_python`, see :class:`~ahttp_client.serialization._types.PydanticSerializeOptions` and :class:`~ahttp_client.serialization._types.PydanticDeserializeOptions`.

marshmallow
~~~~~~~~~~~
.. note:: `marshmallow` package is required.

    .. code-block:: bash

        pip install marshmallow

Unlike the dataclasses and pydantic codecs, a `marshmallow.Schema` **instance** must always be passed explicitly as the `schema` keyword argument, since a schema is not itself the data's Python type.
Because of this, pass the schema *class* explicitly as `model` too, rather than relying on inference from the `Body`/return annotation (a plain `dict`, unlike a dataclass or pydantic model, is not enough on its own to identify which schema to use):

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
