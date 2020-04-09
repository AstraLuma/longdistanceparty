"""
Events for asyncio

In order for your class to have an event, just use it like so:

class Spam:
    egged = Event("The spam has been egged")

To trigger an event, just call it like a method:
>>> Spam().egged(5)

All the positional and keyword arguments get passed to the handlers.

To register an event handler, use the .handler() decorator method:

   myspam = Spam()

   @myspam.egged.handler
   def gotegged(amount):
       print("I got egged: {}".format(amount))

It also works on the class level:
* Handlers registered on the class get called for every instance and
  (TODO) receives the instance as the first argument or None
* Triggering on a class only calls class-level handlers
"""
import asyncio
import traceback


__all__ = 'Event',


"""
About References

Just to document how references are managed:

The class strongly references the unbound Event.

Bound Events are kept in the __dict__ of the instance.

Bound events hold strong references registered callables.

A strong reference of a handler does not need to be kept by the application.

When an instance is freed, its keys in the bound events tables are freed, and
the bound events are collected. Registered handlers are unrefed and possibly
freed.

When a class is freed (all instances already collected), the unbound events are
collected. Again, handlers are left to fend for themselves.
"""


async def dump_traceback(func, *p, **kw):
    try:
        return await func(*p, **kw)
    except Exception:
        traceback.print_exc()


class BoundEvent(set):
    """
    A bound event. Also acts as the base for unbound events.

    Acts as a set for registered handlers.
    """
    def __init__(self, doc, parent=None):
        self.__doc__ = "Event: " + doc
        self._pman = parent

    def trigger(self, **args):
        """e.trigger(...) -> None
        Schedules the calling of all the registered handlers. Exceptions are
        consumed.

        Uses BaseEventLoop.call_soon_threadsafe() if the event loop is running,
        otherwise calls handlers directly.
        """
        if self._pman is not None:
            self._pman.trigger(**args)
        for handler in self:
            asyncio.create_task(dump_traceback(handler, **args))

    def __call__(self, *pargs, **kwargs):
        """
        Syntactic sugar for trigger()
        """
        self.trigger(*pargs, **kwargs)

    def handler(self, callable):
        """
        Registers a handler
        """
        self.add(callable)
        return callable


class Event(BoundEvent):
    _name = None

    def __init__(self, doc):
        super().__init__(doc)

    def __repr__(self):
        return f"<{type(self).__name__} name={self._name} handlers={set.__repr__(self)}>"

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        elif self._name not in vars(obj):
            vars(obj)[self._name] = BoundEvent(self.__doc__, self)
        return vars(obj)[self._name]

    def __set__(self, obj, value):
        # This is so that this appears as a data descriptor.
        raise AttributeError("Can't set an event")

    def __set_name__(self, owner, name):
        self._name = name
