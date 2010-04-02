# coding: utf8

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

from datetime import datetime
from nose import tools

from dacpy.types import *

class TestNumericTypes:
    @tools.raises(ValueError)
    def test_unsigned_big_value(self):
        n = UByte(256)

    @tools.raises(ValueError)
    def test_signed_big_value(self):
        n = Byte(128)

    @tools.raises(ValueError)
    def test_unsigned_small_value(self):
        n = UByte(-1)

    @tools.raises(ValueError)
    def test_signed_small_value(self):
        n = Byte(-129)

    @tools.raises(TypeError)
    def test_bad_Value(self):
        n = UByte('s')

    def test_equivalence(self):
        n = UInt(42)
        tools.assert_equals(n, UInt(42))
        tools.assert_equals(n, 42)
        tools.assert_not_equals(n, 43)
        tools.assert_not_equals(n, UShort(42))

    def test_string(self):
        n = UInt(42)
        tools.assert_equals(str(n), '42')
        tools.assert_equals(unicode(n), u'42')
        tools.assert_equals(n.pprint(), '0x0000002A == 42')

    def test_serialize(self):
        tools.assert_equals(UByte(255).serialize(), '\xff')

    def test_deserialize(self):
        tools.assert_equals(UByte.deserialize('\xff').value, 255)

class TestMultiIntTypes:
    def test_signed(self):
        n = MultiInt((-1, 1))
        tools.assert_equals(len(n), 8)
        tools.assert_equals(n.serialize(), '\xff\xff\xff\xff\x00\x00\x00\x01')
        tools.assert_equals(MultiInt.deserialize('\xff\xff\xff\xff\x00\x00\x00\x01').value, (-1, 1))
        tools.assert_equals(n.pprint(), '(0xFFFFFFFF == -1, 0x00000001 == 1)')

    def test_unsigned(self):
        n = MultiUInt((4294967295, 1))
        tools.assert_equals(len(n), 8)
        tools.assert_equals(n.serialize(), '\xff\xff\xff\xff\x00\x00\x00\x01')
        tools.assert_equals(MultiUInt.deserialize('\xff\xff\xff\xff\x00\x00\x00\x01').value, (4294967295, 1))
        tools.assert_equals(n.pprint(), '(0xFFFFFFFF == 4294967295, 0x00000001 == 1)')


class TestStringType:
    def test_ascii_serialize(self):
        n = String('hello')
        tools.assert_equals(n.serialize(), 'hello')
        tools.assert_equals(n.pprint(), 'hello')

    def test_unicode_serialize(self):
        tools.assert_equals(String(u'привет').serialize(), '\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82')

    def test_ascii_deserialize(self):
        tools.assert_equals(String.deserialize('hello').value, 'hello')

    def test_unicode_deserialize(self):
        tools.assert_equals(String.deserialize('\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82').value, u'привет')

    def test_special_length(self):
        val = String(u'Zem\xe2\x80\x99s Library')
        tools.assert_equals(len(val), 18)

class TestBinaryType:
    def test_serialize(self):
        tools.assert_equals(Binary('\x00\x01').serialize(), '\x00\x01')

    def test_deserialize(self):
        tools.assert_equals(Binary.deserialize('\x00\x01').value, '\x00\x01')

class TestDateTimeType:
    def test_serialize(self):
        d = DateTime(datetime(2010, 3, 11, 11, 31, 58))
        tools.assert_equals(d.serialize(), '\x4b\x99\x45\x2e')

    def test_deserialize(self):
        d = DateTime.deserialize('\x4b\x99\x45\x2e')
        tools.assert_equals(d.value, datetime(2010, 3, 11, 11, 31, 58))

    def test_negative(self):
        zero = datetime(1969, 12, 31, 9, 0)
        tools.assert_equals(DateTime.deserialize('\xff\xff\x9d\x90').value, zero)
        tools.assert_equals(DateTime(None).serialize(), '\xff\xff\x9d\x90')

class TestVersionType:
    def test_version_serialize(self):
        n = Version((3,0,1,0))
        tools.assert_equals(n.serialize(), '\x00\x03\x00\x01')
        tools.assert_equals(n.pprint(), '3.0.1.0')

    def test_version_deserialize(self):
        tools.assert_equals(Version.deserialize('\x00\x03\x00\x01'), Version((3,0,1,0)))

