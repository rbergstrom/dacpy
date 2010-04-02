# The MIT License
#
# Copyright (c) 2010 Ryan Bergstrom
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import struct
import time

from datetime import datetime

import tags

__all__ = [
    'UByte', 'Byte','UShort', 'Short', 'UInt', 'Int', 'ULong', 'Long',
    'Binary', 'Container', 'DateTime', 'MultiInt', 'MultiUInt', 'Node',
    'String', 'Version',

    'UnknownTagError',

    'build_node'
]

class UnknownTagError(ValueError):
    pass

class DAAPType(object):
    """Abstract class to provide utility methods for all DAAP value types."""

    value = None
    length = 0

    def __eq__(self, other):
        try:
            return self.value == other.value
        except AttributeError:
            return self.value == other

    def __ne__(self, other):
        return not self == other

    def __len__(self):
        return self.length

    def __unicode__(self):
        return unicode(self.value)

    def __str__(self):
        return str(unicode(self))

    def pprint(self):
        return unicode(self.value)

class NumericType(type):
    """Metaclass to calculate attributes for a fixed-length numeric type."""
    _format_codes = {
        1: { False: 'B', True: 'b'},
        2: { False: 'H', True: 'h'},
        4: { False: 'L', True: 'l'},
        8: { False: 'Q', True: 'q'},
    }

    def __new__(cls, name, bases, attrs):
        signed = attrs.pop('signed', False)
        length = attrs.get('length', 4)

        if signed == True:
            attrs['min_value'] = - 1 * (1 << (length * 8 - 1))
            attrs['max_value'] = (1 << (length * 8 - 1)) - 1
        else:
            attrs['min_value'] = 0
            attrs['max_value'] = (1 << length * 8) - 1

        attrs['format_code'] = cls._format_codes[length][signed]

        return super(NumericType, cls).__new__(cls, name, bases, attrs)

class Numeric(DAAPType):
    """Abstract numeric value type to provide common utility methods."""

    __metaclass__ = NumericType

    def __init__(self, value):
        try:
            self.value = int(value)
        except Exception:
            raise TypeError('%s requires a numeric value' % self.__class__.__name__)
        if self.value < self.min_value or self.value > self.max_value:
            raise ValueError('%s requires %d <= value <= %d' % (
                self.__class__.__name__, self.min_value, self.max_value
            ))

    def __int__(self):
        return self.value

    def __eq__(self, other):
        try:
            return (self.value == other.value) and (len(self) == len(other))
        except AttributeError:
            return self.value == other

    def serialize(self):
        """Returns a big-endian bytestring representation of the value."""
        return struct.pack('>%s' % self.format_code, self.value)

    @classmethod
    def deserialize(cls, bytes):
        """Creates a numeric type object from a big-endian bytestring."""
        return cls(struct.unpack_from('>%s' % cls.format_code, bytes)[0])

    def pprint(self):
        hexval = struct.unpack('>%s' % self.format_code.upper(), self.serialize())[0]
        return ('0x%%0%dX == %%d' % (2*self.length)) % (hexval, self.value)

class UByte(Numeric):
    """8-bit unsigned integer type."""
    length = 1
    signed = False

class Byte(Numeric):
    """8-bit signed integer type."""
    length = 1
    signed = True

class UShort(Numeric):
    """16-bit unsigned integer type."""
    length = 2
    signed = False

class Short(Numeric):
    """16-bit signed integer type."""
    length = 2
    signed = True

class UInt(Numeric):
    """32-bit unsigned integer type."""
    length = 4
    signed = False

class Int(Numeric):
    """32-bit signed integer type."""
    length = 4
    signed = True

class ULong(Numeric):
    """64-bit unsigned integer type."""
    length = 8
    signed = False

class Long(Numeric):
    """64-bit signed integer type."""
    length = 8
    signed = True

