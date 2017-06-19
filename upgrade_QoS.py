from mininet.net import Mininet,CLI
from mininet.node import RemoteController, OVSController,OVSKernelSwitch, OVSHtbQosSwitch, Host
from mininet.link import TCLink,Link
from mininet.term import makeTerms, makeTerm, runX11
import argparse
import subprocess

__author__ = 'cgiraldo'


net = Mininet( topo=None, listenPort=6633, ipBase='10.0.0.0/8')

h1 = net.addHost( 'server1', mac = '00:00:00:00:00:01', ip='10.0.0.1' )
h2 = net.addHost( 'noise2', mac = '00:00:00:00:00:02', ip='10.0.0.2' )
h3 = net.addHost( 'premium3', mac = '00:00:00:00:00:03', ip='10.0.0.3' )
h4 = net.addHost( 'regular4', mac = '00:00:00:00:00:04', ip='10.0.0.4' )
h5 = net.addHost( 'regular5', mac = '00:00:00:00:00:05', ip='10.0.0.5' )
s1 = net.addSwitch( 'edge1', cls=OVSKernelSwitch, protocols='OpenFlow13' )
s2 = net.addSwitch( 'core2', cls=OVSHtbQosSwitch, protocols='OpenFlow13' )
s3 = net.addSwitch( 'edge3', cls=OVSKernelSwitch, protocols='OpenFlow13' )
net.addLink( h1, s1, cls=Link)
net.addLink( h2, s1, cls=Link)
net.addLink( s1, s2, cls=Link)

net.addLink( s2, s3, cls=TCLink, bw=10)

net.addLink( s3, h3, cls=TCLink, bw=10)
net.addLink( s3, h4, cls=TCLink, bw=10)
net.addLink( s3, h5, cls=TCLink, bw=10)

#c0 = net.addController( 'c0', RemoteController, protocols='OpenFlow13', port=6633)
c0 = net.addController('c0', OVSController, protocols='OpenFlow13')

net.start()
## Configure Priority queues in core router
s2.cmd('ovs-vsctl -- set port core2-eth2 qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q0,1=@q1 -- \
--id=@q0 create queue other-config:min-rate=2000 other-config:max-rate=10000000 -- \
--id=@q1 create queue other-config:min-rate=1000000 other-config:max-rate=10000000')

## Set premium user flows in priority queue
add_premium_flow_qos = 'ovs-ofctl -OOpenFlow13 add-flow core2 \
priority=10,table=0,ip,ip_src={0},ip_dst={1},\
actions=set_queue:1,output:2'.format(h1.IP(),h3.IP())
print add_premium_flow_qos
s2.cmd(add_premium_flow_qos)

xterms = []
[tunnel, term] = runX11( h3, 'vlc-wrapper --rtp-caching=1 rtp://@:5004  --meta-title="premium user:receiving video"')
xterms.append(term)
[tunnel, term] = runX11( h4, 'vlc-wrapper --rtp-caching=1 rtp://@:5004  --meta-title="regular user:receiving video"')
xterms.append(term)

[term] = makeTerm(h5, title='UDP Noise Receiver', cmd="iperf -u -s -i 1")
print h5.IP()
xterms.append(term)
[term] = makeTerm(h2, title='Udp Noise Sender: bash; iperf -u -c IP -b 5M -t 10')
xterms.append(term)

[term] = makeTerm(h1, title='RTP Stream Emiter: ./send_video.sh VIDEO', cmd="bash")
xterms.append(term)

CLI(net)

net.stop()

for term in xterms:
    term.kill()


