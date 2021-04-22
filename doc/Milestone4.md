Now that you can create AST and Symbol Table for a semantically meaningful program, it is time to generate Intermediate code (3-address code, 3AC) with support for run-time activations.

The structure of the activation record must include:
- space for the return value
- space for parameters
- space for old stack pointers to pop an activation
- space for locals
- space for saved registers
- any other fields required by your particular language/target

How to lay them out is your choice but keep it close to the conventions used by the assembler for your target architecture. It will help you generate code that you can run eventually :-)

For the Intermediate code, the preferred choice is 3AC as it is the only form discussed in detail in class. However, you may need additional instructions to suit your compiler's needs. Practically, for some targets, 3AC may not be a suitable choice (for example, JVM and other stack machines). In case you think you need to use some other IR, discuss it with the instructor at the earliest.