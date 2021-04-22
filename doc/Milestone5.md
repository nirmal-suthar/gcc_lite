In this last part of the assignment, you will generate code for the target assembly. For initial ideas regarding code generation, you can read section 8.6 of the dragon book. This is titled "A simple code generator". We shall cover this chapter in the lectures.

The primary requirement of your code generator is correctness. The next requirement is completeness—all compulsory features should be implemented in a general sense. For instance, your code generator should not fail because an expression was too large and you could not find enough registers to hold intermediate values during its evaluation, or because some function called in the code was declared, but not defined (the code may not assemble/run if the definition is never supplied, though).

Going beyond the basic features may earn you bonus points. If you design and implement a code generator that you can argue to be more efficient, that will win you bonus points. You must have examples to demonstrate these extra features during the final presentation.

Later next week I will supply you with features that you are compiler is expected to implement. You write the tests covering these features in the source language. This will help you document any restrictions in your implementation. You can add other tests to demonstrate any feature you have implemented, but are not covered here. TAs will also write the test programs covering these features to test your compiler during the final demo. Again, it is not necessary that your compiler implement all features, but it should give a decent error message and not crash for something not implemented.

It is very important that you are ready with the test cases to show the features of your compiler during the presentation/demo. That will also have some marks.

