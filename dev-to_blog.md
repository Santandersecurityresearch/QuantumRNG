# QuantumRNG-aaS - Harnessing quantum algorithms for useful services

We have all heard the hype...

_"Quantum Computers are gonna break everything!!"_

_"Quantum is coming... the wind is blowing..."_

In a world where 'quantum' is equally likely to be used to sell you [dishwasher tablets](https://www.amazon.co.uk/Finish-Quantum-Ultimate-Dishwasher-Tablets/dp/B07MM5LRDL) or [toilet paper](https://www.amazon.co.uk/Quantum-Luxury-Supreme-Quilted-Cushion/dp/B07CRC65TR), as much as it is to be used as a way to scare people with headlines like "[Quantum Computing and the End of Encryption](https://hackaday.com/2020/06/11/quantum-computing-and-the-end-of-encryption/)" (really, really not helpful, Hackaday...) there is now somewhat of a skills rush to be able to have technicians who can make sense of this bold new world of quantum computing. 

What this Hacktober project will demonstrate is the following:
* That quantum computing is certainly within the understanding of most of us
* Cloud quantum offerings can be implemented into real-world systems beyond the realm of 'novelty'
* With the right approach, a quantum circuit can be used to provide something actually useful for modern applications.

**TL;DR** - we're going to work through the theory to arrive at [this proof of concept](https://gist.github.com/unprovable/437561c660f7d85f283e510a16ef5834) - and then offer up the model that we can build up and collaboratively code as part of the Hacktober activities so that we can arrive at a pretty cool output: Quantum-RNG-as-a-Service! \#QRNGaaS

**DISCLAIMER** - this code is **NOT** for use in production systems without a significant amount of extra engineering and checking. YMMV and Caveat Developer!!

# Primer on Quantum Algorithms

It's impossible to do much with quantum computers at the moment without delving into some deep-tech ideas of what is going on at the fundamental level of a quantum computer - principally discussing the idea of a 'qubit'.

But why do we have to do this? Well, the reason is that quantum computers are much closer to a Z80 processor than they are to a modern Intel i9. And like with the Z80, in order to make them workable, you have to have a good idea what is going on deep under the hood. One day we will have a wonderful, iterative abstraction model for quantum computing - but sadly, that day is not today! 

## So what **isn't** a quantum computer?

Put simply, a quantum computer is __not__ 'just a faster computer'! Quantum algorithms operate in a totally different way to regular, 'classical', computers.

You're not gonna get MS Flight Sim running any better with quantum computers - especially not as they are right now! Quantum computers are still specialist pieces of equipment.

**NB** - our emphasis for 'quantum computing' here is on the 'computing' rather than the 'quantum' part... so we'll keep this bit brief :P

## So what's the big deal?

The fundamental deal is that quantum technologies (usually, but not exclusively) make use of two quantum effects:
* **Superposition** - the idea that a particle is in a combination of states simultaneously.
* **Entanglement** - the idea that two particles can be, in some strict mathematical sense, inseparable to the point that a measurement of one gives you some facts about the other (without measuring it first).

This leads us to the next question - how do you actually do this? 

Well, first up, let's discuss the structure of a qubit in comparison to a regular 'bit'. A bit is just a one or a zero - and it is always exactly one OR the other, NEVER both. A qubit, however, can be in some superposition of the 'zero state' and the 'one state' - when you measure it, you will always get just a '1' or a '0' as your output, just like a bit. The difference is that it can be _either_ 0 or 1, with some _probability_ of being one or the other across many measurements.

To understand this better - take a look at the following diagram:

![The Bloch Sphere - CC Wikipedia](https://dev-to-uploads.s3.amazonaws.com/i/lsh3ae21umujgni95862.png)

This is called the 'Bloch Sphere' - and it represents the 'sphere' of possibilities for the position of a qubit's _state_, which we usually write as |ψ⟩. 

Now, we do have to do a little maths - as we can't just have any old values wandering around - they won't stay on the surface of the sphere! So, we need to define what |ψ⟩ is - let x and y be complex numbers (that is, of the form m+in where i is the imaginary constant, and m and n are whole numbers), then we say that |ψ⟩ = a|0⟩ + b|1⟩, letting |0⟩ be the column vector (1,0), and |1⟩ be the column vector (0,1). We only require that |a|^2 + |b|^2 = 1 (to preserve the probabilities of the system and keep the tip of the state vector |ψ⟩ on the sphere surface). 

I'm not going to go into things like unitary gates, the 4 postulates of quantum mechanics, linear algebra, inner/outer products, tensor products, seperable states, etc. etc. - if you would like a reasonable primer, look at [these slides](https://www.cl.cam.ac.uk/teaching/0910/QuantComp/notes.pdf).

Before we go on - here's an **emergency post-mathematics kitten**:

![Post-mathematics kitten - CC Wikipedia](https://dev-to-uploads.s3.amazonaws.com/i/n6sw4m5p4ikjsdno1sip.jpg)

## Building things for multiple qubits...

Now, this was actually important for the next piece of the puzzle - how you program a quantum computer! Because everything is now reducible to two-place column vectors that have nice properties - we can now manipulate them easily with 2x2 matrices! This is exactly what forms _quantum gates_. 

But what do we mean by 'quantum gate'? Well, classical computers have logic gates; AND, OR, NOT, NOR, NAND, XOR, etc. which are placed in various combinations to make computer programs. All of our computation is fundamentally reducible to these gates.

In the same way, a quantum algorithm is formed from the composition of quantum gates, these 2x2 matrices, in sequences we call 'quantum circuits' (analogous to 'boolean circuits' for those familiar with them).

## Our first Quantum Circuit!

What do these quantum circuits look like? Well, we can see an example here: 

![Basic Circuit](https://dev-to-uploads.s3.amazonaws.com/i/bjufwhl32111w82m5f2d.png)

We assume that on the far left, all qubits are set to |0⟩ (with the vector pointing up on the sphere). Now we can apply gates - and some of these gates have special names;
* the circular blue gate with an '+' in the middle is called the 'Pauli X' - this flips the gate from |0⟩ to |1⟩ or a similar inversion if the qubit vector |ψ⟩ isn't wholly up or down.
* The red gate with a 'H' is called the Hadamard Gate, and this serves to put the qubit into superposition - more on this later!
* The circular blue '+' with a tie to an upper qubit is called a CNOT gate - this is a very cool gate that is involved with entanglement and other cool operations on a quantum computer, but which we'll skip over here. 
* The black box with a vertical line is the 'measurement' gate. 

For the ultimate output, the classical bit 'buffer' is the lowest line in these diagrams - and when we measure qubits we get either a 0 or a 1, and these are placed into the buffer sequentially.

So how do we get an output? Well, the quantum computer will run our circuit more than once, and give us a graph of the outputs - so when I ran the above I got the following output graph:

![Output Histogram](https://dev-to-uploads.s3.amazonaws.com/i/xvh4h5ml0tysal9dmmex.png)

You will notice that we 'almost always' got a '11' (which if you check the matrices is what we should have gotten) but there is just over 13% of the outputs that were the other three possible states for 2 qubits. This inherent noise is why quantum computers such as these that don't do quantum error correction are called 'Noisy Intermediate Scale Quantum computers' or NISQs. 

**NB** - There is also a Quantum Assembly language called QASM! For the above circuit, it looks like this:
```
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];

x q[1];
h q[0];
h q[1];
cx q[0],q[1];
h q[0];
h q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
```
It is also worth mentioning that the above circuit is not what is actually run - the commercial quantum computers implement a reduced set of gates that are equivalent under combinations to every theoretical gate. This transpiling is very common - for the above circuit, the transpiled circuit looks like this: 

![Transpiled Quantum Circuit](https://dev-to-uploads.s3.amazonaws.com/i/eptrrxh3ibegdcngj9d6.png)

## Quick aside - resources

I'm skipping over MANY details here, so if you want to learn more have a look at these resources:
* [Qiskit Documentation](https://qiskit.org/documentation/) - This has many excellent pages covering the basics of quantum gates, but also in-line summaries of the matrix and vector stuff in case that is a little rusty. A really good resource!
* [Quantiki](https://quantiki.org) - a really good website with lots of details and descriptions of various quantum algorithms and their uses!

# Building Something Useful

You'll note that I didn't explain what was really going on in the circuit above - it's not that important (it is a circuit that is equivalent to an inverted CNOT, part of the Bernstein-Vazarani algorithm, for the curious). But the next bit will require us to go into some depth - we're going to show how to acquire some of the best quantum-ly random bits from a quantum computer! We can then use these to fold into a local entropy pool for generating random numbers. 

## Quantum Supremacy and Randomness

When [Google announced quantum supremacy](https://www.nature.com/articles/s41586-019-1666-5) what they had achieved was the measurement of randomness in a few hundred seconds that would take a supercomputer 10,000 years to perform the same fidelity of operation. This is a similar process that companies such as [Cambridge Quantum Computing](https://sifted.eu/articles/finally-a-way-to-make-money-out-of-quantum-selling-randomness/) use (we presume, anyway) to measure the randomness of a source and help it be 'better' randomness. 

## But who cares about this?

Who would find this useful? Well - consider the following clients and use cases:
* Anyone generating keys or doing cryptography will always need good entropy seeds, and quantum is one of the best sources.
* Anyone doing financial simulations and modelling (such as Monte Carlo sims)
* Anyone doing AI/ML model generation will need _plenty_ of good quality randomness.
* Gaming applications - obviously, when you roll a die in a game, you don't want it being predictable! The gaming industry has very strict requirements on randomness for its purposes.

## Our Grand Design

We are not going to do anything so fancy here - we will, however, use the following algorithm:
1. Put a sequence of qubits into superposition with a Hadamard gate
  * This means each qubit has a balanced probability of 1/2 of going into state 0 or 1 on output, which is our source of randomness.
1. Take this output, and blend it with our local randomness entropy pool.
1. Use this pool to seed a CSPRNG (Cryptographically Secure Pseudo-Random Number Generator) that can generate random numbers very quickly for general use. 

The rough block diagram is here: 
![QRNGaaS Block Diagram](https://dev-to-uploads.s3.amazonaws.com/i/c55fagr6ufymdvjdpl3p.png)

So we will setup a background job to use the IBM-Q python API in qiskit, and whilst we wait, we will generate random numbers on the fly for as long/as many as we need to provide. 

So what does our circuit look like? Well, something like this:
![QRNG circuit](https://dev-to-uploads.s3.amazonaws.com/i/tgd85m5uwlyepdutxlwg.png)

Now, we note the following calculation:
* The 15 maximum qubits on the `ibmq_16_melbourne` quantum computer means that we can run for 15 random bits of output for each shot. 
* The max number of shots is 8,192 (2^14).
* This means that we can get up to 15*8192 = 122,880 bits in the output!
* These aren't secret, as IBM can also know these bits, so we will blend them with local randomness that we can assume is known only to us for this use case. 
  * It is important that any input into the RNG is not widely known, else we may compromise our random numbers!
  * For this, we will use SHA3 (Keccak) hashing to keep things as high-entropy as possible. This is a PQC algorithm with a large internal state, so this should maintain a good level of security.

And this is the core of our service! 😁

## But what is there to hack? 

Well, so far - this just shows how to generate random numbers locally from a class with the background process occasionally asking IBM-Q very nicely! (NB - you'll need an IBM-Q account and API token for the script, but these are free!!)

What can we build? Well, consider the following:
* MQTT randomness source - there are projects such as [Entropy Broker](https://www.vanheusden.com/entropybroker/) that allow you to 'import' entropy from various sources. We can maybe write these to support MQTT and then distribute randomness across a network (with appropriate levels of security, ofc!) to better seed local entropy pools.
* A Randomness API! - We could build a python API that would allow us to provide high-quality randomness derived from our beautiful quantum-ly random bits to anyone who asks, in bulk, and at scale!

Or anything else you can think of to get good quality randomness to those who need it! 

## Show us the money!

For those who want to see a PoC flask-based API service (only two endpoints, but it should be quite illustrative) then have a look at the following github repo:

{% github Santandersecurityresearch/QuantumRNG no-readme %} 

But if you want an all-in-one script to play with, we have that, too! Now I have discussed the base theory - here is the proof-of-concept script! 

{% gist https://gist.github.com/unprovable/437561c660f7d85f283e510a16ef5834 %}

Special thanks to Dr. Joe Wilson ([@jmaw88](https://twitter.com/jmaw88)) for his help in proofreading this post. :)