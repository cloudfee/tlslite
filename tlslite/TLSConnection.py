"""
MAIN CLASS FOR TLS LITE (START HERE!).
"""
from __future__ import generators

import socket
from utils.compat import formatExceptionTrace
from TLSRecordLayer import TLSRecordLayer
from Session import Session
from constants import *
from utils.cryptomath import getRandomBytes
from errors import *
from messages import *
from mathtls import *
from HandshakeSettings import HandshakeSettings


class TLSConnection(TLSRecordLayer):
    """
    This class wraps a socket and provides TLS handshaking and data
    transfer.

    To use this class, create a new instance, passing a connected
    socket into the constructor.  Then call some handshake function.
    If the handshake completes without raising an exception, then a TLS
    connection has been negotiated.  You can transfer data over this
    connection as if it were a socket.

    This class provides both synchronous and asynchronous versions of
    its key functions.  The synchronous versions should be used when
    writing single-or multi-threaded code using blocking sockets.  The
    asynchronous versions should be used when performing asynchronous,
    event-based I/O with non-blocking sockets.

    Asynchronous I/O is a complicated subject; typically, you should
    not use the asynchronous functions directly, but should use some
    framework like asyncore or Twisted which TLS Lite integrates with
    (see
    L{tlslite.integration.TLSAsyncDispatcherMixIn.TLSAsyncDispatcherMixIn}).
    """


    def __init__(self, sock):
        """Create a new TLSConnection instance.

        @param sock: The socket data will be transmitted on.  The
        socket should already be connected.  It may be in blocking or
        non-blocking mode.

        @type sock: L{socket.socket}
        """
        TLSRecordLayer.__init__(self, sock)

    def handshakeClientSRP(self, username, password, session=None,
                           settings=None, checker=None, async=False):
        """Perform an SRP handshake in the role of client.

        This function performs a TLS/SRP handshake.  SRP mutually
        authenticates both parties to each other using only a
        username and password.  This function may also perform a
        combined SRP and server-certificate handshake, if the server
        chooses to authenticate itself with a certificate chain in
        addition to doing SRP.

        If the function completes without raising an exception, the
        TLS connection will be open and available for data transfer.

        If an exception is raised, the connection will have been
        automatically closed (if it was ever open).

        @type username: str
        @param username: The SRP username.

        @type password: str
        @param password: The SRP password.

        @type session: L{tlslite.Session.Session}
        @param session: A TLS session to attempt to resume.  This
        session must be an SRP session performed with the same username
        and password as were passed in.  If the resumption does not
        succeed, a full SRP handshake will be performed.

        @type settings: L{tlslite.HandshakeSettings.HandshakeSettings}
        @param settings: Various settings which can be used to control
        the ciphersuites, certificate types, and SSL/TLS versions
        offered by the client.

        @type checker: L{tlslite.Checker.Checker}
        @param checker: A Checker instance.  This instance will be
        invoked to examine the other party's authentication
        credentials, if the handshake completes succesfully.

        @type async: bool
        @param async: If False, this function will block until the
        handshake is completed.  If True, this function will return a
        generator.  Successive invocations of the generator will
        return 0 if it is waiting to read from the socket, 1 if it is
        waiting to write to the socket, or will raise StopIteration if
        the handshake operation is completed.

        @rtype: None or an iterable
        @return: If 'async' is True, a generator object will be
        returned.

        @raise socket.error: If a socket error occurs.
        @raise tlslite.errors.TLSAbruptCloseError: If the socket is closed
        without a preceding alert.
        @raise tlslite.errors.TLSAlert: If a TLS alert is signalled.
        @raise tlslite.errors.TLSAuthenticationError: If the checker
        doesn't like the other party's authentication credentials.
        """
        handshaker = self._handshakeClientAsync(srpParams=(username, password),
                        session=session, settings=settings, checker=checker)
        if async:
            return handshaker
        for result in handshaker:
            pass

    def handshakeClientCert(self, certChain=None, privateKey=None,
                            session=None, settings=None, checker=None,
                            async=False):
        """Perform a certificate-based handshake in the role of client.

        This function performs an SSL or TLS handshake.  The server
        will authenticate itself using an X.509 certificate
        chain.  If the handshake succeeds, the server's certificate
        chain will be stored in the session's serverCertChain attribute.
        Unless a checker object is passed in, this function does no
        validation or checking of the server's certificate chain.

        If the server requests client authentication, the
        client will send the passed-in certificate chain, and use the
        passed-in private key to authenticate itself.  If no
        certificate chain and private key were passed in, the client
        will attempt to proceed without client authentication.  The
        server may or may not allow this.

        If the function completes without raising an exception, the
        TLS connection will be open and available for data transfer.

        If an exception is raised, the connection will have been
        automatically closed (if it was ever open).

        @type certChain: L{tlslite.X509CertChain.X509CertChain}
        @param certChain: The certificate chain to be used if the
        server requests client authentication.

        @type privateKey: L{tlslite.utils.RSAKey.RSAKey}
        @param privateKey: The private key to be used if the server
        requests client authentication.

        @type session: L{tlslite.Session.Session}
        @param session: A TLS session to attempt to resume.  If the
        resumption does not succeed, a full handshake will be
        performed.

        @type settings: L{tlslite.HandshakeSettings.HandshakeSettings}
        @param settings: Various settings which can be used to control
        the ciphersuites, certificate types, and SSL/TLS versions
        offered by the client.

        @type checker: L{tlslite.Checker.Checker}
        @param checker: A Checker instance.  This instance will be
        invoked to examine the other party's authentication
        credentials, if the handshake completes succesfully.

        @type async: bool
        @param async: If False, this function will block until the
        handshake is completed.  If True, this function will return a
        generator.  Successive invocations of the generator will
        return 0 if it is waiting to read from the socket, 1 if it is
        waiting to write to the socket, or will raise StopIteration if
        the handshake operation is completed.

        @rtype: None or an iterable
        @return: If 'async' is True, a generator object will be
        returned.

        @raise socket.error: If a socket error occurs.
        @raise tlslite.errors.TLSAbruptCloseError: If the socket is closed
        without a preceding alert.
        @raise tlslite.errors.TLSAlert: If a TLS alert is signalled.
        @raise tlslite.errors.TLSAuthenticationError: If the checker
        doesn't like the other party's authentication credentials.
        """
        handshaker = self._handshakeClientAsync(certParams=(certChain,
                        privateKey), session=session, settings=settings,
                        checker=checker)
        if async:
            return handshaker
        for result in handshaker:
            pass


    def _handshakeClientAsync(self, srpParams=(), certParams=(),
                             session=None, settings=None, checker=None):

        handshaker = self._handshakeClientAsyncHelper(srpParams=srpParams,
                certParams=certParams,
                session=session,
                settings=settings)
        for result in self._handshakeWrapperAsync(handshaker, checker):
            yield result


    def _handshakeClientAsyncHelper(self, srpParams, certParams, 
                               session, settings):
        
        self._handshakeStart(client=True)

        #Unpack parameters
        srpUsername = None      # srpParams[0]
        password = None         # srpParams[1]
        clientCertChain = None  # certParams[0]
        privateKey = None       # certParams[1]

        # Allow only one of (srpParams, certParams)
        if srpParams:
            assert(not certParams)
            srpUsername, password = srpParams
        if certParams:
            assert(not srpParams)
            clientCertChain, privateKey = certParams

        #Validate parameters
        if srpUsername and not password:
            raise ValueError("Caller passed a username but no password")
        if password and not srpUsername:
            raise ValueError("Caller passed a password but no username")
        if clientCertChain and not privateKey:
            raise ValueError("Caller passed a certChain but no privateKey")
        if privateKey and not clientCertChain:
            raise ValueError("Caller passed a privateKey but no certChain")
        
        # Validates the settings and filters out any unsupported ciphers
        # or crypto libraries that were requested        
        if not settings:
            settings = HandshakeSettings()
        settings = settings._filter()

        if clientCertChain:
            if not isinstance(clientCertChain, X509CertChain):
                raise ValueError("Unrecognized certificate type")
            if "x509" not in settings.certificateTypes:
                raise ValueError("Client certificate doesn't match "\
                                 "Handshake Settings")
                                  
        if session:
            # session.valid() ensures session is resumable and has 
            # non-empty sessionID
            if not session.valid():
                session = None #ignore non-resumable sessions...
            elif session.resumable and \
                    (session.srpUsername != srpUsername):
                raise ValueError("Session username doesn't match")

        #Add Faults to parameters
        if srpUsername and self.fault == Fault.badUsername:
            srpUsername += "GARBAGE"
        if password and self.fault == Fault.badPassword:
            password += "GARBAGE"

        #Tentatively set the version to the client's minimum version.
        #We'll use this for the ClientHello, and if an error occurs
        #parsing the Server Hello, we'll use this version for the response
        self.version = settings.maxVersion

        # Send the ClientHello.
        for result in self._clientSendClientHello(settings, session, 
                                        srpUsername, srpParams, certParams):
            if result in (0,1): yield result
            else: break
        clientHello = result
        
        #Get the ServerHello.
        for result in self._clientGetServerHello(settings, clientHello):
            if result in (0,1): yield result
            else: break
        serverHello = result
        cipherSuite = serverHello.cipher_suite
        
        #If the server elected to resume the session, it is handled here.
        for result in self._clientResume(session, serverHello, 
                        clientHello.random, 
                        settings.cipherImplementations):
            if result in (0,1): yield result
            else: break
        if result == "resumed_and_finished":
            return

        #If the server selected an SRP ciphersuite, the client finishes
        #reading the post-ServerHello messages, then derives a
        #premasterSecret and sends a corresponding ClientKeyExchange.
        if cipherSuite in CipherSuite.srpAllSuites:
            for result in self._clientSRPKeyExchange(\
                    settings, cipherSuite, serverHello.certificate_type, 
                    srpUsername, password,
                    clientHello.random, serverHello.random):                
                if result in (0,1): yield result
                else: break                
            (premasterSecret, serverCertChain) = result           
                
        #If the server selected a certificate-based RSA ciphersuite,
        #the client finishes reading the post-ServerHello messages. If 
        #a CertificateRequest message was sent, the client responds with
        #a Certificate message containing its certificate chain (if any),
        #and also produces a CertificateVerify message that signs the 
        #ClientKeyExchange.
        else:
            for result in self._clientRSAKeyExchange(settings, cipherSuite,
                                    clientCertChain, privateKey,
                                    serverHello.certificate_type,
                                    clientHello.random, serverHello.random):
                if result in (0,1): yield result
                else: break
            (premasterSecret, serverCertChain) = result
                
        self.session = Session()
        self.session._calcMasterSecret(self.version, premasterSecret,
                                      clientHello.random, serverHello.random)
        self.session.sessionID = serverHello.session_id
        self.session.cipherSuite = cipherSuite
        self.session.srpUsername = srpUsername
        self.session.clientCertChain = clientCertChain
        self.session.serverCertChain = serverCertChain
        
        
        #After having previously sent a ClientKeyExchange, the client now
        #initiates an exchange of Finished messages.
        for result in self._clientFinished(clientHello.random, 
                            serverHello.random,
                            settings.cipherImplementations):
            yield result

        #Mark the connection as open
        self.session._setResumable(True)
        self._handshakeDone(resumed=False)


    def _clientSendClientHello(self, settings, session, srpUsername,
                                srpParams, certParams):
        #Initialize acceptable ciphersuites
        cipherSuites = [CipherSuite.TLS_EMPTY_RENEGOTIATION_INFO_SCSV]
        if srpParams:
            cipherSuites += CipherSuite.getSrpAllSuites(settings.cipherNames)
        elif certParams:
            cipherSuites += CipherSuite.getCertSuites(settings.cipherNames)
        else:
            cipherSuites += CipherSuite.getCertSuites(settings.cipherNames)

        #Initialize acceptable certificate types
        certificateTypes = settings._getCertificateTypes()
            
        #Either send ClientHello (with a resumable session)...
        if session and session.sessionID:
            #If it's resumable, then its
            #ciphersuite must be one of the acceptable ciphersuites
            if session.cipherSuite not in cipherSuites:
                raise ValueError("Session's cipher suite not consistent "\
                                 "with parameters")
            else:
                clientHello = ClientHello()
                clientHello.create(settings.maxVersion, getRandomBytes(32),
                                   session.sessionID, cipherSuites,
                                   certificateTypes, session.srpUsername)

        #Or send ClientHello (without)
        else:
            clientHello = ClientHello()
            clientHello.create(settings.maxVersion, getRandomBytes(32),
                               createByteArraySequence([]), cipherSuites,
                               certificateTypes, srpUsername)
        for result in self._sendMsg(clientHello):
            yield result
        yield clientHello


    def _clientGetServerHello(self, settings, clientHello):
        for result in self._getMsg(ContentType.handshake,
                                  HandshakeType.server_hello):
            if result in (0,1): yield result
            else: break
        serverHello = result

        #Get the server version.  Do this before anything else, so any
        #error alerts will use the server's version
        self.version = serverHello.server_version

        #Future responses from server must use this version
        self._versionCheck = True

        #Check ServerHello
        if serverHello.server_version < settings.minVersion:
            for result in self._sendError(\
                AlertDescription.protocol_version,
                "Too old version: %s" % str(serverHello.server_version)):
                yield result
        if serverHello.server_version > settings.maxVersion:
            for result in self._sendError(\
                AlertDescription.protocol_version,
                "Too new version: %s" % str(serverHello.server_version)):
                yield result
        if serverHello.cipher_suite not in clientHello.cipher_suites:
            for result in self._sendError(\
                AlertDescription.illegal_parameter,
                "Server responded with incorrect ciphersuite"):
                yield result
        if serverHello.certificate_type not in clientHello.certificate_types:
            for result in self._sendError(\
                AlertDescription.illegal_parameter,
                "Server responded with incorrect certificate type"):
                yield result
        if serverHello.compression_method != 0:
            for result in self._sendError(\
                AlertDescription.illegal_parameter,
                "Server responded with incorrect compression method"):
                yield result
        yield serverHello
 
    def _clientResume(self, session, serverHello, clientRandom, 
                        cipherImplementations):
        #If the server agrees to resume
        if session and session.sessionID and \
            serverHello.session_id == session.sessionID:

            if serverHello.cipher_suite != session.cipherSuite:
                for result in self._sendError(\
                    AlertDescription.illegal_parameter,\
                    "Server's ciphersuite doesn't match session"):
                    yield result

            #Set the session for this connection
            self.session = session

            #Calculate pending connection states
            self._calcPendingStates(clientRandom, serverHello.random,
                                   cipherImplementations)

            #Exchange ChangeCipherSpec and Finished messages
            for result in self._getFinished():
                yield result
            for result in self._sendFinished():
                yield result

            #Mark the connection as open
            self._handshakeDone(resumed=True)
            yield "resumed_and_finished"        
            
    def _clientSRPKeyExchange(self, settings, cipherSuite, certificateType, 
            srpUsername, password,
            clientRandom, serverRandom):

        #If the server chose an SRP+RSA suite...
        if cipherSuite in CipherSuite.srpCertSuites:
            #Get Certificate, ServerKeyExchange, ServerHelloDone
            for result in self._getMsg(ContentType.handshake,
                    HandshakeType.certificate, certificateType):
                if result in (0,1): yield result
                else: break
            serverCertificate = result
        else:
            serverCertificate = None

        for result in self._getMsg(ContentType.handshake,
                HandshakeType.server_key_exchange, cipherSuite):
            if result in (0,1): yield result
            else: break
        serverKeyExchange = result

        for result in self._getMsg(ContentType.handshake,
                HandshakeType.server_hello_done):
            if result in (0,1): yield result
            else: break
        serverHelloDone = result
            
        #Calculate SRP premaster secret
        #Get and check the server's group parameters and B value
        N = serverKeyExchange.srp_N
        g = serverKeyExchange.srp_g
        s = serverKeyExchange.srp_s
        B = serverKeyExchange.srp_B

        if (g,N) not in goodGroupParameters:
            for result in self._sendError(\
                    AlertDescription.insufficient_security,
                    "Unknown group parameters"):
                yield result
        if numBits(N) < settings.minKeySize:
            for result in self._sendError(\
                    AlertDescription.insufficient_security,
                    "N value is too small: %d" % numBits(N)):
                yield result
        if numBits(N) > settings.maxKeySize:
            for result in self._sendError(\
                    AlertDescription.insufficient_security,
                    "N value is too large: %d" % numBits(N)):
                yield result
        if B % N == 0:
            for result in self._sendError(\
                    AlertDescription.illegal_parameter,
                    "Suspicious B value"):
                yield result

        #Check the server's signature, if server chose an
        #SRP+RSA suite
        serverCertChain = None
        if cipherSuite in CipherSuite.srpCertSuites:
            #Hash ServerKeyExchange/ServerSRPParams
            hashBytes = serverKeyExchange.hash(clientRandom, serverRandom)

            #Extract signature bytes from ServerKeyExchange
            sigBytes = serverKeyExchange.signature
            if len(sigBytes) == 0:
                for result in self._sendError(\
                        AlertDescription.illegal_parameter,
                        "Server sent an SRP ServerKeyExchange "\
                        "message without a signature"):
                    yield result

            #Get server's public key from the Certificate message
            for result in self._clientGetKeyFromChain(serverCertificate,
                                               settings):
                if result in (0,1): yield result
                else: break
            publicKey, serverCertChain = result

            #Verify signature
            if not publicKey.verify(sigBytes, hashBytes):
                for result in self._sendError(\
                        AlertDescription.decrypt_error,
                        "Signature failed to verify"):
                    yield result

        #Calculate client's ephemeral DH values (a, A)
        a = bytesToNumber(getRandomBytes(32))
        A = powMod(g, a, N)

        #Calculate client's static DH values (x, v)
        x = makeX(bytesToString(s), srpUsername, password)
        v = powMod(g, x, N)

        #Calculate u
        u = makeU(N, A, B)

        #Calculate premaster secret
        k = makeK(N, g)
        S = powMod((B - (k*v)) % N, a+(u*x), N)

        if self.fault == Fault.badA:
            A = N
            S = 0
        premasterSecret = numberToBytes(S)

        #Send ClientKeyExchange
        for result in self._sendMsg(\
                ClientKeyExchange(cipherSuite).createSRP(A)):
            yield result
        yield (premasterSecret, serverCertChain)
                   

    def _clientRSAKeyExchange(self, settings, cipherSuite, 
                                clientCertChain, privateKey,
                                certificateType,
                                clientRandom, serverRandom):

        #Get Certificate[, CertificateRequest], ServerHelloDone
        for result in self._getMsg(ContentType.handshake,
                HandshakeType.certificate, certificateType):
            if result in (0,1): yield result
            else: break
        serverCertificate = result

        for result in self._getMsg(ContentType.handshake,
                (HandshakeType.server_hello_done,
                HandshakeType.certificate_request)):
            if result in (0,1): yield result
            else: break
        msg = result

        certificateRequest = None
        if isinstance(msg, CertificateRequest):
            certificateRequest = msg
            for result in self._getMsg(ContentType.handshake,
                    HandshakeType.server_hello_done):
                if result in (0,1): yield result
                else: break
            serverHelloDone = result
        elif isinstance(msg, ServerHelloDone):
            serverHelloDone = msg

        #Get server's public key from the Certificate message
        for result in self._clientGetKeyFromChain(serverCertificate,
                                           settings):
            if result in (0,1): yield result
            else: break
        publicKey, serverCertChain = result

        #Calculate premaster secret
        premasterSecret = getRandomBytes(48)
        premasterSecret[0] = settings.maxVersion[0]
        premasterSecret[1] = settings.maxVersion[1]

        if self.fault == Fault.badPremasterPadding:
            premasterSecret[0] = 5
        if self.fault == Fault.shortPremasterSecret:
            premasterSecret = premasterSecret[:-1]

        #Encrypt premaster secret to server's public key
        encryptedPreMasterSecret = publicKey.encrypt(premasterSecret)

        #If client authentication was requested, send Certificate
        #message, either with certificates or empty
        if certificateRequest:
            clientCertificate = Certificate(certificateType)

            if clientCertChain:
                #Check to make sure we have the same type of
                #certificates the server requested
                wrongType = False
                if certificateType == CertificateType.x509:
                    if not isinstance(clientCertChain, X509CertChain):
                        wrongType = True
                if wrongType:
                    for result in self._sendError(\
                            AlertDescription.handshake_failure,
                            "Client certificate is of wrong type"):
                        yield result

                clientCertificate.create(clientCertChain)
            for result in self._sendMsg(clientCertificate):
                yield result
        else:
            #The server didn't request client auth, so we
            #zeroize these so the clientCertChain won't be
            #stored in the session.
            privateKey = None
            clientCertChain = None

        #Send ClientKeyExchange
        clientKeyExchange = ClientKeyExchange(cipherSuite,
                                              self.version)
        clientKeyExchange.createRSA(encryptedPreMasterSecret)
        for result in self._sendMsg(clientKeyExchange):
            yield result

        #If client authentication was requested and we have a
        #private key, send CertificateVerify
        if certificateRequest and privateKey:
            if self.version == (3,0):
                #Create a temporary session object, just for the
                #purpose of creating the CertificateVerify
                session = Session()
                session._calcMasterSecret(self.version,
                                         premasterSecret,
                                         clientRandom,
                                         serverRandom)
                verifyBytes = self._calcSSLHandshakeHash(\
                                  session.masterSecret, "")
            elif self.version in ((3,1), (3,2)):
                verifyBytes = stringToBytes(\
                    self._handshake_md5.digest() + \
                    self._handshake_sha.digest())
            if self.fault == Fault.badVerifyMessage:
                verifyBytes[0] = ((verifyBytes[0]+1) % 256)
            signedBytes = privateKey.sign(verifyBytes)
            certificateVerify = CertificateVerify()
            certificateVerify.create(signedBytes)
            for result in self._sendMsg(certificateVerify):
                yield result
        yield (premasterSecret, serverCertChain)

    def _clientFinished(self, clientRandom, serverRandom,
                        cipherImplementations):
        #Calculate pending connection states
        self._calcPendingStates(clientRandom, serverRandom,
                               cipherImplementations)

        #Exchange ChangeCipherSpec and Finished messages
        for result in self._sendFinished():
            yield result
        for result in self._getFinished():
            yield result


    def handshakeServer(self, verifierDB=None,
                        certChain=None, privateKey=None, reqCert=False,
                        sessionCache=None, settings=None, checker=None,
                        reqCAs = None):
        """Perform a handshake in the role of server.

        This function performs an SSL or TLS handshake.  Depending on
        the arguments and the behavior of the client, this function can
        perform an SRP, or certificate-based handshake.  It
        can also perform a combined SRP and server-certificate
        handshake.

        Like any handshake function, this can be called on a closed
        TLS connection, or on a TLS connection that is already open.
        If called on an open connection it performs a re-handshake.
        This function does not send a Hello Request message before
        performing the handshake, so if re-handshaking is required,
        the server must signal the client to begin the re-handshake
        through some other means.

        If the function completes without raising an exception, the
        TLS connection will be open and available for data transfer.

        If an exception is raised, the connection will have been
        automatically closed (if it was ever open).

        @type verifierDB: L{tlslite.VerifierDB.VerifierDB}
        @param verifierDB: A database of SRP password verifiers
        associated with usernames.  If the client performs an SRP
        handshake, the session's srpUsername attribute will be set.

        @type certChain: L{tlslite.X509CertChain.X509CertChain}
        @param certChain: The certificate chain to be used if the
        client requests server certificate authentication.

        @type privateKey: L{tlslite.utils.RSAKey.RSAKey}
        @param privateKey: The private key to be used if the client
        requests server certificate authentication.

        @type reqCert: bool
        @param reqCert: Whether to request client certificate
        authentication.  This only applies if the client chooses server
        certificate authentication; if the client chooses SRP
        authentication, this will be ignored.  If the client
        performs a client certificate authentication, the sessions's
        clientCertChain attribute will be set.

        @type sessionCache: L{tlslite.SessionCache.SessionCache}
        @param sessionCache: An in-memory cache of resumable sessions.
        The client can resume sessions from this cache.  Alternatively,
        if the client performs a full handshake, a new session will be
        added to the cache.

        @type settings: L{tlslite.HandshakeSettings.HandshakeSettings}
        @param settings: Various settings which can be used to control
        the ciphersuites and SSL/TLS version chosen by the server.

        @type checker: L{tlslite.Checker.Checker}
        @param checker: A Checker instance.  This instance will be
        invoked to examine the other party's authentication
        credentials, if the handshake completes succesfully.
        
        @type reqCAs: list of L{array.array} of unsigned bytes
        @param reqCAs: A collection of DER-encoded DistinguishedNames that
        will be sent along with a certificate request. This does not affect
        verification.        

        @raise socket.error: If a socket error occurs.
        @raise tlslite.errors.TLSAbruptCloseError: If the socket is closed
        without a preceding alert.
        @raise tlslite.errors.TLSAlert: If a TLS alert is signalled.
        @raise tlslite.errors.TLSAuthenticationError: If the checker
        doesn't like the other party's authentication credentials.
        """
        for result in self.handshakeServerAsync(verifierDB,
                certChain, privateKey, reqCert, sessionCache, settings,
                checker, reqCAs):
            pass


    def handshakeServerAsync(self, verifierDB=None,
                             certChain=None, privateKey=None, reqCert=False,
                             sessionCache=None, settings=None, checker=None,
                             reqCAs=None):
        """Start a server handshake operation on the TLS connection.

        This function returns a generator which behaves similarly to
        handshakeServer().  Successive invocations of the generator
        will return 0 if it is waiting to read from the socket, 1 if it is
        waiting to write to the socket, or it will raise StopIteration
        if the handshake operation is complete.

        @rtype: iterable
        @return: A generator; see above for details.
        """
        handshaker = self._handshakeServerAsyncHelper(\
            verifierDB=verifierDB, certChain=certChain,
            privateKey=privateKey, reqCert=reqCert,
            sessionCache=sessionCache, settings=settings, 
            reqCAs=reqCAs)
        for result in self._handshakeWrapperAsync(handshaker, checker):
            yield result


    def _handshakeServerAsyncHelper(self, verifierDB,
                             certChain, privateKey, reqCert, sessionCache,
                             settings, reqCAs):

        self._handshakeStart(client=False)

        if (not verifierDB) and (not certChain):
            raise ValueError("Caller passed no authentication credentials")
        if certChain and not privateKey:
            raise ValueError("Caller passed a certChain but no privateKey")
        if privateKey and not certChain:
            raise ValueError("Caller passed a privateKey but no certChain")
        if reqCAs and not reqCert:
            raise ValueError("Caller passed reqCAs but not reqCert")            

        if not settings:
            settings = HandshakeSettings()
        settings = settings._filter()

        #Initialize locals
        clientCertChain = None
        serverCertChain = None #We may set certChain to this later
        postFinishedError = None
        
        for result in self._serverGetClientHello(settings, certChain,\
                                                 verifierDB, False, sessionCache):
            if result in (0,1): yield result
            elif result == None:
                return # Handshake was resumed, we're done 
            else: break
        (clientHello, cipherSuite) = result
        
        #If not a resumption

        #If an RSA suite is chosen, check for certificate type intersection
        if cipherSuite in CipherSuite.certSuites + \
                          CipherSuite.srpCertSuites:
            if CertificateType.x509 not in clientHello.certificate_types:
                for result in self._sendError(\
                        AlertDescription.handshake_failure,
                        "the client doesn't support my certificate type"):
                    yield result

            #Move certChain -> serverCertChain, now that we're using it
            serverCertChain = certChain

        #Create sessionID
        if sessionCache:
            sessionID = getRandomBytes(32)
        else:
            sessionID = createByteArraySequence([])

        #If we've selected an SRP suite, exchange keys and calculate
        #premaster secret:
        if cipherSuite in CipherSuite.srpAllSuites:

            #Get parameters from username
            try:
                entry = verifierDB[clientHello.srp_username]
            except KeyError:
                for result in self._sendError(\
                        AlertDescription.unknown_psk_identity):
                    yield result
            (N, g, s, v) = entry

            serverHello = ServerHello()
            serverHello.create(self.version, serverHello.random, sessionID,
                               cipherSuite, CertificateType.x509)            

            #Calculate server's ephemeral DH values (b, B)
            b = bytesToNumber(getRandomBytes(32))
            k = makeK(N, g)
            B = (powMod(g, b, N) + (k*v)) % N

            #Create ServerKeyExchange, signing it if necessary
            serverKeyExchange = ServerKeyExchange(cipherSuite)
            serverKeyExchange.createSRP(N, g, stringToBytes(s), B)
            if cipherSuite in CipherSuite.srpCertSuites:
                hashBytes = serverKeyExchange.hash(clientHello.random,
                                                   serverHello.random)
                serverKeyExchange.signature = privateKey.sign(hashBytes)

            #Send ServerHello[, Certificate], ServerKeyExchange,
            #ServerHelloDone
            msgs = []
            msgs.append(serverHello)
            if cipherSuite in CipherSuite.srpCertSuites:
                certificateMsg = Certificate(CertificateType.x509)
                certificateMsg.create(serverCertChain)
                msgs.append(certificateMsg)
            msgs.append(serverKeyExchange)
            msgs.append(ServerHelloDone())
            for result in self._sendMsgs(msgs):
                yield result

            #From here on, the client's messages must have the right version
            self._versionCheck = True

            #Get and check ClientKeyExchange
            for result in self._getMsg(ContentType.handshake,
                                      HandshakeType.client_key_exchange,
                                      cipherSuite):
                if result in (0,1): yield result
                else: break
            clientKeyExchange = result
            A = clientKeyExchange.srp_A
            if A % N == 0:
                postFinishedError = (AlertDescription.illegal_parameter,
                                     "Suspicious A value")
            #Calculate u
            u = makeU(N, A, B)

            #Calculate premaster secret
            S = powMod((A * powMod(v,u,N)) % N, b, N)
            premasterSecret = numberToBytes(S)


        #If we've selected an RSA suite, exchange keys and calculate
        #premaster secret:
        elif cipherSuite in CipherSuite.certSuites:

            #Send ServerHello, Certificate[, CertificateRequest],
            #ServerHelloDone
            msgs = []
            serverHello = ServerHello()
            serverHello.create(self.version, getRandomBytes(32),
                        sessionID, cipherSuite, CertificateType.x509)
            msgs.append(serverHello)
            msgs.append(Certificate(CertificateType.x509).create(serverCertChain))
            if reqCert and reqCAs:
                msgs.append(CertificateRequest().create(\
                    [ClientCertificateType.rsa_sign], reqCAs))
            elif reqCert:
                msgs.append(CertificateRequest())
            msgs.append(ServerHelloDone())
            for result in self._sendMsgs(msgs):
                yield result

            #From here on, the client's messages must have the right version
            self._versionCheck = True

            #Get [Certificate,] (if was requested)
            if reqCert:
                if self.version == (3,0):
                    for result in self._getMsg((ContentType.handshake,
                                               ContentType.alert),
                                               HandshakeType.certificate,
                                               CertificateType.x509):
                        if result in (0,1): yield result
                        else: break
                    msg = result

                    if isinstance(msg, Alert):
                        #If it's not a no_certificate alert, re-raise
                        alert = msg
                        if alert.description != \
                                AlertDescription.no_certificate:
                            self._shutdown(False)
                            raise TLSRemoteAlert(alert)
                    elif isinstance(msg, Certificate):
                        clientCertificate = msg
                        if clientCertificate.certChain and \
                                clientCertificate.certChain.getNumCerts()!=0:
                            clientCertChain = clientCertificate.certChain
                    else:
                        raise AssertionError()
                elif self.version in ((3,1), (3,2)):
                    for result in self._getMsg(ContentType.handshake,
                                              HandshakeType.certificate,
                                              CertificateType.x509):
                        if result in (0,1): yield result
                        else: break
                    clientCertificate = result
                    if clientCertificate.certChain and \
                            clientCertificate.certChain.getNumCerts()!=0:
                        clientCertChain = clientCertificate.certChain
                else:
                    raise AssertionError()

            #Get ClientKeyExchange
            for result in self._getMsg(ContentType.handshake,
                                      HandshakeType.client_key_exchange,
                                      cipherSuite):
                if result in (0,1): yield result
                else: break
            clientKeyExchange = result

            #Decrypt ClientKeyExchange
            premasterSecret = privateKey.decrypt(\
                clientKeyExchange.encryptedPreMasterSecret)

            randomPreMasterSecret = getRandomBytes(48)
            versionCheck = (premasterSecret[0], premasterSecret[1])
            if not premasterSecret:
                premasterSecret = randomPreMasterSecret
            elif len(premasterSecret)!=48:
                premasterSecret = randomPreMasterSecret
            elif versionCheck != clientHello.client_version:
                if versionCheck != self.version: #Tolerate buggy IE clients
                    premasterSecret = randomPreMasterSecret

            #Get and check CertificateVerify, if relevant
            if clientCertChain:
                if self.version == (3,0):
                    #Create a temporary session object, just for the purpose
                    #of checking the CertificateVerify
                    session = Session()
                    session._calcMasterSecret(self.version, premasterSecret,
                                             clientHello.random, serverHello.random)
                    verifyBytes = self._calcSSLHandshakeHash(\
                                    session.masterSecret, "")
                elif self.version in ((3,1), (3,2)):
                    verifyBytes = stringToBytes(self._handshake_md5.digest() +\
                                                self._handshake_sha.digest())
                for result in self._getMsg(ContentType.handshake,
                                          HandshakeType.certificate_verify):
                    if result in (0,1): yield result
                    else: break
                certificateVerify = result
                publicKey = clientCertChain.getEndEntityPublicKey()
                if len(publicKey) < settings.minKeySize:
                    postFinishedError = (AlertDescription.handshake_failure,
                        "Client's public key too small: %d" % len(publicKey))
                if len(publicKey) > settings.maxKeySize:
                    postFinishedError = (AlertDescription.handshake_failure,
                        "Client's public key too large: %d" % len(publicKey))

                if not publicKey.verify(certificateVerify.signature,
                                        verifyBytes):
                    postFinishedError = (AlertDescription.decrypt_error,
                                         "Signature failed to verify")


        #Create the session object
        self.session = Session()
        self.session._calcMasterSecret(self.version, premasterSecret,
                                      clientHello.random, serverHello.random)
        self.session.sessionID = sessionID
        self.session.cipherSuite = cipherSuite
        self.session.srpUsername = clientHello.srp_username
        self.session.clientCertChain = clientCertChain
        self.session.serverCertChain = serverCertChain

        #Calculate pending connection states
        self._calcPendingStates(clientHello.random, serverHello.random,
                               settings.cipherImplementations)

        #Exchange ChangeCipherSpec and Finished messages
        for result in self._getFinished():
            yield result

        #If we were holding a post-finished error until receiving the client
        #finished message, send it now.  We delay the call until this point
        #because calling sendError() throws an exception, and our caller might
        #shut down the socket upon receiving the exception.  If he did, and the
        #client was still sending its ChangeCipherSpec or Finished messages, it
        #would cause a socket error on the client side.  This is a lot of
        #consideration to show to misbehaving clients, but this would also
        #cause problems with fault-testing.
        if postFinishedError:
            for result in self._sendError(*postFinishedError):
                yield result

        for result in self._sendFinished():
            yield result

        #Add the session object to the session cache
        if sessionCache and sessionID:
            sessionCache[bytesToString(sessionID)] = self.session

        #Mark the connection as open
        self.session._setResumable(True)
        self._handshakeDone(resumed=False)



    def _serverGetClientHello(self, settings, certChain, verifierDB, srpMust,
                                sessionCache):
        #Initialize acceptable cipher suites
        cipherSuites = []
        if srpMust:
            assert(verifierDB)
        if verifierDB:
            if certChain:
                cipherSuites += \
                    CipherSuite.getSrpCertSuites(settings.cipherNames)
            cipherSuites += CipherSuite.getSrpSuites(settings.cipherNames)        
        if certChain and not srpMust:
            cipherSuites += CipherSuite.getCertSuites(settings.cipherNames)

        #Initialize acceptable certificate type
        if certChain:
            if not isinstance(certChain, X509CertChain):
                ValueError("Unrecognized certificate type")

        #Tentatively set version to most-desirable version, so if an error
        #occurs parsing the ClientHello, this is what we'll use for the
        #error alert
        self.version = settings.maxVersion

        #Get ClientHello
        for result in self._getMsg(ContentType.handshake,
                                   HandshakeType.client_hello):
            if result in (0,1): yield result
            else: break
        clientHello = result

        #If client's version is too low, reject it
        if clientHello.client_version < settings.minVersion:
            self.version = settings.minVersion
            for result in self._sendError(\
                  AlertDescription.protocol_version,
                  "Too old version: %s" % str(clientHello.client_version)):
                yield result

        #If client's version is too high, propose my highest version
        elif clientHello.client_version > settings.maxVersion:
            self.version = settings.maxVersion

        else:
            #Set the version to the client's version
            self.version = clientHello.client_version  
        
        #If resumption was requested and we have a session cache...
        if clientHello.session_id and sessionCache:
            session = None

            #Check in the session cache
            if sessionCache and not session:
                try:
                    session = sessionCache[bytesToString(\
                                               clientHello.session_id)]
                    if not session.resumable:
                        raise AssertionError()
                    #Check for consistency with ClientHello
                    if session.cipherSuite not in cipherSuites:
                        for result in self._sendError(\
                                AlertDescription.handshake_failure):
                            yield result
                    if session.cipherSuite not in clientHello.cipher_suites:
                        for result in self._sendError(\
                                AlertDescription.handshake_failure):
                            yield result
                    if clientHello.srp_username:
                        if clientHello.srp_username != session.srpUsername:
                            for result in self._sendError(\
                                    AlertDescription.handshake_failure):
                                yield result
                except KeyError:
                    pass

            #If a session is found..
            if session:
                #Set the session
                self.session = session

                #Send ServerHello
                serverHello = ServerHello()
                serverHello.create(self.version, getRandomBytes(32),
                                   session.sessionID, session.cipherSuite,
                                   CertificateType.x509)
                for result in self._sendMsg(serverHello):
                    yield result

                #From here on, the client's messages must have the right version
                self._versionCheck = True

                #Calculate pending connection states
                self._calcPendingStates(clientHello.random, serverHello.random,
                                       settings.cipherImplementations)

                #Exchange ChangeCipherSpec and Finished messages
                for result in self._sendFinished():
                    yield result
                for result in self._getFinished():
                    yield result

                #Mark the connection as open
                self._handshakeDone(resumed=True)
                yield None # Handshake done!

        #Calculate the first cipher suite intersection.
        #This is the 'privileged' ciphersuite.  We'll use it if we're
        #doing a new negotiation.  In fact,
        #the only time we won't use it is if we're resuming a
        #session, in which case we use the ciphersuite from the session.
        #
        #Given the current ciphersuite ordering, this means we prefer SRP
        #over non-SRP.
        for cipherSuite in cipherSuites:
            if cipherSuite in clientHello.cipher_suites:
                break
        else:
            for result in self._sendError(\
                    AlertDescription.handshake_failure):
                yield result

        if cipherSuite in CipherSuite.srpAllSuites and not clientHello.srp_username:
            for result in self._sendError(\
                    AlertDescription.unknown_psk_identity,
                    "Client sent a hello, but without the SRP username"):
                yield result
                
        # If resumption was not requested, or
        # we have no session cache, or
        # the client's session_id was not found in cache:
        yield (clientHello, cipherSuite)






    def _handshakeWrapperAsync(self, handshaker, checker):
        if not self.fault:
            try:
                for result in handshaker:
                    yield result
                if checker:
                    try:
                        checker(self)
                    except TLSAuthenticationError:
                        alert = Alert().create(AlertDescription.close_notify,
                                               AlertLevel.fatal)
                        for result in self._sendMsg(alert):
                            yield result
                        raise
            except GeneratorExit:
                raise
            except:
                self._shutdown(False)
                raise
        else:
            try:
                for result in handshaker:
                    yield result
                if checker:
                    try:
                        checker(self)
                    except TLSAuthenticationError:
                        alert = Alert().create(AlertDescription.close_notify,
                                               AlertLevel.fatal)
                        for result in self._sendMsg(alert):
                            yield result
                        raise
            except socket.error, e:
                raise TLSFaultError("socket error!")
            except TLSAbruptCloseError, e:
                raise TLSFaultError("abrupt close error!")
            except TLSAlert, alert:
                if alert.description not in Fault.faultAlerts[self.fault]:
                    raise TLSFaultError(str(alert))
                else:
                    pass
            except GeneratorExit:
                raise
            except:
                self._shutdown(False)
                raise
            else:
                raise TLSFaultError("No error!")


    def _clientGetKeyFromChain(self, certificate, settings):
        #Get and check cert chain from the Certificate message
        certChain = certificate.certChain
        if not certChain or certChain.getNumCerts() == 0:
            for result in self._sendError(AlertDescription.illegal_parameter,
                    "Other party sent a Certificate message without "\
                    "certificates"):
                yield result

        #Get and check public key from the cert chain
        publicKey = certChain.getEndEntityPublicKey()
        if len(publicKey) < settings.minKeySize:
            for result in self._sendError(AlertDescription.handshake_failure,
                    "Other party's public key too small: %d" % len(publicKey)):
                yield result
        if len(publicKey) > settings.maxKeySize:
            for result in self._sendError(AlertDescription.handshake_failure,
                    "Other party's public key too large: %d" % len(publicKey)):
                yield result

        yield publicKey, certChain
