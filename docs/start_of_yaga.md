# Start of YAGA

YAGA is started from the command line as:

`python yaga.py [OPTIONS]`

A paradigm file has to be specified with the `-p` or `--paradigm` command line parameter. YAGA will look in the _paradigms_ subfolder for the specified paradigm file. For example, to start the demo paradigm use this command:

`python yaga.py --paradigm demo.py`

Here is a full list of command line options:

| option (short version) | option (long version) | description                                   |
|------------------------|-----------------------|-----------------------------------------------|
| -h                     | --help                | show information                              |
| -p STRING              | --paradigm STRING     | specify the paradigm file to load (necessary) |
| -m                     | --maximize            | maximise application window                   |
|                        | --subject STRING      | specify the subject code                      |
|                        | --session NUMBER      | specify the session number                    |
|                        | --run NUMBER          | specify the run number                        |
|                        | --var1 STRING         | general purpose variable 1                    |
|                        | --var2 STRING         | general purpose variable 2                    |
|                        | --var3 STRING         | general purpose variable 3                    |

The subject code, session and run number are used to select the directory and filename where the recorded data will be saved (see [Integration with LSL](integration_with_lsl.md#integration-with-lab-streaming-layer-lsl)). Moreover, the code in the paradigm file can also make use of this information and, e.g., load subject-specific data. The general purpose variables can be used to specify options for a paradigm (e.g., select a condition). The paradigm option is always obligatory; the other options may be required by the paradigm file.
