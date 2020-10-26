__author__ = "Mark Carney aka @LargeCardinal"
__copyright__ = "The Author"
__license__ = "MIT"
__status__ = "Proof of Concept - NOT FOR PRODUCTION"

import qiskit 
from qiskit import IBMQ

import math
import sympy
import secrets

import threading
import hashlib

import yaml


class QuantumRNG(object):
    def __init__(self, ibmqx_token='', ibm_token_file='ibm_secret.yml'):
        self.sys_rng = secrets.SystemRandom()   
        self.qc_entropy_pool = "{0:b}".format(self.sys_rng.randrange(3*10**100,4*10**100))
        self.seed = secrets.randbelow(5*10**100)
        # prepare the first seeds and fix the random primes
        # for the CSPRNG
        x = self.sys_rng.randrange(3*10**100, 4*10**100)
        y = self.sys_rng.randrange(3*10**100, 4*10**100)
        self.p = self.next_usable_prime(x)
        self.q = self.next_usable_prime(y)
        self.reseed_count = 0
        self.reseed_threshold = 10**7 #reseed every 10 million bits - reduce this to test the IBMQ integration. -MC
        # do qiskit-y stuff
        # get the API token
        with open (ibm_token_file) as secret_file:
            ibm_secrets = yaml.load(secret_file, Loader=yaml.FullLoader)
            ibmqx_token = ibm_secrets['ibm_api_key']
        self.provider = self.set_ibmq_provider(ibmqx_token)
        self.rng_circuit = self.make_circuit(15)
        self.ibmq_backend = self.provider.get_backend('ibmq_16_melbourne')

    
    # small CSPRNG from here: https://www.johndcook.com/blog/2017/09/21/a-cryptographically-secure-random-number-generator/
    # tweaked to match the original paper (not using mod 2, but the proper parity of the output from x*x mod M)
    # the Blum-Blum-Shub algorithm has some critical analysis here - https://arxiv.org/pdf/1811.06418.pdf
    # original is here: https://pdfs.semanticscholar.org/c19b/91cdc1da67c52e606cd4752472ce0db83131.pdf

    def next_usable_prime(self, x):
        # Find the next prime congruent to 3 mod 4 following x.
        p = sympy.nextprime(x)
        while (p % 4 != 3):
            p = sympy.nextprime(p)
        # Check the seed mod p isn't 0...
        if self.seed % p == 0:
            p = self.next_usable_prime(p+1)
        return p
        
    def get_rand_bitstring(self, N=64):
        M = self.p*self.q
        #print("count is {0}".format(self.reseed_count))
        if self.reseed_count > self.reseed_threshold:
            self.do_update_entropy()
        x = self.seed
        bit_string = ""
        for _ in range(N):
            x = x*x % M
            # Turns out we probably don't need the fancy parity, 
            # just odd/even parity will do. -MC
            b = x % 2
            bit_string += str(b)
        # update the seed
        self.seed = x
        # update bit count
        self.reseed_count += N
        if self.reseed_count % 8192 == 0:
            print("[i] Random bits at count {0} are: {1}".format(self.reseed_count, bit_string))
        return bit_string

    def get_rand_bytes(self, N=64):
        bitstring = self.get_rand_bitstring(N=N)
        v = int(bitstring, 2)
        b = bytearray()
        while v:
            b.append(v & 0xff)
            v >>= 8
        return bytes(b[::-1])
    
    def update_seed(self, new_seed):
        self.seed = new_seed
        return
    
    def do_update_entropy(self):
        #print("doing entropy update...")
        # use system entropy in times of need
        if len(self.qc_entropy_pool) < 512:
            # Just copying bits from the local entropy pool for now... Not very elegant :-/ -MC
            local_bits = "{0:b}".format(self.sys_rng.randrange(2*10**100, 3*10**100))
            self.qc_entropy_pool += local_bits
            print("[!] Added {0} bits from local entropy pool...".format(len(local_bits)))
        if len(self.qc_entropy_pool) < 1025: # we don't want to call too much...
            # use background thread to get quantum bits... Get 1024 bits in 15-bit chunks across so many shots on the QC. -MC
            # the queues might be long, so we just have to wait...
            get_qc_thread = threading.Thread(target=self.get_quantum_bits, name="IBM-QX Computation", args=(1024,))
            get_qc_thread.start()
        # consume 64-bits of entropy...
        self.seed += int(self.qc_entropy_pool[:256],2)
        # remove the bits we used...
        self.qc_entropy_pool = self.qc_entropy_pool[256:]
        print("[!] Remaining bits in entropy pool: {0}".format(len(self.qc_entropy_pool)))
        # reset the count
        self.reseed_count = 0
        return
    
    # IBM-QX stuff inspired by: https://github.com/ozanerhansha/qRNG/ 
    def set_ibmq_provider(self, ibmqx_token):
        if ibmqx_token == '':
            provider = qiskit.BasicAer
        else: 
            IBMQ.save_account(ibmqx_token, overwrite=True)
            IBMQ.load_account()
            provider = IBMQ.get_provider('ibm-q')
        return provider
    
    def make_circuit(self, n=15):
        # This quantum circuit takes n-many qubits, and then puts them into 
        # superposition with a Hadamard operation (transpiled to a Z-rotation, usually).
        # We then measure each qubit and put the ouputs into a register of n-bits in length
        # and then return that back. -MC
        qr = qiskit.QuantumRegister(n)
        cr = qiskit.ClassicalRegister(n)
        circ = qiskit.QuantumCircuit(qr, cr)
        circ.h(qr) 
        circ.measure(qr,cr)
        return circ
    
    def get_bits_from_counts(self, counts):
        bits = ""
        for i in [k for k, v in counts.items() if v == 1]:
            bits += i
        return bits
    
    def run_ibmq_circuit(self, shots=35):
        # our circuit will have 2^n bits of entropy of output, but the maxmimum number of shots allowed
        # on the big IBMQ 16-qubit machine in Melbourne is 2^14... so in theory we can run this 
        # up to 2^14 times, and get 15 bits each time with little risk of things overlapping! 
        # (Why? Because pigeonhole principle, and random...)
        # Thus in one job we can theoretically get up to 122,880 (15*8292) bits of good, pure,
        # quantumly-derived entropy! :-D The only problem; it isn't secret to us...
        if self.ibmq_backend.remaining_jobs_count() > 4:
            # if enough jobs are left en queue...
            job = qiskit.execute(self.rng_circuit, self.ibmq_backend, shots=shots)
            bits = self.get_bits_from_counts(job.result().get_counts())
        else:
            print("[!] No free jobs - using system randomnes...")
            #return some system-y randomness
            bits = "{0:b}".format(self.sys_rng.randrange(2*10**100, 3*10**100))
        return bits
    
    def get_quantum_bits(self, n=512):
        print("[*] running bg IBMQ process")
        # default to get ceil(512/15) random bits from QC ...
        numshots = math.ceil(n/self.rng_circuit.width()*2)
        # go get the quantum! -MC
        bits_from_qc = self.run_ibmq_circuit(shots=numshots)
        # hash everything to make the most of the quantum :P
        current_e_pool = self.qc_entropy_pool
        # clear the pool.. or not -MC
        #self.qc_entropy_pool = ""
        m = hashlib.sha3_512()
        # Mixing it up twice by hashing the new bits and the old pool both ways...
        # This is basically using Keccak as an 'entropy expander' twice. 
        # Reason for this is that our quantumly random bits aren't secret to only us,
        # and the entropy may be mismatched with our local os.urandom output, 
        # so this should normalise it. :-) -MC
        for i in range(math.floor(len(bits_from_qc)/512)):
            m.update(str(current_e_pool + bits_from_qc[i*512:(i+1)*512]).encode('utf-8'))
            self.qc_entropy_pool += ''.join(format(byte, '08b') for byte in m.digest())
        m.update(str(bits_from_qc + current_e_pool).encode('utf-8'))
        self.qc_entropy_pool += ''.join(format(byte, '08b') for byte in m.digest())
        print("[i] Updated the entropy pool with {0} bits from IBMQ, {1} bits after hashing...".format(len(bits_from_qc),(math.floor(len(bits_from_qc)/512)+1)*512))
        return
    