class MultiNumeric(DAAPType):
    """
    Special numeric type containing several numeric values of the same base
    type. Represented in Python as a tuple of either numeric literals or other
    numeric types, all of which will be converted to the specified base type.
    
    Serialized as a series of concatenated numeric values.
    """
    _base_type = None

    def __init__(self, value):
        self.value = tuple([self._base_type(x) for x in value])
        self.length = len(value) * self._base_type.length

    def serialize(self):
        return ''.join([x.serialize() for x in self.value])

    @classmethod
    def deserialize(cls, bytes):
        format = '>%d%s' % (len(bytes) / cls._base_type.length, cls._base_type.format_code)
        values = struct.unpack_from(format, bytes)
        return cls(values)

    def pprint(self):
        return u'(%s)' % (', '.join([x.pprint() for x in self.value]))


class MultiInt(MultiNumeric):
    """
    Multiple signed 32-bit integers (see MultiNumeric).
    
    Example:
        MultiInt((-1, 1)) = '\xff\xff\xff\xff\x00\x00\x00\x01'
    """

    _base_type = Int

class MultiUInt(MultiNumeric):
    """
    Multiple unsigned 32-bit integers (see MultiNumeric).
    
    Example:
        MultiUInt((0, 4294967295)) = '\x00\x00\x00\x01\xff\xff\xff\xff'
    """

    _base_type = UInt

class DateTime(DAAPType):
    """Datetime type serialized to a standard UNIX timestamp."""

    def __init__(self, value):
        self.value = value
        self.length = 4

    def serialize(self):
        if self.value is None:
            return '\xff\xff\x9d\x90'
        else:
            return struct.pack('>l', int(time.mktime(self.value.timetuple())))

    @classmethod
    def deserialize(cls, bytes):
        val = struct.unpack_from('>l', bytes)[0]
        return cls(datetime.fromtimestamp(val))

class Version(DAAPType):
    """
    Dotted quad version number, represented by a 4-tuple.
    
    Serialized as two little-endian 16-bit integers.
    
    Example:
        Version((3, 0, 1, 2)) = '\x00\x03\x00\x01'
    """
    def __init__(self, value):
        self.value = value
        self.length = 4

    def serialize(self):
        val = (self.value[1], self.value[0], self.value[3], self.value[2])
        return struct.pack('<4B', *val)

    @classmethod
    def deserialize(cls, bytes):
        val = struct.unpack_from('<4B', bytes)
        return cls((val[1], val[0], val[3], val[2]))

    def pprint(self):
        return '%d.%d.%d.%d' % self.value

class String(DAAPType):
    """
    Unicode string value. Default encoding is utf-8, which is what is used by
    both iTunes and the Remote app. Other encodings can be used, but there is
    no guarantee that the receiving application will properly decode them.
    
    Serialized as a byte string with no length bytes or null terminator.
    """
    def __init__(self, value, codec='utf-8'):
        self.codec = codec
        self.value = unicode(value)
        self.length = len(self.serialize())

    def serialize(self):
        return self.value.encode(self.codec)

    @classmethod
    def deserialize(cls, bytes, codec='utf-8'):
        return cls(bytes.decode(codec))

    def __str__(self):
        return "'%s'" % self.serialize()

    def __unicode__(self):
        return u"'%s'" % self.value

class Binary(DAAPType):
    """
    Raw binary value. The value can be passed to other types to be deserialized
    at any point, if the actual type becomes known.
    """
    def __init__(self, value):
        self.value = value
        self.length = len(self.value)

    def serialize(self):
        return self.value

    @classmethod
    def deserialize(cls, bytes):
        return cls(bytes)

    def pprint(self):
        return repr(self.value)

class Container(DAAPType):
    """
    A value that holds either a list of Nodes, or a single String.
    
    Serialized as the concatenation of all its components' serialized values.
    
    Example:
        Container(String('Foo') = 'Foo'
        Container([
            Node('msup', True),
            Node('musr', 2)
        ]) = 'msup\x00\x00\x00\x01\xffmusr\x00\x00\x00\x04\x00\x00\x00\x02'
    """

    def __init__(self, value):
        self.value = value
        if isinstance(self.value, String):
            self.length = len(self.value)
        else:
            self.length = sum([len(x) for x in self.value])

    def serialize(self):
        if isinstance(self.value, String):
            return self.value.serialize()
        else:
            return ''.join([x.serialize() for x in self.value])

    @classmethod
    def deserialize(cls, bytes):
        pos = 0
        values = []
        while pos < len(bytes):
            try:
                val = Node.deserialize(bytes[pos:])
            except ValueError:
                return cls(String.deserialize(bytes[pos:]))
            pos += len(val)
            values.append(val)
        return cls(values)

    def pprint(self, depth=0):
        sep = (' ' * depth * 4)
        if isinstance(self.value, String):
            return sep + unicode(self.value) + '\n'
        else:
            return unicode(sep + sep.join([x.pprint(depth) for x in self.value]))

    def __iter__(self):
        return self.value.__iter__()

    def __contains__(self, key):
        for i in self.value:
            try:
                if i.tag == key:
                    return True
            except AttributeError:
                # not a list of nodes
                return False
        return False

    def __unicode__(self):
        return u'[' + ', '.join([unicode(x) for x in self.value]) + ']'


