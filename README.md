#                                Python vServer

 PyvServ is a fully fledged encrypting TCP/IP server written in Python. The
encryption algorithm is bluepoint2. The server can be fully administered from
the protocol side.

 PyvServ contains protocol level encryption, which can be switched on by
instructing the server to use an encryption key.

 PyvServ contains key exchange protocol, so the new session keys
can be transmitted securely, even with zero knowledge.

 PyvServ internally generates a random key, so communication is always

 Project still in motion, not much is usable yet.

Working so far:

 Bluepoint2. The subdir bluepy contains the 'c' code and the python binding.

 make build;    # operational
 make test;     # operational

Partiall Working:

 Server.
 Client.
 Test Suite:



##          BELOW IS OLD INFO, PLEASE WAIT FOR UPDATE (dec/2018)

 The server's user names and initial keys can only be initialized from the
loopback interface. An unconfigured server will refuse to accept logins,
but can be configured remotely via public key encryption.

 The best way to learn about the operation of the server is to look at the
sample client examples in the pyclient source tree. (Files named pycli_*)

 User initialization:

 The uini command allows one to create the initial user. It only accepts
the uni command from the loopback interface. Once the initial user is created,
the uini command returns an error.

 Key initialization:

The keys can be initialized by the kini command. The server only accepts the
kini from the loopback interface. Once the initial key is created, the kini command
returns an error.

 After the initial user and initial key has been created, the server can be
securely administered via the protocol interface. Make sure you switch on your
initial encryption key via the xkey command.

  To add a user, use uadd.

  , to add a key use kadd.

 Once a user is created, its parameters are not alterable. If you need to specify a
new pass, simply delete and recreate the user. This has the advantage of no logins
while the user's parameters change. The user created by uini cannot be deleted.

 Protocol usage. The protocol has most of the commands of a traditional file
transfer protocol. See client source examples for more info. The help facility
of PyvServ is able to deliver useful information as well.

Versioning.

  The 'C' module has a date API, that is generated automatically. Use it to
distinguish algorythm versioning.

    print( "Builddate: ",  bluepy.builddate())






