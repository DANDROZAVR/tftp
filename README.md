# SO shell - etap1
Simple client and server python [tftp](https://datatracker.ietf.org/doc/html/rfc1350) implementation for transfer files.

## Client
The Client is designed to download the file with the name *filename* (which easily can be the whole path) from server, using the *port* and server's *hostname*. 

##### Usage

```
python3 client.py <port> <hostname> <filename>
python3 client.py 69 localhost a.txt
```

## Server
Mr. Server can serve multiple connections with different clients at the same time, having the relevant information about such communication. At the beginning, *window size* and *block size* can be specified if the client brings him the necessary information (and of course server can offer his own remarks)

##### Usage

```
python3 server.py <port>
python3 server.py 69
```