class Node(DAAPType):
    """
    A tag-value pair - the fundamental building block in a DACP response.
    
    Serialized as follows:
        4-byte tag | 4-byte data length | data
    
    Example:
        Node('musr', 65535) = 'musr\x00\x00\x00\x04\x00\x00\xff\xff'
    """
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value
        self.length = self.value.length + 8

    def __getattr__(self, name):
        if isinstance(self.value, Container):
            try:
                vals = []
                for x in [item for item in self.value if item.tag == name]:
                    if isinstance(x.value, (Container, Node)):
                        vals.append(x)
                    else:
                        vals.append(x.value.value)
                return vals
            except AttributeError:
                pass

        raise AttributeError(name)

    def __eq__(self, other):
        try:
            return (self.tag == other.tag) and (self.value == other.value)
        except AttributeError:
            return False

    def __ne__(self, other):
        try:
            return (self.tag != other.tag) or (self.value != other.value)
        except AttributeError:
            return True

    def __unicode__(self):
        return u'<%s value="%s">' % (self.tag, unicode(self.value))

    def serialize(self):
        data = self.value.serialize()
        return struct.pack('>4sl', self.tag, len(data)) + data

    @classmethod
    def deserialize(cls, bytes):
        if (len(bytes)) < 8:
            raise ValueError('Not enough data to read tag header')
        (tag, size) = struct.unpack_from('>4sl', bytes)
        data = bytes[8 : 8 + size]
        if len(data) != size:
            raise ValueError('Not enough data to deserialize \'%s\' (%d/%d bytes)' % (tag, len(data), size))
        try:
            tagtype = globals()[tags.TAGS[tag][1]]
        except KeyError:
            tagtype = Binary

        data = tagtype.deserialize(data)
        return cls(tag, data)

    def pprint(self, depth=0):
        from StringIO import StringIO
        try:
            tagdesc = tags.TAGS[self.tag][0]
            if tagdesc:
                tagname = u'%s (%s)' % (self.tag, tagdesc)
            else:
                tagname = self.tag
        except KeyError:
            tagname = self.tag
        out = StringIO()

        if isinstance(self.value, Container):
            depth += 1
            out.write(u'%s --+\n%s' % (tagname, self.value.pprint(depth)))
        else:
            out.write(u'%s = %s\n' % (tagname, self.value.pprint()))
        return unicode(out.getvalue())

def build_node(pair):
    """
    Shortcut method to build a DACP Node tree from (tag, value) tuples.
    
    The tag must be a string, and the value will be converted to the
    appropriate type for the tag. If the value is a callable, it will
    be called and the returned value used for the node.
    
    Examples:
        
        build_node(('mstt', 200))      # uint node
        
        build_node(('msrv', [          # container node
            ('mstt', 200),             # uint node
            ('mslr', True),            # ubyte node
            ('minm', 'Foo'),           # string node
            ('mpro', (1, 2, 3, 4)),    # version node
            ('mstc', datetime.utcnow)  # datetime node
        ]))
    """

    tag, value = pair

    if callable(value):
        value = value()

    try:
        tagname, typename = tags.TAGS[tag]
        tagtype = globals()[typename]

        if tagtype == Container:
            if isinstance(value, list):
                value = [build_node(x) for x in value]
            else:
                value = String(value)

        return Node(tag, tagtype(value))
    except KeyError:
        raise UnknownTagError(tag)

