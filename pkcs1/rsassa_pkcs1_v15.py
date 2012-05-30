import emsa_pkcs1_v15
import primitives
import exceptions

def sign(private_key, message):
    '''Produce a signature of string using a RSA private key and PKCS#1.5
       padding.

       Parameters:

       private_key - a RSA private key
       message - a string to sign

       Result:
       the signature string
    '''

    em = emsa_pkcs1_v15.encode(message, private_key.k)
    m = primitives.os2ip(em)
    s = private_key.rsasp1(m)
    return primitives.i2osp(s, private_key.k)

def verify(public_key, message, signature):
    '''Verify a signature of a message using a RSA public key and PKCS#1.5
       padding.

       Parameters:

       public_key - a RSA public key
       message - the signed string
       signature - the signature string

       Result:
       True if the signature matches the message, False otherwise.
    '''
    if len(signature) != public_key.k:
        raise exceptions.InvalidSignature
    s = primitives.os2ip(signature)
    try:
        m = public_key.rsavp1(s)
    except ValueError:
        raise exceptions.InvalidSignature
    try:
        em = primitives.i2osp(m, public_key.k)
    except ValueError:
        raise exceptions.InvalidSignature
    try:
        em_prime = emsa_pkcs1_v15.encode(message, public_key.k)
    except ValueError:
        raise exceptions.RSAModulusTooShort
    return primitives.constant_time_cmp(em, em_prime)
