import operator

import math
import fractions
import keys

from defaults import default_crypto_random

try:
    import gmpy
except ImportError:
    gmpy = None

from primes import get_prime, DEFAULT_ITERATION
import exceptions


'''Primitive functions extracted from the PKCS1 RFC'''

def _pow(a, b, mod):
    '''Exponentiation function using acceleration from gmpy if possible'''
    if gmpy:
        return long(pow(gmpy.mpz(a), gmpy.mpz(b), gmpy.mpz(mod)))
    else:
        return pow(a, b, mod)

def integer_ceil(a, b):
    '''Return the ceil integer of a div b.'''
    quanta, mod = divmod(a, b)
    if mod:
        quanta += 1
    return quanta

def integer_byte_size(n):
    '''Returns the number of bytes necessary to store the integer n.'''
    quanta, mod = divmod(integer_bit_size(n), 8)
    if mod or n == 0:
        quanta += 1
    return quanta

def integer_bit_size(n):
    '''Returns the number of bits necessary to store the integer n.'''
    if n == 0:
        return 1
    s = 0
    while n:
        s += 1
        n >>= 1
    return s

def bezout(a, b):
    '''Compute the bezout algorithm of a and b, i.e. it returns u, v, p such as:

          p = GCD(a,b)
          a * u + b * v = p

       Copied from http://www.labri.fr/perso/betrema/deug/poly/euclide.html.
    '''
    u = 1
    v = 0
    s = 0
    t = 1
    while b > 0:
        q = a // b
        r = a % b
        a = b
        b = r
        tmp = s
        s = u - q * s
        u = tmp
        tmp = t
        t = v - q * t
        v = tmp
    return u, v, a

def i2osp(x, x_len):
    '''Converts the integer x to its big-endian representation of length
       x_len.
    '''
    if x > 256**x_len:
        raise exceptions.IntegerTooLarge
    h = hex(x)[2:]
    if h[-1] == 'L':
        h = h[:-1]
    if len(h) & 1 == 1:
        h = '0%s' % h
    x = h.decode('hex')
    return '\x00' * int(x_len-len(x)) + x

def os2ip(x):
    '''Converts the byte string x representing an integer reprented using the
       big-endian convient to an integer.
    '''
    h = x.encode('hex')
    return int(h, 16)

def string_xor(a, b):
    '''Computes the XOR operator between two byte strings. If the strings are
       of different lengths, the result string is as long as the shorter.
    '''
    return ''.join((chr(ord(x) ^ ord(y)) for (x,y) in zip(a,b)))

def product(*args):
    '''Computes the product of its arguments.'''
    return reduce(operator.__mul__, args)

def generate_key_pair(size=512, number=2, rnd=default_crypto_random, k=DEFAULT_ITERATION,
        primality_algorithm=None, strict_size=True, e=0x10001):
    '''Generates an RSA key pair.

       size:
           the bit size of the modulus, default to 512.
       number:
           the number of primes to use, default to 2.
       rnd:
           the random number generator to use, default to SystemRandom from the
           random library.
       k:
           the number of iteration to use for the probabilistic primality
           tests.
       primality_algorithm:
           the primality algorithm to use.
       strict_size:
           whether to use size as a lower bound or a strict goal.
       e:
           the public key exponent.

       Returns the pair (public_key, private_key).
    '''
    primes = []
    lbda = 1
    bits = size // number + 1
    n = 1
    while len(primes) < number:
        if number - len(primes) == 1:
            bits = size - integer_bit_size(n) + 1
        prime = get_prime(bits, rnd, k, algorithm=primality_algorithm)
        if prime in primes:
            continue
        if e is not None and fractions.gcd(e, lbda) != 1:
            continue
        if strict_size and number - len(primes) == 1 and integer_bit_size(n*prime) != size:
            continue
        primes.append(prime)
        n *= prime
        lbda *= prime - 1
    if e is None:
        e = 0x10001
        while e < lbda:
            if fractions.gcd(e, lbda) == 1:
                break
            e += 2
    assert 3 <= e <= n-1
    public = keys.RsaPublicKey(n, e)
    private = keys.MultiPrimeRsaPrivateKey(primes, e, blind=True, rnd=rnd)
    return public, private

def get_nonzero_random_bytes(length, rnd=default_crypto_random):
    '''
       Accumulate random bit string and remove \0 bytes until the needed length
       is obtained.
    '''
    result = []
    i = 0
    while i < length:
        l = rnd.getrandbits(12*length)
        s = i2osp(l, 3*length)
        s = s.replace('\x00', '')
        result.append(s)
        i += len(s)
    return (''.join(result))[:length]

def constant_time_cmp(a, b):
    '''Compare two strings using constant time.'''
    result = True
    for x, y in zip(a,b):
        result &= (x == y)
    return result

import textwrap

def dump_hex(data):
    if isinstance(data, basestring):
        print 'length', len(data)
        print textwrap.fill(''.join(['%s ' % x.encode('hex') for x in data]), 72)
