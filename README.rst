pydisc
======

A simple API wrapper for Discord, prepared for async contexts.

.. warning::

    This library is currently at a planning state. Expect many errors or bugs, please create Issues
    so the mantainers can fix them as fast as possible!


Key Features
-------------

- Modern Pythonic API using ``async`` and ``await``.
- Proper rate limit handling.

Installing
----------

**Python 3.12 or higher is required**

.. note::

    A `Virtual Environment <https://docs.python.org/3/library/venv.html>`__ is recommended to install
    the library, especially on Linux where the system Python is externally managed and restricts which
    packages you can install on it.


.. code:: sh

    # Linux/macOS
    python3 -m pip install git+https://github.com/DA-344/pydisc

    # Windows
    py -3 -m pip install git+https://github.com/DA-344/pydisc

Quick Example
--------------

.. code:: py
    import pydisc

    intents = pydisc.Intents.default() | pydisc.Intents.message_content
    client = pydisc.Client(intents=intents)

    @clients.events.listener("ready")
    async def on_ready(event: pydisc.ReadyEvent) -> None:
        print(f"Connected as {event.user.name}")

    @client.command(name="ping")
    async def ping(interaction: pydisc.CommandInteraction) -> None:
        """Sends pong!"""
        await interaction.response.send_message(content="Pong!")

    client.run("token")


You can find more examples in the examples directory.