class TestContainerType:
    def test_container_serialize(self):
        n1 = Node('msup', UByte(1))
        n2 = Node('msup', UByte(2))
        n3 = Node('msup', UByte(3))
        lst = Container([n1, n2, n3])
        tools.assert_equals(len(lst), 27)
        tools.assert_equals(lst.value, [n1, n2, n3])
        tools.assert_true('msup' in lst)
        tools.assert_false('mstt' in lst)

        bytes = 'msup\x00\x00\x00\x01\x01msup\x00\x00\x00\x01\x02msup\x00\x00\x00\x01\x03'
        tools.assert_equals(lst.serialize(), bytes)

    def test_container_deserialize(self):
        n1 = Node('msup', UByte(1))
        n2 = Node('msup', UByte(2))
        n3 = Node('msup', UByte(3))

        bytes = 'msup\x00\x00\x00\x01\x01msup\x00\x00\x00\x01\x02msup\x00\x00\x00\x01\x03'
        lst = Container.deserialize(bytes)
        tools.assert_equals(lst.serialize(), bytes)
        tools.assert_equals(len(lst), 27)
        tools.assert_equals(lst.value[0], n1)
        tools.assert_equals(lst.value[1], n2)
        tools.assert_equals(lst.value[2], n3)

    def test_non_node_container(self):
        bytes = 'mlit\x00\x00\x00\x05Hellomlit\x00\x00\x00\x05World'
        lst = Container.deserialize(bytes)
        tools.assert_equals(lst.value[0], Node('mlit', String('Hello')))
        tools.assert_equals(lst.value[1], Node('mlit', String('World')))
        tools.assert_equals(lst.serialize(), bytes)

class TestNodeType:
    def test_simple_serialize(self):
        node = Node('msup', UByte(255))
        tools.assert_equals(node.tag, 'msup')
        tools.assert_equals(len(node), 9)
        tools.assert_equals(node.value, 255)
        tools.assert_equals(node.serialize(), 'msup\x00\x00\x00\x01\xff')

    def test_simple_deserialize(self):
        node = Node.deserialize('msup\x00\x00\x00\x01\xff')
        tools.assert_equals(node.serialize(), 'msup\x00\x00\x00\x01\xff')
        tools.assert_equals(node.tag, 'msup')
        tools.assert_equals(len(node), 9)
        tools.assert_equals(node.value, 255)

    def test_interface(self):
        node = Node('msrv', Container([
            Node('mstt', UInt(200)),
            Node('mlcl', Container([
                Node('minm', String('Zem\'s Library')),
            ])),
        ]))
        tools.assert_equals(node.mstt[0], 200)
        tools.assert_equals(node.mlcl[0].minm[0], 'Zem\'s Library')

    def test_pprint(self):
        node = Node('msrv', Container([
            Node('mstt', UInt(200)),
        ]))
        tools.assert_equals(node.pprint(), 'msrv (dmap.serverinforesponse) --+\n    mstt (dmap.status) = 0x000000C8 == 200\n')

class TestShorthand:
    def test_build_node(self):
        n1 = build_node(('msrv', [
            ('mstt', lambda: 200),
            ('mpro', (2, 0, 6, 0)),
            ('musr', UShort(64)),
            ('msed', True),
            ('msml', [
                ('msma', 71359108752128L),
                ('msma', 1102738509824L),
                ('msma', 8799319904256L),
            ]),
            ('mlit', 'Foo'),
            ('ceWM', ''),
            ('minm', u'Zem\xe2\x80\x99s Library'),
            ('mstm', 1800),
            ('mstc', datetime(2010, 3, 12, 12, 46, 10)),
        ]))

        n2 = Node('msrv', Container([
            Node('mstt', UInt(200)),
            Node('mpro', Version((2, 0, 6, 0))),
            Node('musr', UInt(64)),
            Node('msed', UByte(1)),
            Node('msml', Container([
                Node('msma', ULong(71359108752128L)),
                Node('msma', ULong(1102738509824L)),
                Node('msma', ULong(8799319904256L)),
            ])),
            Node('mlit', Container('Foo')),
            Node('ceWM', Binary('')),
            Node('minm', String(u'Zem\xe2\x80\x99s Library')),
            Node('mstm', UInt(1800)),
            Node('mstc', DateTime(datetime(2010, 3, 12, 12, 46, 10))),
        ]))

        tools.assert_equals(n1, n2)
