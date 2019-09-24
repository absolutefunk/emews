# eMews
eMews - Scalable Network Experimentation and Automation Framework

Version used in IRI-18 [1] paper contained in v0.32 branch.

Current version is v0.4, which incorporates environments for agent feedback [2]. 

Note:  We are currently porting eMews to Python 3 (currently >= 3.6).  This version should have a smaller memory footprint than v0.4, and incorporate environment extensions to enable agent-based reinforcement learning scenarios.

Quick start:
- Installation is simply a matter of copying everything in /src/emews to a target folder.  Make sure the folder hierarchy remains intact when copying.  Also make sure that the target path to the emews root folder (top of the hierarchy, ie, /src/emews by default) is present in your python path.
- Assuming eMews is being run under CORE, open your CORE config (default path is /etc/core/core.conf), and modify the 'custom_services_dir' key to point to the eMews 'core_services' path:  custom_services_dir = <path_to_emews_root>/core/core_services

When building a network using core_gui, eMews services should be present.  eMews should also run when a CORE network is launched through core_gui.

Helpful hints:
- CORE networks are built under /tmp/pycore.XXXXX.  Under this folder are folders for each node, named <node_name>.conf
- Under the eMews hub node folder (n1.conf by default), the eMews log file is located, named emews.log.  This is the log file for distributed logging from all eMews nodes.  Scenario monitoring should be performed by accessing this file during an active scenario.
- All eMews nodes contain a file called 'emews_console.log'.  This file logs console output (including exceptions) from each eMews daemon and service launcher.
- For basic customization, please consult the system.yml configuration file, located under <emews_root>/system.yml
- Sample CORE networks are located under /core_networks.

A much more complete user guide will be included here soon.

References:

[1] B. Ricks, P. Tague and B. Thuraisingham, "Large-Scale Realistic Network Data Generation on a Budget," 2018 IEEE International Conference on Information Reuse and Integration (IRI), Salt Lake City, UT, 2018, pp. 23-30. doi: 10.1109/IRI.2018.00012
- URL: http://mews.sv.cmu.edu/papers/iri-18.pdf

[2] B. Ricks, B. Thuraisingham and P. Tague, "Mimicking Human Behavior in Shared-Resource Computer Networks", 2019 IEEE Intl Conference on Information Reuse and Integration for Data Science (IRI), Los Angeles, CA, Jul 2019.
- URL: http://mews.sv.cmu.edu/papers/iri-19.pdf
