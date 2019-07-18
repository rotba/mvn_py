# java_tracer

_java_tracer_ project is a _java agent_ that instruments a java program, to log the traces of all invoked methods with various data. The goal of this development is to instrument a java program such that rich traces of the test-suite would be available, for automated fault localization techniques. However, it may be useful for many other use cases.

## Features

  - Each test would be given it's own `.txt` file, containing all of its traces
  - A test's trace is a method that was invoked during the execution of that test, together with various relevant data
  - Data that is currently being traced:
    -   Method's name
    -   If method is non-static, `hashcode` of invoking object
    -   If method has parameters, the arguments (value for primitive parameters, `hashcode` for non-primitive parameters)
    -   If finishes succesfully, the return value (value for primitive return type, `hashcode` for non-primitive return type). In case return type is `void`, trace will contain "VOID"
    -   If does not finish succesfully, instead of the return value (or "VOID"), the trace will contain "EXCEPTION"

## Prerequisites

* Java
* Maven

## Setup

Using Apache POI test-suite as a target example:

Add setup instructions

## Miscellaneous

### Todos

-   Refactoring for MyInstrumentor.java

### License

MIT
Use freely at your own risk and responsability

**Free Software, Hell Yeah!**
