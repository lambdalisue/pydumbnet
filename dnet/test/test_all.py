#!/usr/bin/env python

import unittest

import dnet


class AddrTestCase(unittest.TestCase):

    def test_addr_cmp(self):
        for atxt in ('1.2.3.0', '0:d:e:a:d:0', 'fe::ed:fa:ce:0'):
            a = dnet.addr(atxt)
            b = dnet.addr(atxt)
            assert a == b

            b = dnet.addr(atxt[:-1] + '1')
            assert a < b
            assert b > a

    def test_addr_bcast(self):
        d = {
            32: '10.0.0.0',
            31: '10.0.0.1',
            30: '10.0.0.3',
            29: '10.0.0.7',
            28: '10.0.0.15',
            27: '10.0.0.31',
            26: '10.0.0.63',
            25: '10.0.0.127',
            24: '10.0.0.255',
            23: '10.0.1.255',
            22: '10.0.3.255',
            21: '10.0.7.255',
            20: '10.0.15.255',
            19: '10.0.31.255'}
        for bits in d:
            a = dnet.addr('%s/%d' % (d[32], bits))
            b = a.bcast()
            self.failUnless(b.__str__() == d[bits],
                            'wrong bcast for /%d' % bits)

    def test_addr_net(self):
        d = {32: '1.255.255.255', 31: '1.255.255.254', 30: '1.255.255.252',
             29: '1.255.255.248', 28: '1.255.255.240', 27: '1.255.255.224',
             26: '1.255.255.192', 25: '1.255.255.128', 24: '1.255.255.0',
             23: '1.255.254.0', 22: '1.255.252.0', 21: '1.255.248.0',
             20: '1.255.240.0', 19: '1.255.224.0'}
        for bits in d:
            a = dnet.addr('%s/%d' % (d[32], bits))
            b = a.net()
            self.failUnless(b.__str__() == d[bits],
                            'wrong net for /%d' % bits)

    def test_addr_properties(self):
        atxt = '1.2.3.4/24'
        a = dnet.addr(atxt)
        assert a.type == dnet.ADDR_TYPE_IP and a.bits == 24
        assert a.ip == '\x01\x02\x03\x04' and a.__str__() == atxt
        try:
            self.failUnless(a.eth == 'xxx', 'invalid eth property')
        except ValueError:
            pass

        atxt = '00:0d:0e:0a:0d:00'
        a = dnet.addr(atxt)
        assert a == dnet.addr('0:d:E:a:D:0')
        assert a.type == dnet.ADDR_TYPE_ETH and a.bits == 48
        assert a.eth == '\x00\x0d\x0e\x0a\x0d\x00' and a.__str__() == atxt
        try:
            self.failUnless(a.ip6 == 'xxx', 'invalid ip6 property')
        except ValueError:
            pass

        atxt = 'fe80::dead:beef:feed:face/48'
        a = dnet.addr(atxt)
        assert a == dnet.addr('fe80:0:0::dead:beef:feed:face/48')
        assert a.type == dnet.ADDR_TYPE_IP6 and a.bits == 48
        assert a.ip6 == '\xfe\x80\x00\x00\x00\x00\x00\x00\xde\xad\xbe\xef\xfe\xed\xfa\xce' and a.__str__(
            ) == atxt
        try:
            self.failUnless(a.ip == 'xxx', 'invalid ip property')
        except ValueError:
            pass


class ArpTestCase(unittest.TestCase):

    def setUp(self):
        self.arp = dnet.arp()
        self.failUnless(self.arp, "couldn't open ARP handle")

    def tearDown(self):
        del self.arp

    def test_arp(self):
        # XXX - site-specific values here!
        pa = dnet.addr('192.168.0.123')
        ha = dnet.addr('0:d:e:a:d:0')
        self.failUnless(self.arp.add(pa, ha) is None, "couldn't add ARP entry")
        self.failUnless(self.arp.get(pa) == ha, "couldn't find ARP entry")
        self.failUnless(
            self.arp.delete(pa) is None,
            "couldn't delete ARP entry")

    def __arp_cb(self, pa, ha, arg):
        # XXX - do nothing
        return arg

    def test_arp_loop(self):
        assert self.arp.loop(self.__arp_cb, 0) == 0
        assert self.arp.loop(self.__arp_cb, 123) == 123

    def test_arp_misc(self):
        sha = '\x00\x0d\x0e\x0a\x0d\x00'
        spa = '\x01\x02\x03\x04'
        dha = '\x00\x0b\x0e\x0e\x0f\x00'
        dpa = '\x05\x06\x07\x08'
        msg = dnet.arp_pack_hdr_ethip(dnet.ARP_OP_REQUEST, sha, spa, dha, dpa)
        assert msg == '\x00\x01\x08\x00\x06\x04\x00\x01\x00\r\x0e\n\r\x00\x01\x02\x03\x04\x00\x0b\x0e\x0e\x0f\x00\x05\x06\x07\x08'


