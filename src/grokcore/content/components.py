##############################################################################
#
# Copyright (c) 2006-2007 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Base content components for Grok.
"""
import persistent

from grokcore.content import interfaces
from persistent.list import PersistentList
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.container.btree import BTreeContainer
from zope.container.contained import Contained, notifyContainerModified
from zope.interface import implements


class Model(Contained, persistent.Persistent):
    # XXX Inheritance order is important here. If we reverse this,
    # then containers can't be models anymore because no unambigous MRO
    # can be established.
    """The base class for models in Grok applications.

    When an application class inherits from `grok.Model`, it gains the
    ability to persist itself in the Zope object database along with all
    of its attributes, and to remember the container in which it has
    been placed (its "parent") so that its URL can be computed.  It also
    inherits the `IContext` marker interface, which can make it the
    default context for views in its module; the rule is that if a
    module contains `grok.View` classes or other adapters that do not
    define a `grok.context()`, but the module also defines exactly one
    class that provides the `IContext` interface, then that class will
    automatically be made the `grok.context()` of each of the views.

    """
    implements(IAttributeAnnotatable, interfaces.IContext)


class Container(BTreeContainer):
    """The base class for containers in Grok applications.

    When an application class inherits from `grok.Container`, it not
    only has the features of a `grok.Model` (persistance, location, and
    the ability to serve as a default context for other classes), but it
    also behaves like a persistent dictionary.  To store items inside a
    container, simply use the standard Python getitem/setitem protocol::

        mycontainer['counter'] = 72
        mycontainer['address'] = mymodel
        mycontainer['subfolder'] = another_container

    By default, the URL of each item inside a container is the
    container's own URL followed by a slash and the key (like 'counter'
    or 'address') under which that item has been stored.

    """
    implements(IAttributeAnnotatable, interfaces.IContainer)


class OrderedContainer(Container):
    """A Grok container that remembers the order of its items.

    This straightforward extension of the basic `grok.Container`
    remembers the order in which items have been inserted, so that
    `keys()`, `values()`, `items()`, and iteration across the container
    can all return the items in the order they were inserted.  The only
    way of changing the order is to call the `updateOrder()` method.

    """
    implements(interfaces.IOrderedContainer)

    def __init__(self):
        super(OrderedContainer, self).__init__()
        self._order = PersistentList()

    def keys(self):
        # Return a copy of the list to prevent accidental modifications.
        return self._order[:]

    def __iter__(self):
        return iter(self.keys())

    def values(self):
        return (self[key] for key in self._order)

    def items(self):
        return ((key, self[key]) for key in self._order)

    def __setitem__(self, key, object):
        foo = self.has_key(key)
        # Then do whatever containers normally do.
        super(OrderedContainer, self).__setitem__(key, object)
        if not foo:
            self._order.append(key)

    def __delitem__(self, key):
        # First do whatever containers normally do.
        super(OrderedContainer, self).__delitem__(key)
        self._order.remove(key)

    def updateOrder(self, order):
        """Impose a new order on the items in this container.

        Items in this container are, by default, returned in the order
        in which they were inserted.  To change the order, provide an
        argument to this method that is a sequence containing every key
        already in the container, but in a new order.

        """
        if set(order) != set(self._order):
            raise ValueError("Incompatible key set.")

        self._order = PersistentList()
        self._order.extend(order)
        notifyContainerModified(self)
