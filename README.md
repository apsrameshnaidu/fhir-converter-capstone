## Implementation of **Claude Code AI features as a Capstone project** with fhir converter application.

For fhir-converter app details, please read though **fhir-converter.md file.**

## Pre-requisites:
* Basic of Python
* Claude code setup


## Day 3 Activity
Day 3 activity/task contains two sub-tasks:
1. Api creation 
2. Exposing the Api's using MCP

We can Use this prompt for Api creation:

**Prompt:** Setup a basic FastAPI server and create four api's (two get and two post) and run it using unicorn.

One api's are created, use below command in the powershell/command prompt to add mcp server to the project:

*claude mcp add expose-apis --scope project python "mcp_server.py"*

The above command will add mcp json file to the root level.

Write or generate from Claude Code the **"mcp_server.py"** file which will contail tools to expose the Api's. 

**How to Run**
1. Open Claude Code context window inside your repository.
2. Use command "/mcp"
3. Under Project MCPs, you can find your newly created mcp "expose-apis".
4. Select and connect/enable it.
5. Once it is connected, you can also see the available tools
6. Now your mcp is ready to assist Claude Code to answer your prompt related to the exposed api's/fhir-converter application.

**Ex prompt:** Show me the available templates for ccda

**Try it:** Above prompt with and without connecting to your mcp. You can see the difference, Claude Code will only use your mcp "expose-apis" when you are connected with it.