class EthTestCase(unittest.TestCase):

    def setUp(self):
        self.dev = dnet.intf().get_dst(dnet.addr('1.2.3.4'))['name']
        self.eth = dnet.eth(self.dev)
        self.failUnless(self.eth, "couldn't open Ethernet handle")

    def tearDown(self):
        del self.eth

    def test_eth_get(self):
        mac = self.eth.get()
        self.failUnless(mac, "couldn't get Ethernet address for %s" % self.dev)

    def test_eth_misc(self):
        n = "\x00\x0d\x0e\x0a\x0d\x00"
        a = '00:0d:0e:0a:0d:00'
        self.failUnless(dnet.eth_ntoa(n) == a)
        self.failUnless(dnet.eth_aton(a) == n)
        dst = "\x00\x0d\x0e\x0a\x0d\x01"
        self.failUnless(dnet.eth_pack_hdr(n, dst, dnet.ETH_TYPE_IP) ==
                        '\x00\r\x0e\n\r\x00\x00\r\x0e\n\r\x01\x08\x00')


class FwTestCase(unittest.TestCase):

    def setUp(self):
        self.dev = dnet.intf().get_dst(dnet.addr('1.2.3.4'))['name']
        self.fw = dnet.fw()
        self.failUnless(self.fw, "couldn't open firewall handle")

    def tearDown(self):
        del self.fw

    def test_fw(self):
        src = dnet.addr('1.2.3.4')
        dst = dnet.addr('5.6.7.8')
        d = {'device': self.dev,
             'op': dnet.FW_OP_BLOCK,
             'dir': dnet.FW_DIR_OUT,
             'proto': dnet.IP_PROTO_UDP,
             'src': src,
             'dst': dst,
             'dport': (660, 666)
             }
        self.failUnless(self.fw.add(d) is None,
                        "couldn't add firewall rule: %s" % d)
        self.failUnless(self.fw.delete(d) is None,
                        "couldn't delete firewall rule: %s" % d)

    def __fw_cb(self, rule, arg):
        # XXX - do nothing
        return arg

    def test_fw_loop(self):
        assert self.fw.loop(self.__fw_cb, 0) == 0
        # XXX - no guarantee of existing fw rules.
        #assert self.fw.loop(self.__fw_cb, 123) == 123


class IntfTestCase(unittest.TestCase):

    def setUp(self):
        self.intf = dnet.intf()
        self.failUnless(self.intf, "couldn't open interface handle")

    def tearDown(self):
        del self.intf

    def test_intf_get(self):
        lo0 = self.intf.get('lo0')
        self.failUnless(lo0['name'] == 'lo0', "couldn't get loopback config")
        self.failUnless(self.intf.get_src(dnet.addr('127.0.0.1')) == lo0,
                        "couldn't get_src 127.0.0.1")
        gw = self.intf.get_dst(dnet.addr('1.2.3.4'))
        self.failUnless(gw, "couldn't get outgoing interface")

    def test_intf_set(self):
        lo0 = self.intf.get('lo0')
        old_mtu = lo0['mtu']
        new_mtu = 1234
        lo0['mtu'] = new_mtu
        self.intf.set(lo0)
        lo0 = self.intf.get('lo0')
        assert lo0['mtu'] == new_mtu
        lo0['mtu'] = old_mtu
        self.intf.set(lo0)

    def __intf_cb(self, ifent, arg):
        # XXX - do nothing
        return arg

    def test_intf_loop(self):
        assert self.intf.loop(self.__intf_cb, 0) == 0
        assert self.intf.loop(self.__intf_cb, 123) == 123


class IpTestCase(unittest.TestCase):

    def setUp(self):
        self.ip = dnet.ip()
        self.failUnless(self.ip, "couldn't open raw IP handle")

    def tearDown(self):
        del self.ip

    def test_ip_misc(self):
        n = '\x01\x02\x03\x04'
        a = '1.2.3.4'
        self.failUnless(dnet.ip_ntoa(n) == a)
        self.failUnless(dnet.ip_aton(a) == n)
        dst = '\x05\x06\x07\x08'
        hdr = dnet.ip_pack_hdr(0, dnet.IP_HDR_LEN, 666, 0, 255,
                               dnet.IP_PROTO_UDP, n, dst)
        assert hdr == 'E\x00\x00\x14\x02\x9a\x00\x00\xff\x11\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08'
        hdr = dnet.ip_checksum(hdr)
        assert hdr == 'E\x00\x00\x14\x02\x9a\x00\x00\xff\x11\xa9+\x01\x02\x03\x04\x05\x06\x07\x08'


class RandTestCase(unittest.TestCase):

    def setUp(self):
        self.rand = dnet.rand()
        self.failUnless(self.rand, "couldn't open random handle")

    def tearDown(self):
        del self.rand


class RouteTestCase(unittest.TestCase):

    def setUp(self):
        self.route = dnet.route()
        self.failUnless(self.route, "couldn't open route handle")

    def tearDown(self):
        del self.route

    def test_route(self):
        dst = dnet.addr('1.2.3.4/24')
        gw = dnet.addr('127.0.0.1')
        self.route.add(dst, gw)
        self.failUnless(self.route.get(dst) == gw)
        self.route.delete(dst)

    def __route_cb(self, dst, gw, arg):
        # XXX - do nothing
        return arg

    def test_route_loop(self):
        assert self.route.loop(self.__route_cb, 0) == 0
        assert self.route.loop(self.__route_cb, 123) == 123

if __name__ == '__main__':
    unittest.main()
