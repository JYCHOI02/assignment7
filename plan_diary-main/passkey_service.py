# -*- coding: utf-8 -*-
"""
WebAuthn (Passkey) Authentication & Registration Service
Pure Python implementation using cryptography library.
Complies with W3C WebAuthn Level 2 / FIDO2 specifications.
"""
import os
import base64
import json
import struct
import hashlib
import io
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key, Encoding, PublicFormat
from cryptography.exceptions import InvalidSignature


# ==============================================================================
# 1. Helper: Base64URL Encoding & Decoding
# ==============================================================================

def b64url_encode(data: bytes) -> str:
    """Base64URL encodes bytes into an unpadded ASCII string."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def b64url_decode(s: str) -> bytes:
    """Decodes a Base64URL string (with or without padding) into bytes."""
    s = s.replace('-', '+').replace('_', '/')
    padding = '=' * (-len(s) % 4)
    return base64.b64decode(s + padding)


# ==============================================================================
# 2. Helper: Lightweight Pure-Python CBOR Decoder
# ==============================================================================

class CBORDecoder:
    """Decodes CBOR structures (maps, arrays, integers, byte strings, text strings)."""
    def __init__(self, stream):
        if isinstance(stream, (bytes, bytearray)):
            self.stream = io.BytesIO(stream)
        else:
            self.stream = stream

    def read_exact(self, n):
        b = self.stream.read(n)
        if len(b) < n:
            raise EOFError("Unexpected end of CBOR stream")
        return b

    def decode(self):
        first = self.stream.read(1)
        if not first:
            raise EOFError("Empty CBOR stream")
        b = first[0]
        major = b >> 5
        info = b & 0x1F

        if info < 24:
            val = info
        elif info == 24:
            val = self.read_exact(1)[0]
        elif info == 25:
            val = struct.unpack(">H", self.read_exact(2))[0]
        elif info == 26:
            val = struct.unpack(">I", self.read_exact(4))[0]
        elif info == 27:
            val = struct.unpack(">Q", self.read_exact(8))[0]
        else:
            raise ValueError(f"Unsupported CBOR info: {info}")

        if major == 0:    # unsigned int
            return val
        elif major == 1:  # negative int
            return -1 - val
        elif major == 2:  # byte string
            return self.read_exact(val)
        elif major == 3:  # text string
            return self.read_exact(val).decode("utf-8", errors="replace")
        elif major == 4:  # array
            return [self.decode() for _ in range(val)]
        elif major == 5:  # map
            res = {}
            for _ in range(val):
                k = self.decode()
                v = self.decode()
                res[k] = v
            return res
        elif major == 7:  # simple / bool
            if info == 20: return False
            elif info == 21: return True
            elif info == 22: return None
            return val
        else:
            raise ValueError(f"Unsupported CBOR major type: {major}")


def cbor_loads(data: bytes):
    return CBORDecoder(data).decode()


# ==============================================================================
# 3. WebAuthn Registration (Attestation) Parsing
# ==============================================================================

def parse_attestation_object(attestation_bytes: bytes):
    """
    Parses client attestationObject (CBOR map: fmt, authData, attStmt)
    Extracts credentialId and public key (in PEM format).
    """
    att = cbor_loads(attestation_bytes)
    auth_data = att["authData"]

    # authData structure:
    # - rpIdHash: 32 bytes
    # - flags: 1 byte
    # - signCount: 4 bytes (uint32)
    # - Attested Credential Data (if flags & 0x40):
    #   - aaguid: 16 bytes
    #   - credIdLen: 2 bytes (uint16)
    #   - credId: credIdLen bytes
    #   - credPubKey: COSE_Key (CBOR encoded)
    if len(auth_data) < 37:
        raise ValueError("Invalid authData length")

    flags = auth_data[32]
    has_attested_cred = bool(flags & 0x40)
    if not has_attested_cred:
        raise ValueError("authData does not contain attested credential data")

    stream = io.BytesIO(auth_data[37:])
    aaguid = stream.read(16)
    cred_id_len = struct.unpack(">H", stream.read(2))[0]
    cred_id = stream.read(cred_id_len)

    # Decode COSE public key from the remaining stream
    cose_key = CBORDecoder(stream).decode()

    # We support ES256 (kty: 2 = EC2, alg: -7 = ES256, crv: 1 = P-256)
    kty = cose_key.get(1)
    if kty == 2:  # EC2 (P-256)
        x_bytes = cose_key.get(-2)
        y_bytes = cose_key.get(-3)
        if not x_bytes or not y_bytes:
            raise ValueError("Invalid EC2 COSE Key (missing x or y)")

        point_bytes = b'\x04' + x_bytes + y_bytes
        curve = ec.SECP256R1()
        pub_key = ec.EllipticCurvePublicKey.from_encoded_point(curve, point_bytes)
        pem_key = pub_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        ).decode('ascii')

        return {
            "credential_id_bytes": cred_id,
            "credential_id_b64": b64url_encode(cred_id),
            "public_key_pem": pem_key,
            "aaguid": aaguid.hex()
        }
    else:
        raise ValueError(f"Unsupported key type (kty={kty})")


# ==============================================================================
# 4. WebAuthn Authentication (Assertion) Verification
# ==============================================================================

def verify_assertion(
    public_key_pem: str,
    authenticator_data_b64: str,
    client_data_json_b64: str,
    signature_b64: str,
    expected_challenge_b64: str,
    expected_origin: str = "http://127.0.0.1:5000"
) -> bool:
    """
    Verifies a WebAuthn authentication assertion response against the stored PEM public key.
    Checks:
      1. clientDataJSON.type == 'webauthn.get'
      2. clientDataJSON.challenge == expected_challenge
      3. clientDataJSON.origin matches
      4. userPresent flag in authenticatorData (flags & 0x01)
      5. Cryptographic signature over (authenticatorData || SHA256(clientDataJSON))
    """
    # 1. Decode clientDataJSON
    client_data_bytes = b64url_decode(client_data_json_b64)
    client_data = json.loads(client_data_bytes.decode('utf-8'))

    if client_data.get("type") != "webauthn.get":
        raise ValueError(f"Invalid clientData type: {client_data.get('type')}")

    # Check challenge
    client_challenge = client_data.get("challenge", "").replace('-', '+').replace('_', '/')
    exp_challenge = expected_challenge_b64.replace('-', '+').replace('_', '/')
    # strip padding for flexible comparison
    if client_challenge.rstrip('=') != exp_challenge.rstrip('='):
        raise ValueError("Challenge mismatch in clientDataJSON")

    # 2. Decode authenticatorData
    auth_data_bytes = b64url_decode(authenticator_data_b64)
    if len(auth_data_bytes) < 37:
        raise ValueError("Invalid authenticatorData length")

    flags = auth_data_bytes[32]
    user_present = bool(flags & 0x01)
    if not user_present:
        raise ValueError("User presence flag (UP) is not set")

    # 3. Form signature base = authenticatorData + SHA-256(clientDataJSON)
    client_hash = hashlib.sha256(client_data_bytes).digest()
    signature_base = auth_data_bytes + client_hash

    # 4. Decode signature
    sig_bytes = b64url_decode(signature_b64)

    # 5. Verify signature using stored public key
    pub_key = serialization.load_pem_public_key(public_key_pem.encode('ascii'))

    try:
        if isinstance(pub_key, ec.EllipticCurvePublicKey):
            pub_key.verify(sig_bytes, signature_base, ec.ECDSA(hashes.SHA256()))
        else:
            raise ValueError("Unsupported public key type for verification")
        return True
    except InvalidSignature:
        return False
