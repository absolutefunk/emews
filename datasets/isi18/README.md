DaaSS datasets used for the experiments in Ricks et al. "Lifting the Smokescreen: Detecting Underlying Anomalies During a DDoS Attack", ISI-18.

Datasets collected and aggregated using the approach given in Ricks et al. "Large-Scale Realistic Network Data Generation on a Budget", IRI-18.

The datasets comprise a single training set, three DDoS test sets, and two DaaSS test sets.
The training set and DDoS test sets are binary class (benign/DDoS).  The DaaSS test sets are three class (benign/DDoS/anomaly).
The first feature corresponds to the class label.  Note that in the paper, the approach is unsupervised, and thus the labels were only used when calculating result metrics.

The other features follow from the Argus standard (in order, starting from after the label): flow duration, protocol, destination IP, destination port, total packets over the flow, total bytes over the flow.  Each example comprises one aggregated flow.

The raw PCAP data which our datasets are derived from is also available upon request.

Any questions, contact: absolutefunk@utdallas.edu
