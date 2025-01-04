=============
API Reference
=============

Component
---------

.. autoclass:: ahttp_client.component.Component()
   :members:
   :member-order: groupwise

Request Core
------------

.. autoclass:: ahttp_client.request.RequestCore()
   :members:
   :member-order: groupwise
   :exclude-members: before_hook, after_hook

   .. py:decorator:: before_hook

        A decorator that registers a coroutine as a pre-invoke hook. 
        A pre-invoke hook is called directly before the HTTP request is called. 
        This makes it a useful function to set up authorizations or any type of set up required.

   .. py:decorator:: after_hook

        A decorator that registers a coroutine as a post-invoke hook. 
        A post-invoke hook is called directly after the returned HTTP response. 
        This makes it a useful function to check correct response or any type of clean up response data.

Session
-------

.. autoclass:: ahttp_client.session.Session()
   :members:
   :member-order: groupwise
   :exclude-members: single_session

   .. py:decorator:: single_session(base_url: str, loop: Optional[asyncio.AbstractEventLoop], **session_kwargs)
        
        A single session for one request.

        :param str base_url: base url of the API.
        :param asynico.AbstractEventLoop loop: event loop used for processing HTTP requests.
        :param  session_kwargs: Keyword argument used in `aiohttp.ClientSession`
